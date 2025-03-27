from src.controller.main_controller import MainController
from src.gui.gui import GuiController, wwa

APPLICATION = MainController()
GUI = GuiController()

# 前端连接信号到后端函数
GUI.task_run_requested.connect(APPLICATION.execute)

def run():
    wwa()