import ctypes
import logging
import threading
import time

import win32con

from src.core.color import ColorRule, Color, RuleMode
from src.core.combat.combat_system import CombatSystem
from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, Scaler
from src.core.i18n import I18nText, Language
from src.core.pages import UIOp
from src.core.workflow import NodeContext, AbstractWorkflow
from src.util import img_util, file_util
from src.util.img_sift_util import SIFTFeatureMatcher

logger = logging.getLogger(__name__)


class KeyListener:
    def __init__(self, *, event, interval=0.001):
        """
        interval: 轮询间隔(秒)，建议 0.001~0.005
        """
        self.interval = interval
        self.event = event
        self._running = False
        self._thread = None

        self._callbacks = {}
        self._last_state = {}

    def register(self, vk, callback):
        """
        callback(vk, is_down)
        """
        self._callbacks[vk] = callback
        self._last_state[vk] = False

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def join(self, timeout=None):
        if self._thread:
            self._thread.join(timeout)

    def _loop(self):
        while self._running and self.event.is_set():
            for vk, callback in self._callbacks.items():
                down = bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)

                last = self._last_state[vk]

                if down != last:
                    self._last_state[vk] = down
                    callback(vk, down)

            time.sleep(self.interval)


class ExploreWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        super().__init__(ctx)

        self.combat_system = None
        self.click_cooldown = 0.5  # 防止重复点击间隔时间，秒
        self.last_time = time.monotonic() - self.click_cooldown
        self.ui = UIOp(ctx)
        self.ctx = ctx
        self.lock = threading.Lock()
        self.matcher = SIFTFeatureMatcher()
        self.members_roi = [
            AnchorBBox(
                AnchorPoint(1140, 116, Align.Top | Align.Right),
                AnchorPoint(1280, 210, Align.Top | Align.Right),
            ),
            AnchorBBox(
                AnchorPoint(1140, 210, Align.Top | Align.Right),
                AnchorPoint(1280, 300, Align.Top | Align.Right),
            ),
            AnchorBBox(
                AnchorPoint(1130, 300, Align.Top | Align.Right),
                AnchorPoint(1280, 400, Align.Top | Align.Right),
            ),
        ]
        self.avatar_map = {
            "T_IconRoleHead150_1.png": I18nText.Yangyang,
            "T_IconRoleHead150_2.png": I18nText.Chixia,
            "T_IconRoleHead150_3.png": I18nText.Verina,
            "T_IconRoleHead150_4.png": I18nText.Rover,
            "T_IconRoleHead150_4_a_UI.png": I18nText.Rover,
            "T_IconRoleHead150_5.png": I18nText.Rover,
            "T_IconRoleHead150_5_a_UI.png": I18nText.Rover,
            "T_IconRoleHead150_6.png": I18nText.Baizhi,
            "T_IconRoleHead150_7.png": I18nText.Sanhua,
            "T_IconRoleHead150_7_a.png": I18nText.Sanhua,
            "T_IconRoleHead150_8.png": I18nText.Encore,
            "T_IconRoleHead150_9.png": I18nText.Taoqi,
            "T_IconRoleHead150_10.png": I18nText.Danjin,
            "T_IconRoleHead150_11.png": I18nText.Jiyan,
            "T_IconRoleHead150_12.png": I18nText.Aalto,
            "T_IconRoleHead150_13.png": I18nText.Mortefi,
            "T_IconRoleHead150_14.png": I18nText.Lingyang,
            "T_IconRoleHead150_15.png": I18nText.Yuanwu,
            "T_IconRoleHead150_17.png": I18nText.Yinlin,
            "T_IconRoleHead150_18.png": I18nText.Calcharo,
            "T_IconRoleHead150_23_UI.png": I18nText.Jianxin,
            "T_IconRoleHead150_24_a_UI.png": I18nText.Jinhsi,
            "T_IconRoleHead150_24_UI.png": I18nText.Jinhsi,
            "T_IconRoleHead150_25_UI.png": I18nText.XiangliYao,
            "T_IconRoleHead150_26_a_UI.png": I18nText.Changli,
            "T_IconRoleHead150_26_UI.png": I18nText.Changli,
            "T_IconRoleHead150_27_UI.png": I18nText.Zhezhi,
            "T_IconRoleHead150_28_UI.png": I18nText.Shorekeeper,
            "T_IconRoleHead150_29_UI.png": I18nText.Camellya,
            "T_IconRoleHead150_30_UI.png": I18nText.Lumi,
            "T_IconRoleHead150_31_UI.png": I18nText.Youhu,
            "T_IconRoleHead150_32_a_UI.png": I18nText.Carlotta,
            "T_IconRoleHead150_32_UI.png": I18nText.Carlotta,
            "T_IconRoleHead150_33_UI.png": I18nText.Roccia,
            "T_IconRoleHead150_34_UI.png": I18nText.Cantarella,
            "T_IconRoleHead150_37_UI.png": I18nText.Ciaccona,
            "T_IconRoleHead150_38_a_UI.png": I18nText.Zanni,
            "T_IconRoleHead150_38_UI.png": I18nText.Zanni,
            "T_IconRoleHead150_40_UI.png": I18nText.Cartethyia,
            "T_IconRoleHead150_41_UI.png": I18nText.Phrolova,
            "T_IconRoleHead150_44_UI.png": I18nText.Brant,
            "T_IconRoleHead150_45_UI.png": I18nText.Phoebe,
            "T_IconRoleHead150_46_UI.png": I18nText.Lupa,
            "T_IconRoleHead150_48_UI.png": I18nText.Iuno,
            "T_IconRoleHead150_51_UI.png": I18nText.Augusta,
            "T_IconRoleHead150_53_UI.png": I18nText.Aemeath,
            "T_IconRoleHead150_54_UI.png": I18nText.LuukHerssen,
            "T_IconRoleHead150_55_UI.png": I18nText.Galbrena,
            "T_IconRoleHead150_56_UI.png": I18nText.Qiuyuan,
            "T_IconRoleHead150_57_Skin1_UI.png": I18nText.Chisa,
            "T_IconRoleHead150_57_UI.png": I18nText.Chisa,
            "T_IconRoleHead150_58_UI.png": I18nText.Buling,
            "T_IconRoleHead150_60_Skin1_UI.png": I18nText.Lynae,
            "T_IconRoleHead150_60_UI.png": I18nText.Lynae,
            "T_IconRoleHead150_61_Skin1_UI.png": I18nText.Mornye,
            "T_IconRoleHead150_61_UI.png": I18nText.Mornye,
            "T_IconRoleHead150_64_UI.png": I18nText.Denia,
            "T_IconRoleHead150_65_UI.png": I18nText.Sigrika,
            "T_IconRoleHead150_66_UI.png": I18nText.Lucilla,
            "T_IconRoleHead150_67_UI.png": I18nText.Hiyuki,
            "T_IconRoleHead150_68_UI.png": I18nText.Lucy,
            "T_IconRoleHead150_69_UI.png": I18nText.Rebecca,
            "T_IconRoleHead150_70_UI.png": I18nText.YangyangXuanling,
            "T_IconRoleHead150_71_UI.png": I18nText.Suisui,
        }
        self.role_features = self.__init_role_features()
        self.count = 1

    def execute(self, **kwargs):
        try:
            logger.debug(f"task: {self.__class__.__name__}")

            listener = KeyListener(event=self.ctx.runtime.stop_event, interval=0.005)

            listener.register(win32con.VK_XBUTTON1, self._on_click)
            listener.register(win32con.VK_ESCAPE, self._on_press)

            listener.start()
            listener.join()

        except Exception as e:
            raise e

    def __init_role_features(self):
        role_features = []
        path = file_util.get_assets_avatar()
        for p in path.glob("*.png"):
            # logger.debug(p.absolute())
            feature_image = img_util.read_img(p.absolute())
            feature_data = self.matcher.build_feature_data_masked(feature_id=p.name, image=feature_image)
            role_features.append(feature_data)
        return role_features

    def member_count(self):
        cc = Color.bgr(241, 241, 241)
        points = [
            [
                AnchorPoint(1158, 146, Align.Top | Align.Right),
                AnchorPoint(1160, 151, Align.Top | Align.Right),
                AnchorPoint(1166, 143, Align.Top | Align.Right),
                AnchorPoint(1166, 151, Align.Top | Align.Right),
            ],
            [
                AnchorPoint(1159, 234, Align.Top | Align.Right),
                AnchorPoint(1158, 240, Align.Top | Align.Right),
                AnchorPoint(1167, 231, Align.Top | Align.Right),
                AnchorPoint(1168, 240, Align.Top | Align.Right),
            ],
            [
                AnchorPoint(1159, 322, Align.Top | Align.Right),
                AnchorPoint(1158, 328, Align.Top | Align.Right),
                AnchorPoint(1167, 319, Align.Top | Align.Right),
                AnchorPoint(1168, 328, Align.Top | Align.Right),
            ],
        ]
        img = self.ui.grap()
        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        result = [ColorRule().points(p).colors(cc, 20, RuleMode.ALL).match(img, scaler) for p in points]
        white_count = sum(x for x in result)
        return min(white_count + 1, 3)

    def _on_click(self, button, pressed):
        if not pressed:  # 忽略弹起信号
            return True
        try:
            # logger.info(f"[{self.count:03d}] XButton1 在位置 ({x}, {y}) 被按下")
            with self.lock:
                # 没启动就启动，已启动就停止
                if self.combat_system is None:
                    logger.info(f"[{self.count:03d}] XButton1 start")
                    self.last_time = time.monotonic()
                    img = self.ui.grap()
                    if not self.ui.is_on_homepage(img):
                        logger.info(f"[{self.count:03d}] Not in the overworld")
                        return True
                    team_members = [None, None, None]
                    scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
                    for index, member_roi in enumerate(self.members_roi):
                        cur_roi = scaler.as_bbox(member_roi)
                        scene_image = img[cur_roi.as_slice()]
                        results = self.matcher.identify_roles(scene_image, self.role_features, min_good_matches=3)
                        logger.debug(f"identify_roles: {results}")
                        if not results:
                            continue
                        avatar_key = self.avatar_map.get(results[0])
                        if not avatar_key:
                            continue
                        team_members[index] = self.ctx.tr(avatar_key, lang=Language.ZH).raw
                    logger.debug(f"team_members: {team_members}")

                    member_count = self.member_count()
                    logger.debug(f"member_count: {member_count}")

                    for i in range(3):
                        if i + 1 <= member_count:
                            if team_members[i] is None:
                                team_members[i] = "unknown"
                        else:
                            team_members[i] = None

                    combat_system = CombatSystem(self.ctx.control_service, self.ctx.img_service)
                    combat_system.set_resonators(team_members)
                    combat_system.is_async = True
                    combat_system.check_boss_hp = False
                    combat_system.auto_pickup = True
                    combat_system.start(10 * 60)
                    self.combat_system = combat_system
                else:
                    if time.monotonic() - self.last_time < self.click_cooldown:
                        logger.info(f"[{self.count:03d}] 短期重复点击，忽略")
                        return True
                    logger.info(f"[{self.count:03d}] XButton1 stop")
                    self.count += 1
                    combat_system = self.combat_system
                    self.combat_system = None
                    if combat_system is not None:
                        combat_system.stop()
        except KeyboardInterrupt as e:
            return False
        except StopError as e:
            pass
        except Exception as e:
            logger.exception(e)
        return True

    def _on_press(self, key, pressed):
        if not pressed:  # 忽略弹起信号
            return True
        try:
            with self.lock:
                combat_system = self.combat_system
                self.combat_system = None
                if combat_system is not None:
                    logger.info(f"[{self.count:03d}] ESC stop")
                    self.count += 1
                    combat_system.stop()
                else:
                    logger.info(f"[{self.count:03d}] ESC skip")
        except KeyboardInterrupt as e:
            return False
        except StopError as e:
            pass
        except Exception as e:
            logger.exception(e)
        return True
