import logging
from typing import Union, List

from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QIcon, QColor, QIntValidator
from PySide6.QtWidgets import (QWidget, QLabel, QFileDialog, QFrame, QVBoxLayout, QButtonGroup, QHBoxLayout,
                               QPushButton, QApplication, QSizePolicy, QFormLayout, QCheckBox, QGridLayout)
from qfluentwidgets import (FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition,
                            InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit, InfoBar,
                            SettingCardGroup, ScrollArea, ExpandLayout, ExpandSettingCard, FluentIconBase,
                            OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
                            SingleDirectionScrollArea, PrimaryPushButton, FluentStyleSheet,
                            LineEdit, SettingCard, ComboBox, ConfigItem,
                            PushButton, ToolButton, MessageBox)

logger = logging.getLogger(__name__)


class ReadOnlyCheckBox(CheckBox):
    def mousePressEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        event.ignore()


class CheckCard(QFrame):
    toggled = Signal(bool)
    clicked = Signal(bool)
    stateChanged = Signal(int)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.checkbox = CheckBox(text, self)
        self.checkbox.setCheckable(True)

        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 1, 0, 1)
        self.mainLayout.addWidget(self.checkbox)
        self.mainLayout.addStretch()
        self.mainLayout.setAlignment(Qt.AlignVCenter)

        self.checkbox.toggled.connect(self.toggled)
        self.checkbox.clicked.connect(self.clicked)
        self.checkbox.stateChanged.connect(self.stateChanged)

        # self.setObjectName('view')

    def mousePressEvent(self, event):
        pos = event.position().toPoint()

        # 点到 checkbox 本身时交给 Qt 处理
        if self.checkbox.geometry().contains(pos):
            return super().mousePressEvent(event)

        self.checkbox.toggle()
        super().mousePressEvent(event)

    def isChecked(self) -> bool:
        return self.checkbox.isChecked()

    def setChecked(self, checked: bool):
        self.checkbox.setChecked(checked)

    def text(self) -> str:
        return self.checkbox.text()

    def setText(self, text: str):
        self.checkbox.setText(text)

    def blockSignals(self, block: bool) -> bool:
        previous = super().blockSignals(block)
        self.checkbox.blockSignals(block)
        return previous

    def setBackground(self):
        self.setStyleSheet("""
            CheckCard {
                background-color: rgba(0, 255, 0, 0.1);
                border-radius: 16px;
            }
        """)
