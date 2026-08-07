# coding: utf-8
from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """ Signal bus """

    switchToSampleCard = Signal(str, int)
    micaEnableChanged = Signal(bool)
    windowSizeChanged = Signal(object)
    supportSignal = Signal()

    logQueueSignal = Signal(tuple)  # 日志队列信号，表明队列有新日志
    homeMessageSignal = Signal(str)


signalBus = SignalBus()
