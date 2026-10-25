from __future__ import annotations

import sys
from collections.abc import Iterable
from typing import Union

from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QFont,
    QFontDatabase,
    QIcon,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QStyle,
    QStyledItemDelegate,
    QWidget,
)

from qfluentwidgets import (
    FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition,
    InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit, InfoBar,
    SettingCardGroup, ScrollArea, ExpandLayout, ExpandSettingCard, FluentIconBase,
    OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
    SingleDirectionScrollArea, PrimaryPushButton,
    LineEdit, SettingCard, ConfigItem,
    PushButton, ToolButton, MessageBox, ToggleToolButton, RoundMenu, isDarkTheme, themeColor, ThemeColor,
    MenuAnimationType, setFont, IndicatorMenuItemDelegate,
)
from qfluentwidgets.common.animation import TranslateYAnimation
from qfluentwidgets.components.widgets.check_box import CheckBoxIcon

from src.gui.common.style_sheet import StyleSheet
from src.gui.components.widgets.button import SubClip


# from ...common.animation import TranslateYAnimation
# from ...common.color import fallbackThemeColor, validColor
# from ...common.font import setFont
# from ...common.icon import FluentIcon as FIF
# from ...common.icon import FluentIconBase, isDarkTheme
# from ...common.style_sheet import FluentStyleSheet, ThemeColor, themeColor
# from .button import SubClip
# from .line_edit import LineEdit, LineEditButton
# from .menu import (
#     IndicatorMenuItemDelegate,
#     MenuAnimationType,
#     MenuItemDelegate,
#     RoundMenu,
# )
# from .scroll_area import SingleDirectionScrollArea
#

def fallbackThemeColor(color: QColor):
    return color if color.isValid() else themeColor()

def validColor(color: QColor, default: QColor) -> QColor:
    return color if color.isValid() else default


class ComboItem:
    """Combo box item"""

    def __init__(
        self,
        text: str,
        icon: Union[str, QIcon, FluentIconBase] = None,
        userData=None,
        isEnabled=True,
    ):
        """add item

        Parameters
        ----------
        text: str
            the text of item

        icon: str | QIcon | FluentIconBase
            the icon of item

        userData: Any
            user data

        isEnabled: bool
            whether to enable the item
        """
        self.text = text
        self.userData = userData
        self.icon = icon
        self.isEnabled = isEnabled

    @property
    def icon(self):
        if isinstance(self._icon, QIcon):
            return self._icon

        return self._icon.icon()

    @icon.setter
    def icon(self, ico: Union[str, QIcon, FluentIconBase]):
        if ico:
            self._icon = QIcon(ico) if isinstance(ico, str) else ico
        else:
            self._icon = QIcon()


class ComboBoxBase:
    """Combo box base"""

    activated = Signal(int)
    textActivated = Signal(str)

    def __init__(self, parent=None, **kwargs):
        pass

    def _setUpUi(self):
        self.isHover = False
        self.isPressed = False
        self.items = []  # type: List[ComboItem]
        self._currentIndex = -1
        self._maxVisibleItems = -1
        self.dropMenu = None
        self._placeholderText = ""

        # FluentStyleSheet.COMBO_BOX.apply(self)
        StyleSheet.COMBO_BOX.apply(self)
        self.installEventFilter(self)

    def addItem(
        self, text, icon: Union[str, QIcon, FluentIconBase] = None, userData=None
    ):
        """add item

        Parameters
        ----------
        text: str
            the text of item

        icon: str | QIcon | FluentIconBase
        """
        item = ComboItem(text, icon, userData)
        self.items.append(item)
        if len(self.items) == 1:
            self.setCurrentIndex(0)

    def addItems(self, texts: Iterable[str]):
        """add items

        Parameters
        ----------
        text: Iterable[str]
            the text of item
        """
        for text in texts:
            self.addItem(text)

    def removeItem(self, index: int):
        """Removes the item at the given index from the combobox.
        This will update the current index if the index is removed.
        """
        if not 0 <= index < len(self.items):
            return

        self.items.pop(index)

        if index < self.currentIndex():
            self.setCurrentIndex(self._currentIndex - 1)
        elif index == self.currentIndex():
            if index > 0:
                self.setCurrentIndex(self._currentIndex - 1)
            else:
                self.setText(self.itemText(0))
                self.currentTextChanged.emit(self.currentText())
                self.currentIndexChanged.emit(0)

        if self.count() == 0:
            self.clear()

    def currentIndex(self):
        return self._currentIndex

    def setCurrentIndex(self, index: int):
        """set current index

        Parameters
        ----------
        index: int
            current index
        """
        if not 0 <= index < len(self.items) or index == self.currentIndex():
            return

        oldText = self.currentText()

        self._currentIndex = index
        self.setText(self.items[index].text)

        if oldText != self.currentText():
            self.currentTextChanged.emit(self.currentText())

        self.currentIndexChanged.emit(index)

    def setText(self, text: str):
        super().setText(text)
        self.adjustSize()

    def currentText(self):
        if not 0 <= self.currentIndex() < len(self.items):
            return ""

        return self.items[self.currentIndex()].text

    def currentData(self):
        if not 0 <= self.currentIndex() < len(self.items):
            return None

        return self.items[self.currentIndex()].userData

    def setCurrentText(self, text):
        """set the current text displayed in combo box,
        text should be in the item list

        Parameters
        ----------
        text: str
            text displayed in combo box
        """
        if text == self.currentText():
            return

        index = self.findText(text)
        if index >= 0:
            self.setCurrentIndex(index)

    def setItemText(self, index: int, text: str):
        """set the text of item

        Parameters
        ----------
        index: int
            the index of item

        text: str
            new text of item
        """
        if not 0 <= index < len(self.items):
            return

        self.items[index].text = text
        if self.currentIndex() == index:
            self.setText(text)

    def itemData(self, index: int):
        """Returns the data in the given index"""
        if not 0 <= index < len(self.items):
            return None

        return self.items[index].userData

    def itemText(self, index: int):
        """Returns the text in the given index"""
        if not 0 <= index < len(self.items):
            return ""

        return self.items[index].text

    def itemIcon(self, index: int):
        """Returns the icon in the given index"""
        if not 0 <= index < len(self.items):
            return QIcon()

        return self.items[index].icon

    def setItemData(self, index: int, value):
        """Sets the data role for the item on the given index"""
        if 0 <= index < len(self.items):
            self.items[index].userData = value

    def setItemIcon(self, index: int, icon: Union[str, QIcon, FluentIconBase]):
        """Sets the data role for the item on the given index"""
        if 0 <= index < len(self.items):
            self.items[index].icon = icon

    def setItemEnabled(self, index: int, isEnabled: bool):
        """Sets the enabled status of the item on the given index"""
        if 0 <= index < len(self.items):
            self.items[index].isEnabled = isEnabled

    def findData(self, data):
        """Returns the index of the item containing the given data, otherwise returns -1"""
        for i, item in enumerate(self.items):
            if item.userData == data:
                return i

        return -1

    def findText(self, text: str):
        """Returns the index of the item containing the given text; otherwise returns -1."""
        for i, item in enumerate(self.items):
            if item.text == text:
                return i

        return -1

    def clear(self):
        """Clears the combobox, removing all items."""
        if self.currentIndex() >= 0:
            self.setText("")

        self.items.clear()
        self._currentIndex = -1

    def count(self):
        """Returns the number of items in the combobox"""
        return len(self.items)

    def insertItem(
        self,
        index: int,
        text: str,
        icon: Union[str, QIcon, FluentIconBase] = None,
        userData=None,
    ):
        """Inserts item into the combobox at the given index."""
        item = ComboItem(text, icon, userData)
        self.items.insert(index, item)

        if index <= self.currentIndex():
            self.setCurrentIndex(self.currentIndex() + 1)

    def insertItems(self, index: int, texts: Iterable[str]):
        """Inserts items into the combobox, starting at the index specified."""
        pos = index
        for text in texts:
            item = ComboItem(text)
            self.items.insert(pos, item)
            pos += 1

        if index <= self.currentIndex():
            self.setCurrentIndex(self.currentIndex() + pos - index)

    def setMaxVisibleItems(self, num: int):
        self._maxVisibleItems = num

    def maxVisibleItems(self):
        return self._maxVisibleItems

    def _closeComboMenu(self):
        if not self.dropMenu:
            return

        # drop menu could be deleted before this method
        try:
            self.dropMenu.close()
        except Exception:
            pass

        self.dropMenu = None

    def _onDropMenuClosed(self):
        if sys.platform != "win32":
            self.dropMenu = None
        else:
            pos = self.mapFromGlobal(QCursor.pos())
            if not self.rect().contains(pos):
                self.dropMenu = None

    def _createComboMenu(self):
        return ComboBoxMenu(self)

    def _showComboMenu(self):
        if not self.items:
            return

        menu = self._createComboMenu()
        for item in self.items:
            action = QAction(item.icon, item.text)
            action.setEnabled(item.isEnabled)
            menu.addAction(action)

        # fixes issue #468
        menu.view.itemClicked.connect(
            lambda i: self._onItemClicked(self.findText(i.text().lstrip()))
        )

        if menu.view.width() < self.width():
            menu.view.setMinimumWidth(self.width())
            menu.adjustSize()

        menu.setMaxVisibleItems(self.maxVisibleItems())
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        menu.closedSignal.connect(self._onDropMenuClosed)
        self.dropMenu = menu

        # set the selected item
        if self.currentIndex() >= 0 and self.items:
            menu.setDefaultAction(menu.actions()[self.currentIndex()])

        # determine the animation type by choosing the maximum height of view
        x = (
            -menu.width() // 2
            + menu.layout().contentsMargins().left()
            + self.width() // 2
        )
        pd = self.mapToGlobal(QPoint(x, self.height()))
        hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)

        pu = self.mapToGlobal(QPoint(x, 0))
        hu = menu.view.heightForAnimation(pu, MenuAnimationType.PULL_UP)

        if hd >= hu:
            menu.view.adjustSize(pd, MenuAnimationType.DROP_DOWN)
            menu.exec(pd, aniType=MenuAnimationType.DROP_DOWN)
        else:
            menu.view.adjustSize(pu, MenuAnimationType.PULL_UP)
            menu.exec(pu, aniType=MenuAnimationType.PULL_UP)

    def _toggleComboMenu(self):
        if self.dropMenu:
            self._closeComboMenu()
        else:
            self._showComboMenu()

    def _onItemClicked(self, index):
        if not self.items[index].isEnabled:
            return

        if index != self.currentIndex():
            self.setCurrentIndex(index)

        self.activated.emit(index)
        self.textActivated.emit(self.currentText())


class ComboBox(QPushButton, ComboBoxBase):
    """Combo box"""

    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)
    activated = Signal(int)
    textActivated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.arrowAni = TranslateYAnimation(self)
        self._setUpUi()
        setFont(self)

    def eventFilter(self, obj, e: QEvent):
        if obj is self:
            if e.type() == QEvent.MouseButtonPress:
                self.isPressed = True
            elif e.type() == QEvent.MouseButtonRelease:
                self.isPressed = False
            elif e.type() == QEvent.Enter:
                self.isHover = True
            elif e.type() == QEvent.Leave:
                self.isHover = False

        return super().eventFilter(obj, e)

    def setPlaceholderText(self, text: str):
        self._placeholderText = text

        if self.currentIndex() <= 0:
            self._updateTextState(True)
            self.setText(text)

    def setCurrentIndex(self, index: int):
        if index < 0:
            self._currentIndex = -1
            self.setPlaceholderText(self._placeholderText)
        elif 0 <= index < len(self.items):
            self._updateTextState(False)
            super().setCurrentIndex(index)

    def _updateTextState(self, isPlaceholder):
        if self.property("isPlaceholderText") == isPlaceholder:
            return

        self.setProperty("isPlaceholderText", isPlaceholder)
        self.setStyle(QApplication.style())

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._toggleComboMenu()

    def paintEvent(self, e):
        QPushButton.paintEvent(self, e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isHover:
            painter.setOpacity(0.8)
        elif self.isPressed:
            painter.setOpacity(0.7)

        rect = QRectF(
            self.width() - 22, self.height() / 2 - 5 + self.arrowAni.y, 10, 10
        )
        if isDarkTheme():
            FIF.ARROW_DOWN.render(painter, rect)
        else:
            FIF.ARROW_DOWN.render(painter, rect, fill="#646464")


class ComboBoxMenu(RoundMenu):
    """Combo box menu"""

    def __init__(self, parent=None):
        super().__init__(title="", parent=parent)

        self.view.setViewportMargins(0, 2, 0, 6)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setItemDelegate(IndicatorMenuItemDelegate())
        self.view.setObjectName("comboListWidget")

        self.setItemHeight(33)

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        self.view.adjustSize(pos, aniType)
        self.adjustSize()
        return super().exec(pos, ani, aniType)


class CheckBoxMenuItemDelegate(QStyledItemDelegate):
    """Check box menu item delegate for multi-select combo box

    Uses the same drawing logic as CheckBox widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def _borderColor(
        self, isDark: bool, isChecked: bool, isHover: bool, isPressed: bool
    ):
        """Get border color based on state - matches CheckBox"""
        if isDark:
            if isChecked:
                return fallbackThemeColor(QColor())
            elif isPressed:
                return QColor(255, 255, 255, 40)
            elif isHover:
                return QColor(255, 255, 255, 141)
            else:
                return QColor(255, 255, 255, 141)
        else:
            if isChecked:
                return fallbackThemeColor(QColor())
            elif isPressed:
                return QColor(0, 0, 0, 69)
            elif isHover:
                return QColor(0, 0, 0, 143)
            else:
                return QColor(0, 0, 0, 122)

    def _backgroundColor(
        self, isDark: bool, isChecked: bool, isHover: bool, isPressed: bool
    ):
        """Get background color based on state - matches CheckBox"""
        if isDark:
            if isChecked:
                return fallbackThemeColor(QColor())
            elif isPressed:
                return QColor(255, 255, 255, 18)
            elif isHover:
                return QColor(255, 255, 255, 11)
            else:
                return QColor(0, 0, 0, 26)
        else:
            if isChecked:
                return fallbackThemeColor(QColor())
            elif isPressed:
                return QColor(0, 0, 0, 31)
            elif isHover:
                return QColor(0, 0, 0, 13)
            else:
                return QColor(0, 0, 0, 6)

    def paint(self, painter, option, index):
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        isChecked = index.data(Qt.CheckStateRole) == Qt.Checked
        isHover = option.state & QStyle.State_MouseOver
        isPressed = option.state & QStyle.State_Sunken

        # draw background for checked or hover state with rounded corners and padding
        bgRect = option.rect.adjusted(6, 2, -6, -2)
        if isChecked:
            # selected item background
            bgColor = QColor(255, 255, 255, 9) if isDark else QColor(0, 0, 0, 9)
            painter.setPen(Qt.NoPen)
            painter.setBrush(bgColor)
            painter.drawRoundedRect(bgRect, 5, 5)
        if isHover:
            painter.setPen(Qt.NoPen)
            painter.setBrush(
                QColor(255, 255, 255, 10) if isDark else QColor(0, 0, 0, 10)
            )
            painter.drawRoundedRect(bgRect, 5, 5)

        # draw check box indicator with more left padding
        rect = QRect(14, option.rect.top() + (option.rect.height() - 18) // 2, 18, 18)

        # draw border and background
        borderColor = self._borderColor(isDark, isChecked, bool(isHover), isPressed)
        bgColor = self._backgroundColor(isDark, isChecked, bool(isHover), isPressed)

        if isChecked:
            bgColor = validColor(
                bgColor,
                ThemeColor.DARK_1.color() if isDark else ThemeColor.LIGHT_1.color(),
            )

        painter.setPen(QPen(borderColor, 1.5))
        painter.setBrush(bgColor)
        painter.drawRoundedRect(rect, 4.5, 4.5)

        # draw check mark using the same style as CheckBox
        if isChecked:
            # from .check_box import CheckBoxIcon

            CheckBoxIcon.ACCEPT.render(painter, rect)

        # draw text with more left padding
        text = index.data(Qt.DisplayRole)
        if text:
            painter.setPen(Qt.white if isDark else Qt.black)
            painter.setFont(option.font)
            textRect = option.rect.adjusted(40, 0, -8, 0)
            painter.drawText(textRect, Qt.AlignVCenter | Qt.AlignLeft, text)

    def sizeHint(self, option, index):
        return QSize(100, 36)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            # toggle check state
            currentState = index.data(Qt.CheckStateRole)
            newState = Qt.Unchecked if currentState == Qt.Checked else Qt.Checked
            model.setData(index, newState, Qt.CheckStateRole)
            return True
        return False


class MultiSelectionComboBoxMenu(RoundMenu):
    """Multi-select combo box menu with check boxes"""

    def __init__(self, parent=None):
        super().__init__(title="", parent=parent)
        self.view.setViewportMargins(0, 5, 0, 5)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setItemDelegate(CheckBoxMenuItemDelegate())
        self.view.setObjectName("multiSelectComboListWidget")
        self.setItemHeight(36)

    def _onItemClicked(self, item):
        """Override to prevent menu from closing on item click"""
        action = item.data(Qt.UserRole)
        if action and action.isEnabled():
            action.trigger()

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        self.view.adjustSize(pos, aniType)
        self.adjustSize()
        return super().exec(pos, ani, aniType)


# class MultiSelectionComboBox(QPushButton):
#     """Multi-select combo box with check boxes"""
#
#     selectionChanged = Signal(set)
#     selectedTextChanged = Signal(list)
#
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#         self.arrowAni = TranslateYAnimation(self)
#         self._setUpUi()
#         setFont(self)
#
#     def _setUpUi(self):
#         self.isHover = False
#         self.isPressed = False
#         self.items: list[ComboItem] = []
#         self._selectedIndices: set[int] = set()
#         self._placeholderText = ""
#         self._maxVisibleItems = -1
#         self.dropMenu = None
#         self._chipsMode = False
#
#         # FluentStyleSheet.COMBO_BOX.apply(self)
#         StyleSheet.COMBO_BOX.apply(self)
#         self.installEventFilter(self)
#
#     def setChipsMode(self, enabled: bool = True):
#         """Set whether to use chips display mode"""
#         self._chipsMode = enabled
#         self._updateDisplay()
#
#     def isChipsMode(self) -> bool:
#         """Return whether chips mode is enabled"""
#         return self._chipsMode
#
#     def eventFilter(self, obj, e: QEvent):
#         if obj is self:
#             if e.type() == QEvent.MouseButtonPress:
#                 self.isPressed = True
#             elif e.type() == QEvent.MouseButtonRelease:
#                 self.isPressed = False
#             elif e.type() == QEvent.Enter:
#                 self.isHover = True
#             elif e.type() == QEvent.Leave:
#                 self.isHover = False
#         return super().eventFilter(obj, e)
#
#     def addItem(
#         self, text: str, icon: Union[str, QIcon, FluentIconBase] = None, userData=None
#     ):
#         """Add an item"""
#         item = ComboItem(text, icon, userData)
#         self.items.append(item)
#
#     def addItems(self, texts: Iterable[str]):
#         """Add multiple items"""
#         for text in texts:
#             self.addItem(text)
#
#     def removeItem(self, index: int):
#         """Remove item at index"""
#         if not 0 <= index < len(self.items):
#             return
#         self.items.pop(index)
#         # update selected indices
#         newSelected = set()
#         for i in self._selectedIndices:
#             if i < index:
#                 newSelected.add(i)
#             elif i > index:
#                 newSelected.add(i - 1)
#         self._selectedIndices = newSelected
#         self._updateDisplay()
#
#     def clear(self):
#         """Clear all items"""
#         self.items.clear()
#         self._selectedIndices.clear()
#         self.setText("")
#         self._currentIndex = -1
#
#     def count(self) -> int:
#         """Return number of items"""
#         return len(self.items)
#
#     def selectedIndices(self) -> set[int]:
#         """Return set of selected indices"""
#         return self._selectedIndices.copy()
#
#     def selectedItems(self) -> list[ComboItem]:
#         """Return list of selected items"""
#         return [
#             self.items[i] for i in self._selectedIndices if 0 <= i < len(self.items)
#         ]
#
#     def selectedTexts(self) -> list[str]:
#         """Return list of selected texts"""
#         return [
#             self.items[i].text
#             for i in self._selectedIndices
#             if 0 <= i < len(self.items)
#         ]
#
#     def setSelectedIndices(self, indices: set[int]):
#         """Set selected indices"""
#         self._selectedIndices = {i for i in indices if 0 <= i < len(self.items)}
#         self._updateDisplay()
#         self.selectionChanged.emit(self._selectedIndices)
#         self.selectedTextChanged.emit(self.selectedTexts())
#
#     def setPlaceholderText(self, text: str):
#         """Set placeholder text"""
#         self._placeholderText = text
#         if not self._selectedIndices:
#             self._updateTextState(True)
#             self.setText(text)
#
#     def _updateDisplay(self):
#         """Update display based on mode and selection"""
#         if self._chipsMode:
#             self._updateDisplayChips()
#         else:
#             self._updateDisplayText()
#
#     def _updateTextState(self, isPlaceholder):
#         """Update placeholder text state for styling"""
#         if self.property("isPlaceholderText") == isPlaceholder:
#             return
#
#         self.setProperty("isPlaceholderText", isPlaceholder)
#         self.style().unpolish(self)
#         self.style().polish(self)
#         self.update()
#
#     def _updateDisplayText(self):
#         """Update display text based on selection (TEXT mode)"""
#         if not self._selectedIndices:
#             self._updateTextState(True)
#             self.setText(self._placeholderText or "")
#             return
#
#         self._updateTextState(False)
#         selected = self.selectedTexts()
#         self.setText(", ".join(selected))
#
#     def _updateDisplayChips(self):
#         """Update display with chips (CHIPS mode)"""
#         # Clear text in chips mode
#         self.setText("")
#
#         # Create chips container if not exists
#         if not hasattr(self, "_chipsScrollArea"):
#             self._setupChipsContainer()
#
#         # Clear existing chips
#         self._clearChips()
#
#         # Create chips for selected items
#         if not self._selectedIndices:
#             if self._placeholderText:
#                 self._updateTextState(True)
#                 self.setText(self._placeholderText)
#             self._chipsScrollArea.setVisible(False)
#             return
#
#         self._updateTextState(False)
#
#         for idx in sorted(self._selectedIndices):
#             if 0 <= idx < len(self.items):
#                 chip = SubClip(self.items[idx].text)
#                 chip.closed.connect(lambda text, i=idx: self._onChipClosed(i))
#                 self._chipsLayout.insertWidget(0, chip)
#
#         self._chipsScrollArea.setVisible(True)
#
#     def _setupChipsContainer(self):
#         """Setup the scroll area and container for chips"""
#         # Create scroll area with horizontal smooth scrolling
#         self._chipsScrollArea = SingleDirectionScrollArea(self, Qt.Horizontal)
#         self._chipsScrollArea.setWidgetResizable(True)
#         self._chipsScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self._chipsScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self._chipsScrollArea.setFrameShape(QScrollArea.NoFrame)
#         self._chipsScrollArea.setStyleSheet("background: transparent;")
#         self._chipsScrollArea.setFocusPolicy(Qt.NoFocus)
#
#         # Create container widget
#         self._chipsContainer = QWidget()
#         self._chipsContainer.setStyleSheet("background: transparent;")
#
#         # Create horizontal layout for chips
#         self._chipsLayout = QHBoxLayout(self._chipsContainer)
#         self._chipsLayout.setContentsMargins(10, 0, 40, 0)
#         self._chipsLayout.setSpacing(4)
#         self._chipsLayout.addStretch()
#
#         self._chipsScrollArea.setWidget(self._chipsContainer)
#         self._chipsScrollArea.setGeometry(self.rect())
#
#     def _clearChips(self):
#         """Clear all chips from container"""
#         if not hasattr(self, "_chipsLayout"):
#             return
#
#         # Remove all items except the stretch
#         while self._chipsLayout.count() > 1:
#             item = self._chipsLayout.takeAt(0)
#             if item.widget():
#                 item.widget().deleteLater()
#
#     def _onChipClosed(self, index: int):
#         """Handle chip close button click"""
#         if index in self._selectedIndices:
#             self._selectedIndices.discard(index)
#             self._updateDisplay()
#             self.selectionChanged.emit(self._selectedIndices)
#             self.selectedTextChanged.emit(self.selectedTexts())
#
#     def setMaxVisibleItems(self, num: int):
#         self._maxVisibleItems = num
#
#     def maxVisibleItems(self) -> int:
#         return self._maxVisibleItems
#
#     def _createComboMenu(self):
#         return MultiSelectionComboBoxMenu(self)
#
#     def _showComboMenu(self):
#         if not self.items:
#             return
#
#         menu = self._createComboMenu()
#
#         # create actions with checkable state
#         for i, item in enumerate(self.items):
#             action = QAction(item.icon, item.text)
#             action.setEnabled(item.isEnabled)
#             action.setCheckable(True)
#             action.setChecked(i in self._selectedIndices)
#             menu.addAction(action)
#
#             listItem = menu.view.item(i)
#             if listItem:
#                 checkState = Qt.Checked if i in self._selectedIndices else Qt.Unchecked
#                 listItem.setData(Qt.CheckStateRole, checkState)
#
#         # connect to handle selection changes
#         menu.view.itemClicked.connect(self._onItemClicked)
#
#         if menu.view.width() < self.width():
#             menu.view.setMinimumWidth(self.width())
#             menu.adjustSize()
#
#         menu.setMaxVisibleItems(self.maxVisibleItems())
#         menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
#         menu.closedSignal.connect(self._onDropMenuClosed)
#         self.dropMenu = menu
#
#         # determine animation type
#         x = (
#             -menu.width() // 2
#             + menu.layout().contentsMargins().left()
#             + self.width() // 2
#         )
#         pd = self.mapToGlobal(QPoint(x, self.height()))
#         hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)
#
#         pu = self.mapToGlobal(QPoint(x, 0))
#         hu = menu.view.heightForAnimation(pu, MenuAnimationType.PULL_UP)
#
#         if hd >= hu:
#             menu.view.adjustSize(pd, MenuAnimationType.DROP_DOWN)
#             menu.exec(pd, aniType=MenuAnimationType.DROP_DOWN)
#         else:
#             menu.view.adjustSize(pu, MenuAnimationType.PULL_UP)
#             menu.exec(pu, aniType=MenuAnimationType.PULL_UP)
#
#     def _toggleComboMenu(self):
#         if self.dropMenu:
#             self._closeComboMenu()
#         else:
#             self._showComboMenu()
#
#     def _closeComboMenu(self):
#         if not self.dropMenu:
#             return
#         try:
#             self.dropMenu.close()
#         except Exception:
#             pass
#         self.dropMenu = None
#
#     def _onDropMenuClosed(self):
#         if sys.platform != "win32":
#             self.dropMenu = None
#         else:
#             pos = self.mapFromGlobal(QCursor.pos())
#             if not self.rect().contains(pos):
#                 self.dropMenu = None
#
#     def _onItemClicked(self, item):
#         """Handle item click - toggle selection without closing menu"""
#         index = self._findItemByText(item.text())
#         if index < 0 or not self.items[index].isEnabled:
#             return
#
#         if index in self._selectedIndices:
#             self._selectedIndices.discard(index)
#         else:
#             self._selectedIndices.add(index)
#
#         self._updateDisplay()
#         self.selectionChanged.emit(self._selectedIndices)
#         self.selectedTextChanged.emit(self.selectedTexts())
#
#     def _findItemByText(self, text: str) -> int:
#         """Find item index by text"""
#         for i, item in enumerate(self.items):
#             if item.text == text:
#                 return i
#         return -1
#
#     def mouseReleaseEvent(self, e):
#         super().mouseReleaseEvent(e)
#         self._toggleComboMenu()
#
#     def resizeEvent(self, e):
#         super().resizeEvent(e)
#         if hasattr(self, "_chipsScrollArea"):
#             self._chipsScrollArea.setGeometry(0, 0, self.width() - 36, self.height())
#
#     def paintEvent(self, e):
#         QPushButton.paintEvent(self, e)
#         painter = QPainter(self)
#         painter.setRenderHints(QPainter.Antialiasing)
#         if self.isHover:
#             painter.setOpacity(0.8)
#         elif self.isPressed:
#             painter.setOpacity(0.7)
#
#         rect = QRectF(
#             self.width() - 22, self.height() / 2 - 5 + self.arrowAni.y, 10, 10
#         )
#         if isDarkTheme():
#             FIF.ARROW_DOWN.render(painter, rect)
#         else:
#             FIF.ARROW_DOWN.render(painter, rect, fill="#646464")



class MultiSelectionComboBox(QPushButton, ComboBoxBase):
    """Multi-select combo box with check boxes"""

    selectionChanged = Signal(set)
    selectedTextChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.arrowAni = TranslateYAnimation(self)
        self._setUpUi()
        setFont(self)

    def _setUpUi(self):
        self.isHover = False
        self.isPressed = False
        self.items: list[ComboItem] = []
        self._selectedIndices: set[int] = set()
        self._placeholderText = ""
        self._maxVisibleItems = -1
        self.dropMenu = None
        self._chipsMode = False

        # FluentStyleSheet.COMBO_BOX.apply(self)
        StyleSheet.COMBO_BOX.apply(self)
        self.installEventFilter(self)

    def setChipsMode(self, enabled: bool = True):
        """Set whether to use chips display mode"""
        self._chipsMode = enabled
        self._updateDisplay()

    def isChipsMode(self) -> bool:
        """Return whether chips mode is enabled"""
        return self._chipsMode

    def eventFilter(self, obj, e: QEvent):
        if obj is self:
            if e.type() == QEvent.MouseButtonPress:
                self.isPressed = True
            elif e.type() == QEvent.MouseButtonRelease:
                self.isPressed = False
            elif e.type() == QEvent.Enter:
                self.isHover = True
            elif e.type() == QEvent.Leave:
                self.isHover = False
        return super().eventFilter(obj, e)

    def addItem(
        self, text: str, icon: Union[str, QIcon, FluentIconBase] = None, userData=None
    ):
        """Add an item"""
        item = ComboItem(text, icon, userData)
        self.items.append(item)

    def addItems(self, texts: Iterable[str]):
        """Add multiple items"""
        for text in texts:
            self.addItem(text)

    def removeItem(self, index: int):
        """Remove item at index"""
        if not 0 <= index < len(self.items):
            return
        self.items.pop(index)
        # update selected indices
        newSelected = set()
        for i in self._selectedIndices:
            if i < index:
                newSelected.add(i)
            elif i > index:
                newSelected.add(i - 1)
        self._selectedIndices = newSelected
        self._updateDisplay()

    def clear(self):
        """Clear all items"""
        self.items.clear()
        self._selectedIndices.clear()
        self.setText("")
        self._currentIndex = -1

    def count(self) -> int:
        """Return number of items"""
        return len(self.items)

    def selectedIndices(self) -> set[int]:
        """Return set of selected indices"""
        return self._selectedIndices.copy()

    def selectedItems(self) -> list[ComboItem]:
        """Return list of selected items"""
        return [
            self.items[i] for i in self._selectedIndices if 0 <= i < len(self.items)
        ]

    def selectedTexts(self) -> list[str]:
        """Return list of selected texts"""
        return [
            self.items[i].text
            for i in self._selectedIndices
            if 0 <= i < len(self.items)
        ]

    def setSelectedIndices(self, indices: set[int]):
        """Set selected indices"""
        self._selectedIndices = {i for i in indices if 0 <= i < len(self.items)}
        self._updateDisplay()
        self.selectionChanged.emit(self._selectedIndices)
        self.selectedTextChanged.emit(self.selectedTexts())

    def setPlaceholderText(self, text: str):
        """Set placeholder text"""
        self._placeholderText = text
        if not self._selectedIndices:
            self._updateTextState(True)
            self.setText(text)

    def _updateDisplay(self):
        """Update display based on mode and selection"""
        if self._chipsMode:
            self._updateDisplayChips()
        else:
            self._updateDisplayText()

    def _updateTextState(self, isPlaceholder):
        """Update placeholder text state for styling"""
        if self.property("isPlaceholderText") == isPlaceholder:
            return

        self.setProperty("isPlaceholderText", isPlaceholder)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _updateDisplayText(self):
        """Update display text based on selection (TEXT mode)"""
        if not self._selectedIndices:
            self._updateTextState(True)
            self.setText(self._placeholderText or "")
            return

        self._updateTextState(False)
        selected = self.selectedTexts()
        self.setText(", ".join(selected))

    def _updateDisplayChips(self):
        """Update display with chips (CHIPS mode)"""
        # Clear text in chips mode
        self.setText("")

        # Create chips container if not exists
        if not hasattr(self, "_chipsScrollArea"):
            self._setupChipsContainer()

        # Clear existing chips
        self._clearChips()

        # Create chips for selected items
        if not self._selectedIndices:
            if self._placeholderText:
                self._updateTextState(True)
                self.setText(self._placeholderText)
            self._chipsScrollArea.setVisible(False)
            return

        self._updateTextState(False)

        for idx in sorted(self._selectedIndices):
            if 0 <= idx < len(self.items):
                chip = SubClip(self.items[idx].text)
                chip.closed.connect(lambda text, i=idx: self._onChipClosed(i))
                self._chipsLayout.insertWidget(0, chip)

        self._chipsScrollArea.setVisible(True)

    def _setupChipsContainer(self):
        """Setup the scroll area and container for chips"""
        # Create scroll area with horizontal smooth scrolling
        self._chipsScrollArea = SingleDirectionScrollArea(self, Qt.Horizontal)
        self._chipsScrollArea.setWidgetResizable(True)
        self._chipsScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chipsScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chipsScrollArea.setFrameShape(QScrollArea.NoFrame)
        self._chipsScrollArea.setStyleSheet("background: transparent;")
        self._chipsScrollArea.setFocusPolicy(Qt.NoFocus)

        # Create container widget
        self._chipsContainer = QWidget()
        self._chipsContainer.setStyleSheet("background: transparent;")

        # Create horizontal layout for chips
        self._chipsLayout = QHBoxLayout(self._chipsContainer)
        self._chipsLayout.setContentsMargins(10, 0, 40, 0)
        self._chipsLayout.setSpacing(4)
        self._chipsLayout.addStretch()

        self._chipsScrollArea.setWidget(self._chipsContainer)
        self._chipsScrollArea.setGeometry(self.rect())

    def _clearChips(self):
        """Clear all chips from container"""
        if not hasattr(self, "_chipsLayout"):
            return

        # Remove all items except the stretch
        while self._chipsLayout.count() > 1:
            item = self._chipsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _onChipClosed(self, index: int):
        """Handle chip close button click"""
        if index in self._selectedIndices:
            self._selectedIndices.discard(index)
            self._updateDisplay()
            self.selectionChanged.emit(self._selectedIndices)
            self.selectedTextChanged.emit(self.selectedTexts())

    def setMaxVisibleItems(self, num: int):
        self._maxVisibleItems = num

    def maxVisibleItems(self) -> int:
        return self._maxVisibleItems

    def _createComboMenu(self):
        return MultiSelectionComboBoxMenu(self)

    def _showComboMenu(self):
        if not self.items:
            return

        menu = self._createComboMenu()

        # create actions with checkable state
        for i, item in enumerate(self.items):
            action = QAction(item.icon, item.text)
            action.setEnabled(item.isEnabled)
            action.setCheckable(True)
            action.setChecked(i in self._selectedIndices)
            menu.addAction(action)

            listItem = menu.view.item(i)
            if listItem:
                checkState = Qt.Checked if i in self._selectedIndices else Qt.Unchecked
                listItem.setData(Qt.CheckStateRole, checkState)

        # connect to handle selection changes
        menu.view.itemClicked.connect(self._onItemClicked)

        if menu.view.width() < self.width():
            menu.view.setMinimumWidth(self.width())
            menu.adjustSize()

        menu.setMaxVisibleItems(self.maxVisibleItems())
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        menu.closedSignal.connect(self._onDropMenuClosed)
        self.dropMenu = menu

        # determine animation type
        x = (
            -menu.width() // 2
            + menu.layout().contentsMargins().left()
            + self.width() // 2
        )
        pd = self.mapToGlobal(QPoint(x, self.height()))
        hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)

        pu = self.mapToGlobal(QPoint(x, 0))
        hu = menu.view.heightForAnimation(pu, MenuAnimationType.PULL_UP)

        if hd >= hu:
            menu.view.adjustSize(pd, MenuAnimationType.DROP_DOWN)
            menu.exec(pd, aniType=MenuAnimationType.DROP_DOWN)
        else:
            menu.view.adjustSize(pu, MenuAnimationType.PULL_UP)
            menu.exec(pu, aniType=MenuAnimationType.PULL_UP)

    def _toggleComboMenu(self):
        if self.dropMenu:
            self._closeComboMenu()
        else:
            self._showComboMenu()

    def _closeComboMenu(self):
        if not self.dropMenu:
            return
        try:
            self.dropMenu.close()
        except Exception:
            pass
        self.dropMenu = None

    def _onDropMenuClosed(self):
        if sys.platform != "win32":
            self.dropMenu = None
        else:
            pos = self.mapFromGlobal(QCursor.pos())
            if not self.rect().contains(pos):
                self.dropMenu = None

    def _onItemClicked(self, item):
        """Handle item click - toggle selection without closing menu"""
        index = self._findItemByText(item.text())
        if index < 0 or not self.items[index].isEnabled:
            return

        if index in self._selectedIndices:
            self._selectedIndices.discard(index)
        else:
            self._selectedIndices.add(index)

        self._updateDisplay()
        self.selectionChanged.emit(self._selectedIndices)
        self.selectedTextChanged.emit(self.selectedTexts())

    def _findItemByText(self, text: str) -> int:
        """Find item index by text"""
        for i, item in enumerate(self.items):
            if item.text == text:
                return i
        return -1

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._toggleComboMenu()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_chipsScrollArea"):
            self._chipsScrollArea.setGeometry(0, 0, self.width() - 36, self.height())

    def paintEvent(self, e):
        QPushButton.paintEvent(self, e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isHover:
            painter.setOpacity(0.8)
        elif self.isPressed:
            painter.setOpacity(0.7)

        rect = QRectF(
            self.width() - 22, self.height() / 2 - 5 + self.arrowAni.y, 10, 10
        )
        if isDarkTheme():
            FIF.ARROW_DOWN.render(painter, rect)
        else:
            FIF.ARROW_DOWN.render(painter, rect, fill="#646464")


