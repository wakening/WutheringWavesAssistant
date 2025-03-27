import logging

from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

logger = logging.getLogger(__name__)


def mute_program(exe_name: str, mute: bool = True) -> bool:
    """
    设置程序是否静音，需要目标进程正在运行

    :param exe_name: 程序的 exe 名称（例如 'chrome.exe'）
    :param mute: True = 静音, False = 取消静音
    :return 是否设置成功
    """
    # 获取所有音频会话
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        process = session.Process
        if not process:
            continue
        # noinspection PyProtectedMember
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        logger.debug("Process: %s, mute: %s", process.name(), "Muted 🔇" if volume.GetMute() else "Unmuted 🔊")
        if process.name().lower() == exe_name.lower():
            volume.SetMute(mute, None)
            logger.info("[+] %s: %s", exe_name, "Muted 🔇" if mute else "Unmuted 🔊")
            return True
    return False


def is_muted(exe_name: str) -> bool | None:
    """
    程序是否静音了，需要目标进程正在运行

    :param exe_name: 程序的 exe 名称（例如 'chrome.exe'）
    :return True 静音了 False 没静音 None 目标进程不存在
    """
    # 获取所有音频会话
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        process = session.Process
        if not process:
            continue
        # noinspection PyProtectedMember
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        logger.debug("Process: %s, mute: %s", process.name(), "Muted 🔇" if volume.GetMute() else "Unmuted 🔊")
        if process.name().lower() == exe_name.lower():
            return bool(volume.GetMute())
    logger.debug("Process [%s] is not found!", exe_name)
    return None
