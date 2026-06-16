from PySide6.QtCore import Signal, QObject


class GlobalSignal(QObject):
    """ Signal """
    closeMainWindowSignal = Signal()  # gui关闭信号，右上角的关闭
    guiExistSignal = Signal()  # 有同路径的gui启动了，不允许，发送信号通知并退出
    taskChangedSignal = Signal(object)  # 当前选择的运行任务，各页面实时发给运行按钮
    executeTaskSignal = Signal(str, str)  # 运行按钮提交运行任务给后台，任务名 和 启动/停止
    taskFinishedSignal = Signal(str)  # 后台任务运行结束，后台发给前台的运行按钮
    taskInfoBarSignal = Signal(str, str, int)  # 后台任务实时发送运行消息给前台展示运行情况
    paramConfigPathSignal = Signal(str)  # 参数配置文件的路径
    guiWinId = Signal(int)  # gui主窗口hwnd


class GlobalParam:

    def __init__(self):
        self.logFile = None
        self.logQueue = None
        self.gamePath = None  # winreg内游戏的路径


# 前后端交互专用信号和参数
globalSignal = GlobalSignal()
globalParam = GlobalParam()
