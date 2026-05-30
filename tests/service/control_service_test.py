import logging

from src.core.contexts import Context
from src.service.control_service import Win32ControlServiceImpl
from src.service.window_service import HwndServiceImpl
from src.util import hwnd_util, keymouse_util

logger = logging.getLogger(__name__)


def test_controls():
    logger.debug("\n")
    # hwnd = hwnd_util.get_hwnd()
    context = Context()
    # context = None
    window_service = HwndServiceImpl(context)
    hwnd = window_service.window
    keymouse_util.window_activate(hwnd)
    control = Win32ControlServiceImpl(context, window_service)
    control.left().sleep(0.5).left().sleep(1)
    control.down().sleep(0.5).down().sleep(1)
    control.right().sleep(0.5).right().sleep(1)
    control.up().sleep(0.5).up().sleep(1)
    control.camera_reset().sleep(2)
    control.right_click().sleep().sleep(2)
    control.attack().click().attack().sleep(2)
    control.dash_dodge().sleep(2)
    control.jump().sleep(2)
    control.resonance_skill().sleep(2)
    control.echo_skill().sleep(2)
    control.resonance_liberation().sleep(5)
    control.guidebook().sleep(3).guidebook().sleep(3)
    control.map().sleep(3).map().sleep(3)
    control.team_member1().sleep(1).team_member2().sleep(1).team_member3().sleep(1)
    control.events().sleep(3).events().sleep(3)
    control.use_utility().sleep(2)