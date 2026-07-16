import logging
import threading
import time

from src.core.combat.combat_core import TeamMemberSelector, BaseResonator, CharClassEnum, ResonatorNameEnum, \
    Morph
from src.core.combat.resonator.aemeath import Aemeath
from src.core.combat.resonator.camellya import Camellya
from src.core.combat.resonator.cantarella import Cantarella
from src.core.combat.resonator.cartethyia import Cartethyia
from src.core.combat.resonator.changli import Changli
from src.core.combat.resonator.ciaccona import Ciaccona
from src.core.combat.resonator.encore import Encore
from src.core.combat.resonator.generic import GenericResonator
from src.core.combat.resonator.hiyuki import Hiyuki
from src.core.combat.resonator.jinhsi import Jinhsi
from src.core.combat.resonator.lucilla import Lucilla
from src.core.combat.resonator.lynae import Lynae
from src.core.combat.resonator.mornye import Mornye
from src.core.combat.resonator.phoebe import Phoebe
from src.core.combat.resonator.phrolova import Phrolova
from src.core.combat.resonator.rover import Rover
from src.core.combat.resonator.sanhua import Sanhua
from src.core.combat.resonator.shorekeeper import Shorekeeper
from src.core.combat.resonator.verina import Verina
from src.core.exceptions import StopError
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class CombatSystem:

    def __init__(self, control_service: ControlService, img_service: ImgService):
        self.control_service: ControlService = control_service
        self.img_service: ImgService = img_service

        self.team_member_selector = TeamMemberSelector(self.control_service, self.img_service)

        self.is_async = False
        self.event = threading.Event()
        # self._thread = threading.Thread(target=self.run)
        # self._thread.daemon = True
        self._thread = None
        self._delay_seconds = None
        self._delay_time = None
        self._lock = threading.Lock()

        self.rover = Rover(self.control_service, self.img_service)
        self.generic_resonator = GenericResonator(self.control_service, self.img_service)

        self.jinhsi = Jinhsi(self.control_service, self.img_service)
        self.changli = Changli(self.control_service, self.img_service)
        self.shorekeeper = Shorekeeper(self.control_service, self.img_service)
        self.encore = Encore(self.control_service, self.img_service)
        self.verina = Verina(self.control_service, self.img_service)
        self.camellya = Camellya(self.control_service, self.img_service)
        self.sanhua = Sanhua(self.control_service, self.img_service)
        self.cartethyia = Cartethyia(self.control_service, self.img_service)
        self.ciaccona = Ciaccona(self.control_service, self.img_service)
        self.phoebe = Phoebe(self.control_service, self.img_service)
        self.phrolova = Phrolova(self.control_service, self.img_service)
        self.lynae = Lynae(self.control_service, self.img_service)
        self.mornye = Mornye(self.control_service, self.img_service)
        self.cantarella = Cantarella(self.control_service, self.img_service)
        self.aemeath = Aemeath(self.control_service, self.img_service)
        self.hiyuki = Hiyuki(self.control_service, self.img_service)
        self.lucilla = Lucilla(self.control_service, self.img_service)

        self.resonator_map: dict[ResonatorNameEnum, BaseResonator] = {
            ResonatorNameEnum.jinhsi: self.jinhsi,
            ResonatorNameEnum.changli: self.changli,
            ResonatorNameEnum.shorekeeper: self.shorekeeper,
            ResonatorNameEnum.encore: self.encore,
            ResonatorNameEnum.verina: self.verina,
            ResonatorNameEnum.camellya: self.camellya,
            ResonatorNameEnum.sanhua: self.sanhua,
            ResonatorNameEnum.cartethyia: self.cartethyia,
            ResonatorNameEnum.ciaccona: self.ciaccona,
            # ResonatorNameEnum.phoebe: self.phoebe,
            ResonatorNameEnum.phrolova: self.phrolova,
            ResonatorNameEnum.lynae: self.lynae,
            ResonatorNameEnum.mornye: self.mornye,
            ResonatorNameEnum.cantarella: self.cantarella,
            ResonatorNameEnum.aemeath: self.aemeath,
            ResonatorNameEnum.hiyuki: self.hiyuki,
            ResonatorNameEnum.lucilla: self.lucilla,
        }
        self.resonators: list[BaseResonator] | None = None
        self._sorted_resonators: list[tuple[BaseResonator, int]] | None = None

        self.auto_pickup: bool = False
        self.check_boss_hp: bool = True

    # def get_resonators(self) -> list[BaseResonator]:
    #     resonators = []
    #     member_names = self.team_member_selector.get_team_members()
    #     member_names_log = []
    #     for member_name in member_names:
    #         resonator = self.resonator_map.get(member_name)
    #         resonators.append(resonator)
    #         member_names_log.append(resonator.name)
    #     logger.info(f"编队: {member_names_log}")
    #     return resonators

    def _sort_resonators(self, resonators: list[BaseResonator]) -> list[tuple[BaseResonator, int]]:
        dps = []
        support = []
        healer = []
        none = []
        for index, resonator in enumerate(resonators):
            if resonator is None:
                none.append((None, index))
                continue
            char_class = resonator.char_class()
            if CharClassEnum.MainDPS in char_class or CharClassEnum.SubDPS in char_class:
                dps.append((resonator, index))
            elif CharClassEnum.Support in char_class:
                support.append((resonator, index))
            elif CharClassEnum.Healer in char_class:
                healer.append((resonator, index))
            else:
                raise ValueError("Unknown enum value")
        # 辅助先于输出
        sorted_resonators: list[tuple[BaseResonator, int]] = support + dps + healer + none
        logger.debug(f"sorted_resonators: {sorted_resonators}")
        return sorted_resonators

    def run(self, event: threading.Event):
        if self.resonators is None:
            return
        if self.resonators and self._sorted_resonators is None:
            self._sorted_resonators = self._sort_resonators(self.resonators)

        index = 0
        exists_length = sum(1 for i in self.resonators if i is not None)
        seq_length = len(self.resonators)

        last_index = index
        last_index_toggle = True
        is_toggle_failed = False
        last_time = None

        while True:
            # 暂停
            # logger.debug("member: %s", index + 1)
            # 主动暂停
            if not event.is_set():
                # logger.info("暂停中，event.is_set()")
                time.sleep(0.3)
                continue
            # 超时暂停
            if self.is_async and self._delay_time - time.monotonic() < 0.0:
                # logger.info("暂停中，delay_time")
                time.sleep(0.3)
                continue

            if last_time is None:
                last_time = time.monotonic()
                self.control_service.activate()
                # self.control_service.camera_reset()
            else:
                cur_time = time.monotonic()
                if cur_time - last_time >= 5:
                    self.control_service.activate()
                last_time = time.monotonic()

            # logger.info("index：%s", index)
            resonator, src_index = self._sorted_resonators[index]
            if resonator is None:
                time.sleep(0.3)
                last_index_toggle = True
                last_index = index
                index = self._next_index(index, seq_length)
                continue

            # 编队至少有两人才切人
            if exists_length > 1:
                is_toggled = self.team_member_selector.toggle(src_index, event=event, resonators=self.resonators)
                logger.debug(f"is_toggled: {is_toggled}")
                if is_toggled is None:
                    index = self._next_index(index, seq_length)
                    continue
                elif is_toggled is False:
                    is_toggle_failed = True
                    index = self._next_index(index, seq_length)
                    continue

                # 大招期间无法切人，若又切到同一个角色，尝试切下一个人，避免单角色连续站场两次
                # 阵亡或当前索引没有角色导致的切人失败而回到当前角色，属于正常，让当前角色再打一套才切
                # 能切（待切索引位有存活角色）但没切过去就继续切
                if last_index == index and last_index_toggle and is_toggle_failed:
                    logger.debug(f"又轮到同一个角色，跳过, member: {index + 1}")
                    index = self._next_index(index, seq_length)
                    last_index_toggle = False
                    continue
                # 切成功，重置状态
                last_index_toggle = True
                is_toggle_failed = False
                last_index = index
                index = self._next_index(index, seq_length)

            resonator.event = event
            resonator.auto_pickup = self.auto_pickup
            resonator.check_boss_hp = self.check_boss_hp
            try:
                # logger.debug(f"combo: {resonator.resonator_name().value}")
                resonator.combo()
            except StopError:  # 主动抛出异常快速跳出连招序列
                pass
            finally:
                self.control_service.mouse_left_up()
                self.control_service.mouse_right_up()

    def _next_index(self, index, seq_length) -> int:
        next_index = index + 1
        if next_index >= seq_length:
            next_index = 0
        return next_index

    def start(self, delay_seconds: float = 0.0):
        if self.is_async:
            with self._lock:
                # logger.info("Combat system started.")
                if not self.event.is_set():
                    self.control_service.camera_reset()
                self.event.set()
                if delay_seconds > 0.0:
                    self._delay_seconds = delay_seconds
                    self._delay_time = time.monotonic() + delay_seconds
                    # logger.debug(f"+{delay_seconds}s")
                if self._thread is None:
                    self._thread = threading.Thread(target=self.run, args=(self.event,))
                    self._thread.daemon = True
                    self._delay_seconds = delay_seconds
                    self._thread.start()
        else:
            self.event.set()
            self.run(self.event)

    def stop(self, join: bool = False):
        with self._lock:
            self.event.clear()
            t = self._thread
            if self.is_async:
                self._thread = None
            if not join:
                return
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                t.join(0.1)
                if not t.is_alive():
                    break

    def pause(self):
        with self._lock:
            self.event.clear()
            # logger.debug("combat pause")

    def set_resonators(self, resonator_names_zh: list[str | None]):
        resonators: list[BaseResonator] = []
        _resonators_names_en = []
        for name_zh in resonator_names_zh:
            if not name_zh:
                break
            resonator_temp = None
            if name_zh == ResonatorNameEnum.rover.value:
                resonator_temp = self.rover
            elif name_zh == ResonatorNameEnum.none.value:
                resonator_temp = None
            else:
                name_enum = ResonatorNameEnum.get_enum_by_value(name_zh)
                if name_enum:
                    # 找出定制连招
                    resonator_temp = self.resonator_map.get(name_enum)
                # 没有定制连招则使用默认连招
                if resonator_temp is None:
                    resonator_temp = self.generic_resonator
            resonators.append(resonator_temp)
            _resonators_names_en.append(resonator_temp.resonator_name().name if resonator_temp else None)

        logger.info(f"team_members: {_resonators_names_en}")
        logger.info(f"编队: {resonator_names_zh}")
        self.resonators = resonators

    def is_boss_health_bar_exist(self, img=None):
        if img is None:
            img = self.img_service.screenshot()
        return BaseResonator.is_boss_health_bar_exist(img)

    def boss_immobilized_bar_exist(self, img=None):
        if img is None:
            img = self.img_service.screenshot()
        return BaseResonator.boss_immobilized_bar_exist(img)

    def exit_special_state(self, morph: Morph) -> bool:
        if self.resonators is None:
            return True
        try:
            toggle_list = list(range(1, len(self.resonators) + 1))
            cur_member_number = self.team_member_selector.get_cur_member_number(self.resonators)
            if cur_member_number in toggle_list:
                toggle_list.remove(cur_member_number)
                toggle_list.insert(0, cur_member_number)
            # logger.debug(f"toggle_list: {toggle_list}")
            for i, cur_member_number in enumerate(toggle_list):
                # logger.debug(f"cur_member_number: {cur_member_number}")
                resonator = self.resonators[cur_member_number - 1]
                if i > 0:
                    img = self.img_service.screenshot()
                    if resonator.is_avatar_grey(img, cur_member_number):
                        continue
                    time.sleep(0.1)
                    self.control_service.toggle_team_member(cur_member_number)
                    time.sleep(0.35)
                    toggled_member_number = self.team_member_selector.get_cur_member_number(self.resonators)
                    # logger.debug(f"toggled_member_number: {toggled_member_number}")
                    if toggled_member_number is None:
                        break
                    if toggled_member_number != cur_member_number:
                        # 以防万一，关掉复活药弹窗
                        self.control_service.attack()
                        time.sleep(0.2)
                        continue

                exit_result = resonator.exit_special_state(morph)
                if exit_result:
                    break
        except (KeyboardInterrupt, StopError) as e:
            raise e
        except Exception as e:
            logger.exception(e)
        return True
