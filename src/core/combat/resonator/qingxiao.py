import logging

from src.core.combat.combat_core import BaseResonator, CharClassEnum, ResonatorNameEnum, Morph, combat_cache
from src.core.combat.resonator.generic import GenericCombo
from src.core.exceptions import StopError
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseQingxiao(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.qingxiao

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.MainDPS]


class Qingxiao(BaseQingxiao):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)
        self._generic_combo = GenericCombo(control_service)

    @combat_cache
    def jump(self):
        return [
            ["j", 0.05, 1.2],
        ]

    def exit_special_state(self, morph: Morph) -> bool:
        logger.debug("exit_special_state")
        # 退出御剑
        self.combo_action(self.jump(), True, ignore_event=True)
        return True

    def combo(self):
        self._generic_combo.combo(self)
