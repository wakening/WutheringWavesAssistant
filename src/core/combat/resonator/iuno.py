import logging

from src.core.combat.combat_core import BaseResonator, CharClassEnum, ResonatorNameEnum, Morph
from src.core.combat.resonator.generic import GenericCombo
from src.core.interface import ControlService, ImgService

logger = logging.getLogger(__name__)


class BaseIuno(BaseResonator):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)

    def __str__(self):
        return self.resonator_name().name

    def resonator_name(self) -> ResonatorNameEnum:
        return ResonatorNameEnum.iuno

    def char_class(self) -> list[CharClassEnum]:
        return [CharClassEnum.SubDPS]


class Iuno(BaseIuno):

    def __init__(self, control_service: ControlService, img_service: ImgService):
        super().__init__(control_service, img_service)
        self._generic_combo = GenericCombo(control_service)

    def exit_special_state(self, morph: Morph) -> bool:
        logger.debug("exit_special_state")
        return False

    def combo(self):
        self._generic_combo.combo(self)
