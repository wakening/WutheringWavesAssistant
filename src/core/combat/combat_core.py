import logging
import random
import threading
import time
from enum import Enum
from functools import wraps
from typing import Sequence, Optional

import numpy as np

from src.core.exceptions import StopError
from src.core.interface import ControlService, ImgService
from src.core.regions import AlignEnum, DynamicPointTransformer

logger = logging.getLogger(__name__)


class ResonatorNameEnum(Enum):
    # 特殊
    rover = "漂泊者"
    generic = "generic"
    none = "None"

    # 常驻
    encore = "安可"
    verina = "维里奈"
    calcharo = "卡卡罗"
    lingyang = "凌阳"
    jianxin = "鉴心"

    yangyang = "秧秧"
    baizhi = "白芷"
    chixia = "炽霞"
    sanhua = "散华"
    aalto = "秋水"
    danjin = "丹瑾"
    mortefi = "莫特斐"
    yuanwu = "渊武"
    taoqi = "桃祈"

    # v1.0
    jiyan = "忌炎"
    yinlin = "吟霖"

    # v1.1
    jinhsi = "今汐"
    changli = "长离"

    # v1.2
    zhezhi = "折枝"
    xiangliyao = "相里要"

    # v1.3
    shorekeeper = "守岸人"
    youhu = "釉瑚"

    # v1.4
    camellya = "椿"
    lumi = "灯灯"

    # v2.0
    carlotta = "珂莱塔"
    roccia = "洛可可"

    # v2.1
    phoebe = "菲比"
    brant = "布兰特"

    # v2.2
    cantarella = "坎特蕾拉"

    # v2.3
    zanni = "赞妮"
    ciaccona = "夏空"

    # v2.4
    cartethyia = "卡提希娅"
    lupa = "露帕"

    # v2.5
    phrolova = "弗洛洛"

    # v2.6
    augusta = "奥古斯塔"
    iuno = "尤诺"

    # v2.7
    galbrena = "嘉贝莉娜"
    qiuyuan = "仇远"

    # v2.8
    chisa = "千咲"
    buling = "卜灵"

    # v3.0
    lynae = "琳奈"
    mornye = "莫宁"

    # v3.1
    aemeath = "爱弥斯"
    luukherssen = "陆赫斯"

    # v3.2
    sigrika = "西格莉卡"

    # v3.3
    hiyuki = "绯雪"
    denia = "达妮娅"

    # v3.4
    lucy = "露西"
    rebecca = "丽贝卡"
    lucilla = "洛瑟菈"

    # v3.5
    yangyangxuanling = "秧秧玄翎"
    suisui = "穗穗"

    # v3.6
    qingxiao = "清宵"
    jingran = "景燃"

    # v3.x
    suoming = "锁暝"
    hsin = "心"

    # 缓存
    __value_map = None

    @classmethod
    def get_enum_map(cls):
        """ 获取枚举集合，不包含特殊的几个 """
        if cls.__value_map is None:
            # cls.__value_map = {member.value: member for member in cls}
            cls.__value_map = {}
            for member in cls:
                if member in [cls.rover, cls.generic, cls.none]:
                    continue
                cls.__value_map[member.value] = member
        return cls.__value_map

    @classmethod
    def get_names_zh(cls):
        return list(cls.get_enum_map().keys())

    @classmethod
    def get_names_en(cls):
        return [i.name for i in cls.get_enum_map().values()]

    @classmethod
    def get_enum_by_value(cls, value):
        return cls.get_enum_map().get(value)

    @classmethod
    def get_enum_by_ocr_text(cls, ocr_text) -> Optional["ResonatorNameEnum"]:
        """
        ocr文本匹配角色名，部分角色有生僻字或特殊字符，需要特殊处理
        :param ocr_text:
        :return: 枚举或None
        """
        if not ocr_text:
            return None
        ocr_text = ocr_text.strip()
        enum_map = cls.get_enum_map()
        for name_zh, enum_obj in enum_map.items():
            if name_zh == ocr_text:
                return enum_obj
            if 1 <= len(ocr_text) <= 2 and ocr_text.startswith(cls.chisa.value[0]):
                return cls.chisa
            if len(ocr_text) >= 3 and ocr_text.startswith(cls.luukherssen.value[0]) and ocr_text.endswith(cls.luukherssen.value[-2:]):
                return cls.luukherssen
            if len(ocr_text) >= 2 and ocr_text.startswith(cls.lucilla.value[:2]):
                return cls.lucilla
            if len(ocr_text) >= 4 and ocr_text.startswith(cls.yangyangxuanling.value[:2]) and ocr_text.endswith(cls.yangyangxuanling.value[-2:]):
                return cls.yangyangxuanling
        return None


class BaseChecker:

    def __init__(self):
        pass

    def check(self, img: np.ndarray) -> bool:
        pass


class LogicEnum(Enum):
    """
    多点匹配，逻辑或、与
    """
    OR = "or"  # 默认使用或，一点匹配即可，适用于一个技能只有亮或灰两种状态
    AND = "and"  # 当一个技能有多种变化，比如今汐E，则需要多点联合点位，使用与


def combat_cache(func):
    """
    仅用于缓存连招
    :param func:
    :return:
    """

    storage = {}

    @wraps(func)
    def wrapper(*args, **kwargs):

        key = (args, tuple(kwargs.items()))

        if logger.isEnabledFor(logging.DEBUG):
            cls_name = None
            if args:
                obj = args[0]
                if hasattr(obj, '__class__'):
                    cls_name = obj.__class__.__name__  # 实例方法
                elif isinstance(obj, type):
                    cls_name = obj.__name__  # 类方法

            if cls_name:
                logger.debug(f"{cls_name}.{func.__name__}", stacklevel=2)
            else:
                logger.debug(func.__name__, stacklevel=2)

        if key not in storage:
            storage[key] = func(*args, **kwargs)

        return storage[key]

    return wrapper


class ColorChecker(BaseChecker):
    """ 像素颜色校验器 """

    def __init__(self, points: Sequence[tuple[int, int]], colors: Sequence[tuple[int, int, int]], tolerance: int = 30,
                 logic=LogicEnum.OR, align: AlignEnum = None):
        super().__init__()
        self.points = points  # 坐标 x,y
        self.colors = np.array(colors)  # BGR
        self.tolerance = tolerance  # 容差
        self.logic = logic
        self.align = align  # 对齐方式

    def check(self, img: np.ndarray) -> bool:
        if self.points is None or len(self.points) == 0:
            raise ValueError("Points is empty")

        dpt = DynamicPointTransformer(img)

        if self.logic == LogicEnum.OR:
            # 多点匹配，一个点的颜色匹配上就为真
            # scale = self.get_scale(img)
            for pre_point in self.points:
                point = dpt.transform(pre_point, self.align)
                # target = img[int(scale * point[1]), int(scale * point[0])]
                target = img[point[1], point[0]]
                # logger.debug(f"target: {target}")
                # 颜色按或匹配
                for sample in self.colors:
                    if np.all(np.abs(sample - target) <= self.tolerance):  # 容差匹配
                        # logger.debug(f"sample: {sample}")
                        return True
            return False
        elif self.logic == LogicEnum.AND:
            # 多点匹配，所有点的颜色都匹配才为真
            # scale = self.get_scale(img)
            for pre_point in self.points:
                point = dpt.transform(pre_point, self.align)
                # target = img[int(scale * point[1]), int(scale * point[0])]
                target = img[point[1], point[0]]
                # logger.debug(f"target: {target}")
                # 颜色按或匹配
                is_color_match = False
                for sample in self.colors:
                    if np.all(np.abs(sample - target) <= self.tolerance):  # 容差匹配
                        # logger.debug(f"sample: {sample}")
                        is_color_match = True
                        break
                if not is_color_match:
                    return False
            return True
        raise NotImplementedError("Unknown logic")

    @staticmethod
    def concerto_spectro():
        """ 衍射 协奏能量校验器，左下血条旁黄圈 """
        concerto_energy_point = [(513, 669), (514, 669), (514, 670), (514, 671)]
        concerto_energy_color = [(105, 204, 217)]  # BGR
        return ColorChecker(concerto_energy_point, concerto_energy_color)

    @staticmethod
    def concerto_fusion():
        """ 热熔 协奏能量校验器，左下血条旁红圈 """
        concerto_energy_point = [(513, 669), (514, 669), (514, 670), (514, 671)]
        concerto_energy_color = [(81, 112, 210)]  # BGR
        return ColorChecker(concerto_energy_point, concerto_energy_color)

    @staticmethod
    def concerto_havoc():
        """ 湮灭 协奏能量校验器，左下血条旁紫圈 """
        concerto_energy_point = [(513, 669), (514, 669), (514, 670), (514, 671)]
        concerto_energy_color = [(153, 77, 201)]  # BGR
        return ColorChecker(concerto_energy_point, concerto_energy_color)

    @staticmethod
    def concerto_glacio():
        """ 冷凝 协奏能量校验器，左下血条旁蓝圈 """
        concerto_energy_point = [(513, 669), (514, 669), (514, 670), (514, 671)]
        concerto_energy_color = [(222, 159, 68)]  # BGR
        return ColorChecker(concerto_energy_point, concerto_energy_color)

    @staticmethod
    def concerto_aero():
        """ 气动 协奏能量校验器，左下血条旁绿圈 """
        concerto_energy_point = [(513, 669), (514, 669), (514, 670), (514, 671)]
        concerto_energy_color = [(168, 226, 87), (171, 216, 121)]  # BGR
        return ColorChecker(concerto_energy_point, concerto_energy_color)


class BaseCombo:
    """ 连招 """

    def __init__(self, control_service: ControlService):
        super().__init__()
        self.control_service = control_service
        self.event: threading.Event | None = None
        self.auto_pickup: bool = False

    def combo_action(self, sequence: Sequence, end_wait: bool, ignore_event: bool = False):
        """
        执行按键序列
        :param sequence:
        :param end_wait: 队列最后一个按键是否睡眠等待后摇时间，用于合轴，False不等就是一放就切，True等待就是放完技能结束才切
        :param ignore_event:
        :return:
        """
        max_size = len(sequence)
        key_down_caches = set()
        tap_f_time = time.monotonic()
        for i, keys in enumerate(sequence):
            if not ignore_event and self.event is not None and not self.event.is_set():
                # 退出前释放按压的按键
                for key_down_cache in key_down_caches:
                    if key_down_cache in ["a", "z"]:
                        self.control_service.mouse_left_up(0.001)
                    elif key_down_cache == "w":
                        pass
                    elif key_down_cache == "j":
                        self.control_service.key_up("SPACE", 0.001)
                    elif key_down_cache == "d":
                        self.control_service.mouse_right_up(0.001)
                    else:
                        self.control_service.key_up(key_down_cache, 0.001)
                raise StopError()
            if self.auto_pickup:
                tap_f_cur_time = time.monotonic()
                # 限制自动F频率
                if tap_f_cur_time - tap_f_time > 0.25 or (i > 0 and i == max_size - 1):
                    tap_f_time = tap_f_cur_time
                    self.control_service.fight_tap("F", 0.001)
            key_src, press_time, wait_time = keys[:3]
            key = key_src  # a a_down a_up
            key_action = None  # down up
            if "_" in key_src:
                key, key_action = key_src.strip().split("_", 1)
            if not key_action:
                if key == "a":
                    if press_time > 0.2:
                        raise ValueError("普攻按压时间不可大于0.2，默认统一填写0.05")
                    self.control_service.fight_click(seconds=press_time)
                elif key == "z":
                    if press_time < 0.3:
                        raise ValueError("重击按压时间不可小于0.3，默认统一写0.5")
                    self.control_service.fight_click(seconds=press_time)
                elif key == "w":
                    pass
                elif key == "j":
                    self.control_service.fight_tap("SPACE", press_time)
                elif key == "d":
                    # self.control_service.fight_tap("LSHIFT", press_time)
                    self.control_service.fight_right_click(seconds=press_time)
                else:
                    self.control_service.fight_tap(key, press_time)
            else:
                if key_action == "down":
                    if key in ["a", "z"]:
                        self.control_service.mouse_left_down(seconds=press_time)
                    elif key == "w":
                        pass
                    elif key == "j":
                        self.control_service.key_down("SPACE", press_time)
                    elif key == "d":
                        # self.control_service.fight_tap("LSHIFT", press_time)
                        self.control_service.mouse_right_down(seconds=press_time)
                    else:
                        self.control_service.key_down(key, press_time)
                    key_down_caches.add(key)
                elif key_action == "up":
                    if key in ["a", "z"]:
                        self.control_service.mouse_left_up(seconds=press_time)
                    elif key == "w":
                        pass
                    elif key == "j":
                        self.control_service.key_up("SPACE", press_time)
                    elif key == "d":
                        # self.control_service.fight_tap("LSHIFT", press_time)
                        self.control_service.mouse_right_up(seconds=press_time)
                    else:
                        self.control_service.key_up(key, press_time)
                    key_down_caches.discard(key)
                else:
                    logger.warning("Unknown key action '{}'".format(key_action))
            if wait_time <= 0:
                continue
            # 最后一下可合轴，显示传入False表示无需等待后摇结束
            if i == max_size - 1 and end_wait is False:
                break
            if not ignore_event and self.event is not None and not self.event.is_set():
                raise StopError()
            # 后摇等待
            time.sleep(wait_time)


class CharClassEnum(Enum):
    """
    角色分类，用于给编队内角色的出场顺序做排序
    """
    MainDPS = "MainDPS"  # 主c
    SubDPS = "SubDPS"  # 副c，暂时无用，若需要在主c前出场，应标为辅助而非副c，这样才一定能排在前面
    Support = "Support"  # 辅助，排序先于主副c
    Healer = "Healer"  # 奶，排序后于主副c


class Morph(Enum):
    """
    变回原始形态，用于奔跑、行走前判断，有些角色变身状态无法走路，或走的太快，需要变回普通形态
    """
    Prefer = "Prefer"  # 尽量变回去，能动的可以不变如大卡，不能动的必须变回去如红椿
    Forced = "Forced"  # 强制变回去


class BaseResonator(BaseCombo):
    """ 共鸣者基类，定义了一些常用函数，可按需实现 """

    ## boss hp
    # 血条为黄到红的渐变色
    _health_01_point = [(454, 41)]
    _health_01_color = [(68, 179, 255)]  # BGR

    _health_20_point = [(528, 41)]
    _health_20_color = [(62, 164, 255), (206, 237, 255)]  # BGR

    _health_30_point = [(565, 41)]
    _health_30_color = [(55, 148, 255)]  # BGR

    _health_50_point = [(641, 41)]
    _health_50_color = [(38, 109, 255), (56, 124, 255)]  # BGR

    _health_100_point = [(830, 41)]
    _health_100_color = [(8, 37, 255)]  # BGR

    _health_01_color_checker = ColorChecker(_health_01_point, _health_01_color, align=AlignEnum.TOP_CENTER)
    _health_20_color_checker = ColorChecker(_health_20_point, _health_20_color, align=AlignEnum.TOP_CENTER)
    _health_30_color_checker = ColorChecker(_health_30_point, _health_30_color, align=AlignEnum.TOP_CENTER)
    _health_50_color_checker = ColorChecker(_health_50_point, _health_50_color, align=AlignEnum.TOP_CENTER)
    _health_100_color_checker = ColorChecker(_health_100_point, _health_100_color, align=AlignEnum.TOP_CENTER)


    _immobilized_20_point = [(528, 52)]
    _immobilized_20_color = [(255, 255, 255)]  # BGR

    _immobilized_30_point = [(565, 52)]
    _immobilized_30_color = [(255, 255, 255)]  # BGR

    _immobilized_50_point = [(641, 52)]
    _immobilized_50_color = [(255, 255, 255)]  # BGR

    _immobilized_20_color_checker = ColorChecker(_immobilized_20_point, _immobilized_20_color, align=AlignEnum.TOP_CENTER)
    _immobilized_30_color_checker = ColorChecker(_immobilized_30_point, _immobilized_30_color, align=AlignEnum.TOP_CENTER)
    _immobilized_50_color_checker = ColorChecker(_immobilized_50_point, _immobilized_50_color, align=AlignEnum.TOP_CENTER)

    ## is_boss_health_bar_exist
    _tolerance = 20
    # 血条为黄到红的渐变色
    _a_health_01_point = [(453, 40)]
    _a_health_01_color = [(69, 178, 253), (71, 134, 180)]  # BGR
    _a_health_01_checker = ColorChecker(
        _a_health_01_point, _a_health_01_color, tolerance=_tolerance, align=AlignEnum.TOP_CENTER)

    _a_health_02_point = [(454, 40), (454, 41), (450, 39)]
    _a_health_02_color = [(68, 179, 255)]  # BGR
    _a_health_02_checker = ColorChecker(
        _a_health_02_point, _a_health_02_color, tolerance=_tolerance, align=AlignEnum.TOP_CENTER)

    _a_health_20_point = [(528, 40)]
    # health_20_color = [(62, 164, 255), (47, 18, 28)]  # BGR
    _a_health_20_color = [(62, 164, 255)]  # BGR
    _a_health_20_checker = ColorChecker(
        _a_health_20_point, _a_health_20_color, tolerance=_tolerance, align=AlignEnum.TOP_CENTER)

    _a_health_30_point = [(566, 40)]
    # health_30_color = [(55, 148, 255), (47, 17, 27)]  # BGR
    _a_health_30_color = [(55, 148, 255)]  # BGR
    _a_health_30_checker = ColorChecker(
        _a_health_30_point, _a_health_30_color, tolerance=_tolerance, align=AlignEnum.TOP_CENTER)

    _a_health_50_point = [(642, 40)]
    # health_50_color = [(38, 109, 255), (51, 19, 29)]  # BGR
    _a_health_50_color = [(38, 109, 255)]  # BGR
    _a_health_50_checker = ColorChecker(
        _a_health_50_point, _a_health_50_color, tolerance=_tolerance, align=AlignEnum.TOP_CENTER)

    # health_100_point = [(830, 41)]
    # health_100_color = [(8, 37, 255), (65, 30, 41), (93, 80, 83)]  # BGR

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service)
        self.img_service = img_service
        self.check_boss_hp = True

    def resonator_name(self) -> ResonatorNameEnum:
        """ 角色名 """
        raise NotImplementedError()

    def char_class(self) -> list[CharClassEnum]:
        """ 角色分类 """
        raise NotImplementedError()

    def energy_count(self, img: np.ndarray) -> int:
        raise NotImplementedError()

    def is_concerto_energy_ready(self, img: np.ndarray) -> bool:
        raise NotImplementedError()

    def is_resonance_skill_ready(self, img: np.ndarray) -> bool:
        raise NotImplementedError()

    def is_echo_skill_ready(self, img: np.ndarray) -> bool:
        raise NotImplementedError()

    def is_resonance_liberation_ready(self, img: np.ndarray) -> bool:
        raise NotImplementedError()

    def exit_special_state(self, morph: Morph) -> bool:
        """
        脱离特殊状态，部分角色可变身飞天等，影响移动，需实现此函数
        :param morph:
        :return:
        """
        return True

    def combo(self):
        raise NotImplementedError()

    @classmethod
    def random_float(cls) -> float:
        return random.random()

    @classmethod
    def is_avatar_grey(cls, img: np.ndarray, member: int) -> bool:
        dpt = DynamicPointTransformer(img)
        # 多点采样，有些角色带灰色，会误判灰度
        # 0: 头像中心
        # 1: 头像中心偏左下，脸部
        member1_points = [(1195, 168), (1193, 177)]
        alive_count = 0
        for member1_point in member1_points:
            if not cls._is_avatar_grey(img, member, dpt, member1_point):
                alive_count += 1
        # 所有点都是灰才认定为阵亡
        is_avatar_grey = alive_count == 0
        # logger.debug("is_avatar_grey: %s", is_avatar_grey)
        return is_avatar_grey

    @classmethod
    def _is_avatar_grey(cls, img: np.ndarray, member: int, dpt, member1_point: tuple[int, int]) -> bool:
        # dpt = DynamicPointTransformer(img)
        # team_member_health_points = [(1170, 192), (1170, 280), (1170, 368)]  # 右侧123号位角色血条起始点，用于定位，计算相对位置
        team_member_points = [
            member1_point,
            (member1_point[0], member1_point[1] + 280 - 192),
            (member1_point[0], member1_point[1] + 368 - 192)
        ]
        point = team_member_points[member - 1]
        point = dpt.transform(point, AlignEnum.TOP_RIGHT)
        b, g, r = img[point[1], point[0]]
        tolerance = 1  # 容差
        # uint8转为int
        is_avatar_grey = abs(int(b) - int(g)) <= tolerance and abs(int(g) - int(r)) <= tolerance
        # logger.debug("is_avatar_grey: %s", is_avatar_grey)
        return is_avatar_grey

    # @classmethod
    def boss_hp(self, img: np.ndarray) -> float:
        """ boss剩余血条比例，归一 """
        if not self.check_boss_hp:
            return 1.00
        health = 0.0
        if self._health_01_color_checker.check(img):
            health = 0.01  # 血量1%
        if self._health_20_color_checker.check(img):
            health = 0.20
            # logger.debug("boss_hp: %s", health)
        if self._health_30_color_checker.check(img):
            health = 0.30
            # logger.debug("boss_hp: %s", health)
        if self._health_50_color_checker.check(img):
            health = 0.50
            # logger.debug("boss_hp: %s", health)
        if self._health_100_color_checker.check(img):
            health = 1.00

        logger.debug(f"boss_hp: {health}", stacklevel=2)
        return health

    @classmethod
    def boss_immobilized_bar_exist(cls, img: np.ndarray) -> bool:
        """ boss剩余白条比例，归一 """
        immobilized = (cls._immobilized_20_color_checker.check(img)
                       and cls._immobilized_30_color_checker.check(img)
                       and cls._immobilized_50_color_checker.check(img))

        logger.debug("boss_immobilized: %s", immobilized)
        return immobilized

    @classmethod
    def is_boss_health_bar_exist(cls, img: np.ndarray) -> bool:
        """ boss剩余血条比例，归一 """
        if (cls._a_health_02_checker.check(img)
                or cls._a_health_01_checker.check(img)
                or cls._a_health_20_checker.check(img)
                or cls._a_health_30_checker.check(img)
                or cls._a_health_50_checker.check(img)):
            is_exist = True
        else:
            is_exist = False
        logger.debug("is_boss_health_bar_exist: %s", is_exist)
        return is_exist

    @classmethod
    def boss_is_immobilized(cls, img: np.ndarray) -> bool:
        """ boss是否已瘫痪 """
        # # 共振度，比血条略短一点点
        vibration_strength_00_point = [(453, 54)]
        # vibration_strength_20_point = [(528, 54)]
        # vibration_strength_50_point = [(641, 54)]
        # vibration_strength_100_point = [(826, 54)]
        # vibration_strength_color = [(255, 255, 255)]  # BGR

        # 瘫痪后，共振条由白色变为黄色
        immobilize_color = [(28, 235, 255)]  # BGR
        checker = ColorChecker(vibration_strength_00_point, immobilize_color, align=AlignEnum.TOP_CENTER)
        is_immobilized = checker.check(img)
        logger.debug("is_immobilized: %s", is_immobilized)
        return is_immobilized


class TeamMemberSelector:

    def __init__(self, control_service: ControlService, img_service: ImgService):
        self.control_service = control_service
        self.img_service = img_service

        self.point_1 = [(1158, 146), (1166, 143)]
        self.point_2 = [(1159, 234), (1167, 231)]
        self.point_3 = [(1159, 322), (1167, 319)]
        self.colors = [(247, 250, 254)]
        self.tolerance = 20

        # team_member 1
        self._team_member_1_checker = ColorChecker(
            self.point_1, self.colors, self.tolerance, logic=LogicEnum.AND, align=AlignEnum.TOP_RIGHT)

        # team_member 2
        self._team_member_2_checker = ColorChecker(
            self.point_2, self.colors, self.tolerance, logic=LogicEnum.AND, align=AlignEnum.TOP_RIGHT)

        # team_member 3
        self._team_member_3_checker = ColorChecker(
            self.point_3, self.colors, self.tolerance, logic=LogicEnum.AND, align=AlignEnum.TOP_RIGHT)

        self._team_member_map = {
            1: self._team_member_1_checker,
            2: self._team_member_2_checker,
            3: self._team_member_3_checker,
        }

    def _get_team_member_checker(self, index: int, resonators: list[BaseResonator]) -> BaseChecker:
        # 兼容编队少人，只检查有人的数字标
        # 若有三人则需检查当前角色外的另外两人的数字标
        # 若有空两人则跳过没人的数字标
        length = len(resonators)
        # 找出哪几个位置有人
        need_check_index_list = []
        for i in range(length):
            if i == index:  # 不检查自己的，比如2号角色需检查13的数字标
                continue
            if resonators[i] is not None:  # 若没带3号角色，跳过
                need_check_index_list.append(i)
        team_member_points = []
        for check_index in need_check_index_list:
            member = check_index + 1
            if member == 1:
                team_member_points.extend(self.point_1)
            elif member == 2:
                team_member_points.extend(self.point_2)
            elif member == 3:
                team_member_points.extend(self.point_3)
        return ColorChecker(
            team_member_points, self.colors, self.tolerance, logic=LogicEnum.AND, align=AlignEnum.TOP_RIGHT)

    # def get_avatars(self) -> dict[str, np.ndarray]:
    #     """ 获取所有角色的头像 """
    #     from src.util import file_util, img_util
    #     # 所有头像都放在一张透明图里1280x720，按网格摆放
    #     img_path = file_util.get_assets_template("Avatars.png")
    #     img = img_util.read_img(img_path, alpha=False)
    #     # logger.debug("img shape: %s", img.shape)
    #     # 头像摆放顺序
    #     avatar_names = [ # 重复的为皮肤或亮暗背景下的头像
    #         "jinhsi", "jinhsi", "jinhsi", "jinhsi", "jinhsi", "changli", "changli", "changli", "shorekeeper",
    #         "verina", "verina", "verina", "encore", "encore", "encore",
    #         "camellya", "rover", "sanhua", "sanhua", "sanhua", "cantarella",
    #         "zani", "baizhi", "xiangliyao", "calcharo", "jianxin",
    #         "cartethyia", #"ciaccona",
    #     ]
    #     # 头像网格，40像素放一个，1280宽度，一行放32个
    #     avatar_grid = (40, 40)
    #     # 头像在网格内的位置，左上角0,0 到 右下角这个位置的正方形。有四个像素的空白间隙
    #     avatar_wh = (36, 36)
    #     x = 0
    #     y = 0
    #     avatar_map = {}
    #     for name in avatar_names:
    #         avatar_grid_img = img[y:y + avatar_grid[1], x:x + avatar_grid[0]]
    #         avatar_img = avatar_grid_img[0:avatar_wh[1], 0:avatar_wh[0]]
    #         avatar_map[name] = avatar_img
    #         # img_util.save_img_in_temp(avatar_img)
    #         x = x + avatar_grid[0]
    #         if x >= 1280:
    #             x = 0
    #             y = y + avatar_grid[1]
    #     return avatar_map
    #
    # def get_team_members(self, img: np.ndarray | None = None) -> list[str]:
    #     """
    #     识别画面中的角色，从上到下
    #     :param img: 16:9 BGR
    #     :return:
    #     """
    #     if img is None:
    #         img = self.img_service.screenshot()
    #         # from src.util import img_util
    #         # img_util.save_img_in_temp(img)
    #     img = self.img_service.resize(img)
    #     logger.debug("img shape: %s", img.shape)
    #     # start_col = int(img.shape[1] * 0.85)
    #     # img = img[:, start_col:]
    #     # img = img[135:372, 1168:1225]
    #     # 123号位角色头像在图中的区域
    #     member_regions = [(1167, 135, 1230, 198), (1167, 224, 1230, 285), (1167, 314, 1230, 373)]
    #     avatars = self.get_avatars()
    #     members = []
    #     for i, region in enumerate(member_regions):
    #         # 每个位置都匹配一遍头像，找出相似度最高的那个
    #         region_img = img[region[1]:region[3], region[0]:region[2]]
    #         # from src.util import img_util
    #         # img_util.save_img_in_temp(region_img)
    #         match_results = []
    #         for avatar_name, avatar_img in avatars.items():
    #             position = self.img_service.match_template(region_img, avatar_img, threshold=0.3)
    #             logger.debug(f"{i} avatar: {avatar_name}, position: {position}")
    #             if not position:
    #                 continue
    #             match_results.append((avatar_name, position.confidence))
    #         logger.debug(f"{i} match_results: {match_results}")
    #         if len(match_results) == 0:
    #             members.append(None)
    #             continue
    #         if len(match_results) > 1:
    #             match_results.sort(key=lambda x: x[1], reverse=True)  # 从大到小
    #         logger.debug(f"{i} match_results: {match_results}")
    #         members.append(match_results[0])
    #
    #     logger.debug(f"members: {members}")
    #     member_names = []
    #     for i, member in enumerate(members):
    #         if member is None:
    #             logger.warning(f"无法识别{i + 1}号位角色")
    #             member_names.append(None)
    #             continue
    #         member_names.append(member[0])
    #     logger.info(f"member_names: {member_names}")
    #     return member_names

    def toggle(self, index: int, event: threading.Event | None,
               resonators: list[BaseResonator], timeout_seconds: float = 1.0) -> bool | None:
        member = index + 1

        resonator = resonators[index]
        img = self.img_service.screenshot()
        is_avatar_grey = resonator.is_avatar_grey(img, member)
        if is_avatar_grey:
            logger.debug(f"角色{member}已阵亡，跳过")
            return None
        else:
            logger.debug(f"角色{member}存活")

        team_member_checker = self._get_team_member_checker(index, resonators)
        start_time = time.monotonic()

        while time.monotonic() - start_time < timeout_seconds:
            if event is not None and not event.is_set():
                return None
            logger.debug("切换角色: %s", member)
            self.control_service.toggle_team_member(member)
            time.sleep(0.5)
            img = self.img_service.screenshot()
            is_toggled = team_member_checker.check(img)

            # from src.util import img_util
            # img_util.save_img_in_temp(img)

            if is_toggled:
                return True
            time.sleep(0.1)
        return False

    def get_cur_member_number(self, resonators: list[BaseResonator]) -> int | None:
        """
        获取当前角色编队位置，几号位
        :param resonators:
        :return: 返回1或2或3
        """
        img = self.img_service.screenshot()
        is_exists = [
            self._team_member_1_checker.check(img),
            self._team_member_2_checker.check(img),
            self._team_member_3_checker.check(img),
        ]
        for index, resonator in enumerate(resonators):
            if is_exists[index] is False and resonator is not None:
                return index + 1
        return None

# circular import
# class CombatSystem:
