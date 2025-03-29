# coding:utf-8
import logging

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QButtonGroup

from qfluentwidgets import IconWidget, TextWrap, FlowLayout, CardWidget, SwitchButton, IndicatorPosition, \
    ToggleToolButton, FluentIcon, ProgressRing, IndeterminateProgressRing
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ... import application

logger = logging.getLogger(__name__)

class SampleCard(CardWidget):
    """ Sample card """

    task_selected = Signal(str)

    def __init__(self, icon, title, content, routeKey, index, parent=None, group_index = None, task_name = None):
        super().__init__(parent=parent)
        self.index = index
        self.routekey = routeKey

        self.iconWidget = IconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(TextWrap.wrap(content, 57, False)[0], self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedSize(570, 90)
        self.iconWidget.setFixedSize(48, 48)

        self.hBoxLayout.setSpacing(28)
        self.hBoxLayout.setContentsMargins(20, 0, 20, 0)
        self.vBoxLayout.setSpacing(2)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self.switchButton = SwitchButton(self.tr('Off'), parent=self, indicatorPos=IndicatorPosition.LEFT)
        self.switchButton.checkedChanged.connect(self.onCheckedChanged)

        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addStretch()  # 添加一个弹性空间，让后面的控件推到最右侧
        self.hBoxLayout.addWidget(self.switchButton)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.contentLabel)
        self.vBoxLayout.addStretch(1)

        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')

        self.parentCardManager = parent
        self.group_index = group_index
        self.task_name = task_name

    def onCheckedChanged(self, isChecked: bool):
        if self.group_index > 3:
            self.switchButton.setChecked(False)
            return

        if isChecked:
            if self.parentCardManager:
                self.parentCardManager.handleSwitchChange(self.group_index)
                self.task_selected.emit(self.task_name)
        text = 'On' if isChecked else 'Off'
        self.switchButton.setText(self.tr(text))



class RunCard(CardWidget):
    """ Sample card """



    def __init__(self, icon, title, content, routeKey, index, parent=None):
        super().__init__(parent=parent)
        self.index = index
        self.routekey = routeKey

        self.spinner = IndeterminateProgressRing(self, start=False)
        self.spinner.setStrokeWidth(4)

        # self.iconWidget = IconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        # self.contentLabel = QLabel(TextWrap.wrap(content, 45, False)[0], self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedSize(570, 90)
        # self.iconWidget.setFixedSize(40, 40)
        self.spinner.setFixedSize(40, 40)

        self.hBoxLayout.setSpacing(28)
        self.hBoxLayout.setContentsMargins(36, 0, 20, 0)
        self.vBoxLayout.setSpacing(2)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        # self.switchButton = SwitchButton(self.tr('Off'), parent=self, indicatorPos=IndicatorPosition.LEFT)
        # self.switchButton.checkedChanged.connect(self.onCheckedChanged)
        self.button = ToggleToolButton(FluentIcon.PLAY_SOLID, self)
        self.button.clicked.connect(self.onButtonClicked)
        self.button.setFixedSize(100, 50)

        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        # self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addStretch()  # 添加一个弹性空间，让后面的控件推到最右侧
        self.hBoxLayout.addWidget(self.spinner)
        self.hBoxLayout.addWidget(self.button)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.titleLabel)
        # self.vBoxLayout.addWidget(self.contentLabel)
        self.vBoxLayout.addStretch(1)

        self.titleLabel.setObjectName('titleLabel')
        # self.contentLabel.setObjectName('contentLabel')

        self.parentCardManager = parent
        # self.group_index = group_index
        self.task_name = None
        self.running_task_name = None

    # def onCheckedChanged(self, isChecked: bool):
    #     if isChecked:
    #         if self.parentCardManager:
    #             self.parentCardManager.handleSwitchChange(self.group_index)
    #
    #     text = 'On' if isChecked else 'Off'
    #     self.switchButton.setText(self.tr(text))

    def onButtonClicked(self):
        logger.info("任务名: %s", self.task_name)
        if self.button.isChecked():
            self.button.setIcon(FluentIcon.PAUSE_BOLD)
            self.spinner.start()
            if self.task_name:
                self.running_task_name = self.task_name
                application.GUI.on_run_clicked(self.running_task_name, "START")
            else:
                logger.info("没有要运行的任务")
        else: # stop
            self.spinner.stop()
            self.spinner.reset()
            if self.running_task_name:
                application.GUI.on_run_clicked(self.running_task_name, "STOP")
                self.running_task_name = None
            self.button.setIcon(FluentIcon.PLAY_SOLID)

    def update_task(self, task_name: str):
        self.task_name = task_name


class SampleCardView(QWidget):
    """ Sample card view """

    def __init__(self, title: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.flowLayout = FlowLayout()

        self.vBoxLayout.setContentsMargins(36, 0, 36, 0)
        self.vBoxLayout.setSpacing(10)
        self.flowLayout.setContentsMargins(0, 0, 0, 0)
        self.flowLayout.setHorizontalSpacing(12)
        self.flowLayout.setVerticalSpacing(12)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.flowLayout, 1)

        self.titleLabel.setObjectName('viewTitleLabel')
        StyleSheet.SAMPLE_CARD.apply(self)

        self.card_group: list[SampleCard] = []
        self.select_task = None
        self.run = None

    def addSampleCard(self, icon, title, content, routeKey, index, task_name):
        """ add sample card """
        card = SampleCard(icon, title, content, routeKey, index, self, len(self.card_group), task_name)
        self.flowLayout.addWidget(card)
        self.card_group.append(card)

    def addRun(self, icon, title, content, routeKey, index):
        self.run = RunCard(icon, title, content, routeKey, index, self)
        self.flowLayout.addWidget(self.run)
        return self.run

    def handleSwitchChange(self, group_index: int):
        """ Ensure that only one switch button is active at a time """
        for i in range(len(self.card_group)):
            if i != group_index:
                self.card_group[i].switchButton.setChecked(False)

    # def set_task_name(self, select_task: str):
    #     self.select_task = select_task
    #
    # def get_task_name(self):
    #     return self.select_task