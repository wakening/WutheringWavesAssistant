from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QWidget
from qfluentwidgets import SmoothScrollArea, TransparentToolButton, PillPushButton
from qfluentwidgets.common.icon import FluentIcon as FIF

from .button import OutlinedPushButton


# from ...common.icon import FluentIcon as FIF
# from .button import OutlinedPushButton, PillPushButton, TransparentToolButton
# from .scroll_area import SmoothScrollArea


class ExclusiveLiteFilterBase(QWidget):
    """Base class for exclusive lite filter widgets"""

    currentTextChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = {}
        self._currentText: str = None

        # Create layout
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)

        # Create scroll area
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setFixedHeight(36)
        self.scrollArea.setStyleSheet(
            "QScrollArea{border: none; background: transparent;}"
        )

        # Container for items
        self.container = QWidget(self.scrollArea)
        self.container.setStyleSheet("QWidget{background: transparent;}")
        self.itemsLayout = QHBoxLayout(self.container)
        self.itemsLayout.setContentsMargins(0, 0, 0, 0)
        self.itemsLayout.setSpacing(8)
        self.itemsLayout.setAlignment(Qt.AlignLeft)
        self.itemsLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.scrollArea.setWidget(self.container)

        # Connect scroll bar value change to update arrow visibility
        self.scrollArea.horizontalScrollBar().valueChanged.connect(
            self._updateArrowVisibility
        )
        # 滚动范围变化时也要更新箭头（修复首次显示时布局未 settle 导致箭头误现）
        self.scrollArea.horizontalScrollBar().rangeChanged.connect(
            lambda: self._updateArrowVisibility()
        )

        # Right arrow button
        self.rightArrowBtn = TransparentToolButton(FIF.CARE_RIGHT_SOLID, self)
        self.rightArrowBtn.setFixedSize(24, 24)
        self.rightArrowBtn.setIconSize(QSize(12, 12))
        self.rightArrowBtn.clicked.connect(self._scrollRight)

        # Spacer to maintain spacing when arrow is hidden
        self.spacer = QWidget(self)
        self.spacer.setFixedSize(24, 24)
        self.spacer.setVisible(False)

        # Add to layout
        self.hBoxLayout.addWidget(self.scrollArea, 1)
        self.hBoxLayout.addWidget(self.rightArrowBtn, 0)
        self.hBoxLayout.addWidget(self.spacer, 0)

        # Size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(36)

    def _createButton(self, text: str):
        """Create button for item. Override in subclasses."""
        raise NotImplementedError

    def addItem(self, text: str):
        """Add an item to the filter

        Parameters
        ----------
        text : str
            The text to display for this filter item.

        Returns
        -------
        QPushButton
            The created button widget.
        """
        if text in self._items:
            return self._items[text]

        button = self._createButton(text)
        button.setCheckable(True)
        button.clicked.connect(lambda checked, t=text: self._onItemClicked(t))

        self._items[text] = button
        self.itemsLayout.addWidget(button)

        # Select first item by default
        if self._currentText is None:
            self.setCurrentItem(text)

        return button

    def addItems(self, texts: list[str]):
        """Add multiple items to the filter

        Parameters
        ----------
        texts : List[str]
            List of texts to add as filter items.
        """
        for text in texts:
            self.addItem(text)

    def currentItem(self) -> str:
        """Get the currently selected item text

        Returns
        -------
        str
            The text of the currently selected item, or None if no selection.
        """
        return self._currentText

    def setCurrentItem(self, text: str):
        """Set the currently selected item

        Parameters
        ----------
        text : str
            The text of the item to select. If the item doesn't exist, nothing happens.
        """
        if text not in self._items:
            return

        # Deselect all
        for itemText, button in self._items.items():
            button.setChecked(itemText == text)

        oldText = self._currentText
        self._currentText = text

        if oldText != text:
            self.currentTextChanged.emit(text)

    def clear(self):
        """Clear all items from the filter"""
        for button in self._items.values():
            button.deleteLater()

        self._items.clear()
        self._currentText = None

    def items(self) -> list[str]:
        """Get all item texts

        Returns
        -------
        List[str]
            List of all item texts in order.
        """
        return list(self._items.keys())

    def _onItemClicked(self, text: str):
        """Handle item click"""
        self.setCurrentItem(text)

    def _scrollRight(self):
        """Scroll the filter area to the right"""
        scrollBar = self.scrollArea.horizontalScrollBar()
        scrollBar.setValue(scrollBar.value() + 100)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._updateArrowVisibility()

    def _updateArrowVisibility(self):
        """Show/hide arrow based on scroll position"""
        scrollBar = self.scrollArea.horizontalScrollBar()
        maxScroll = scrollBar.maximum()
        currentScroll = scrollBar.value()
        visible = currentScroll < maxScroll
        self.rightArrowBtn.setVisible(visible)
        self.spacer.setVisible(not visible)

    def wheelEvent(self, e):
        """Handle wheel event for horizontal scrolling"""
        delta = e.angleDelta().y()
        if delta != 0:
            self.scrollArea.delegate.hScrollBar.scrollValue(-delta)
        e.accept()


class ExclusiveLiteFilter(ExclusiveLiteFilterBase):
    """Exclusive lite filter with PillPushButton items

    A horizontally scrollable filter component that provides exclusive (single) selection.
    Items are displayed as PillPushButton, and only one can be selected at a time.

    Signals
    -------
    currentTextChanged : Signal(str)
        Emitted when the selected item changes, passing the text of the new selection.

    Examples
    --------
    Basic usage:

    filter = ExclusiveLiteFilter()
    filter.addItems(["All", "Active", "Completed", "Pending"])
    filter.currentTextChanged.connect(lambda text: print(f"Selected: {text}"))
    """

    def _createButton(self, text: str):
        return PillPushButton(text, self.container)


class OutlinedExclusiveLiteFilter(ExclusiveLiteFilterBase):
    """Exclusive lite filter with OutlinedPushButton items

    A horizontally scrollable filter component that provides exclusive (single) selection.
    Items are displayed as OutlinedPushButton, and only one can be selected at a time.

    Signals
    -------
    currentTextChanged : Signal(str)
        Emitted when the selected item changes, passing the text of the new selection.

    Examples
    --------
    Basic usage:

    filter = OutlinedExclusiveLiteFilter()
    filter.addItems(["All", "Active", "Completed", "Pending"])
    filter.currentTextChanged.connect(lambda text: print(f"Selected: {text}"))
    """

    def _createButton(self, text: str):
        return OutlinedPushButton(text, self.container)


class MultiSelectionLiteFilterBase(QWidget):
    """Base class for multi-selection lite filter widgets"""

    currentItemsChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = {}
        self._selectedItems: list[str] = []

        # Create layout
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)

        # Create scroll area
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setFixedHeight(36)
        self.scrollArea.setStyleSheet(
            "QScrollArea{border: none; background: transparent;}"
        )

        # Container for items
        self.container = QWidget(self.scrollArea)
        self.container.setStyleSheet("QWidget{background: transparent;}")
        self.itemsLayout = QHBoxLayout(self.container)
        self.itemsLayout.setContentsMargins(0, 0, 0, 0)
        self.itemsLayout.setSpacing(8)
        self.itemsLayout.setAlignment(Qt.AlignLeft)
        self.itemsLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.scrollArea.setWidget(self.container)

        # Connect scroll bar value change to update arrow visibility
        self.scrollArea.horizontalScrollBar().valueChanged.connect(
            self._updateArrowVisibility
        )
        # 滚动范围变化时也要更新箭头（修复首次显示时布局未 settle 导致箭头误现）
        self.scrollArea.horizontalScrollBar().rangeChanged.connect(
            lambda: self._updateArrowVisibility()
        )

        # Right arrow button
        self.rightArrowBtn = TransparentToolButton(FIF.CARE_RIGHT_SOLID, self)
        self.rightArrowBtn.setFixedSize(24, 24)
        self.rightArrowBtn.setIconSize(QSize(12, 12))
        self.rightArrowBtn.clicked.connect(self._scrollRight)

        # Spacer to maintain spacing when arrow is hidden
        self.spacer = QWidget(self)
        self.spacer.setFixedSize(24, 24)
        self.spacer.setVisible(False)

        # Add to layout
        self.hBoxLayout.addWidget(self.scrollArea, 1)
        self.hBoxLayout.addWidget(self.rightArrowBtn, 0)
        self.hBoxLayout.addWidget(self.spacer, 0)

        # Size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(36)

    def _createButton(self, text: str):
        """Create button for item. Override in subclasses."""
        raise NotImplementedError

    def addItem(self, text: str):
        """Add an item to the filter

        Parameters
        ----------
        text : str
            The text to display for this filter item.

        Returns
        -------
        QPushButton
            The created button widget.
        """
        if text in self._items:
            return self._items[text]

        button = self._createButton(text)
        button.setCheckable(True)
        button.clicked.connect(lambda checked, t=text: self._onItemClicked(t))

        self._items[text] = button
        self.itemsLayout.addWidget(button)

        return button

    def addItems(self, texts: list[str]):
        """Add multiple items to the filter

        Parameters
        ----------
        texts : List[str]
            List of texts to add as filter items.
        """
        for text in texts:
            self.addItem(text)

    def currentItems(self) -> list[str]:
        """Get the currently selected items

        Returns
        -------
        List[str]
            List of currently selected item texts.
        """
        return self._selectedItems.copy()

    def setCurrentItems(self, texts: list[str]):
        """Set the currently selected items

        Parameters
        ----------
        texts : List[str]
            List of texts to select. Items that don't exist are ignored.
        """
        oldItems = self._selectedItems.copy()
        self._selectedItems.clear()

        for itemText, button in self._items.items():
            if itemText in texts:
                button.setChecked(True)
                self._selectedItems.append(itemText)
            else:
                button.setChecked(False)

        if set(oldItems) != set(self._selectedItems):
            self.currentItemsChanged.emit(self._selectedItems)

    def clearSelection(self):
        """Clear all selections"""
        for button in self._items.values():
            button.setChecked(False)
        self._selectedItems.clear()
        self.currentItemsChanged.emit([])

    def clear(self):
        """Clear all items from the filter"""
        for button in self._items.values():
            button.deleteLater()

        self._items.clear()
        self._selectedItems.clear()

    def items(self) -> list[str]:
        """Get all item texts

        Returns
        -------
        List[str]
            List of all item texts in order.
        """
        return list(self._items.keys())

    def _onItemClicked(self, text: str):
        """Handle item click - toggle selection"""
        button = self._items[text]
        if button.isChecked():
            if text not in self._selectedItems:
                self._selectedItems.append(text)
        else:
            if text in self._selectedItems:
                self._selectedItems.remove(text)
        self.currentItemsChanged.emit(self._selectedItems)

    def _scrollRight(self):
        """Scroll the filter area to the right"""
        scrollBar = self.scrollArea.horizontalScrollBar()
        scrollBar.setValue(scrollBar.value() + 100)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._updateArrowVisibility()

    def _updateArrowVisibility(self):
        """Show/hide arrow based on scroll position"""
        scrollBar = self.scrollArea.horizontalScrollBar()
        maxScroll = scrollBar.maximum()
        currentScroll = scrollBar.value()
        visible = currentScroll < maxScroll
        self.rightArrowBtn.setVisible(visible)
        self.spacer.setVisible(not visible)

    def wheelEvent(self, e):
        """Handle wheel event for horizontal scrolling"""
        delta = e.angleDelta().y()
        if delta != 0:
            self.scrollArea.delegate.hScrollBar.scrollValue(-delta)
        e.accept()


class MultiSelectionLiteFilter(MultiSelectionLiteFilterBase):
    """Multi-selection lite filter with PillPushButton items

    A horizontally scrollable filter component that provides multi-selection.
    Items are displayed as PillPushButton, and multiple can be selected at once.

    Signals
    -------
    currentItemsChanged : Signal(list)
        Emitted when the selection changes, passing the list of selected items.

    Examples
    --------
    Basic usage:

    filter = MultiSelectionLiteFilter()
    filter.addItems(["Active", "Completed", "Pending", "Archived"])
    filter.currentItemsChanged.connect(lambda items: print(f"Selected: {items}"))
    """

    def _createButton(self, text: str):
        return PillPushButton(text, self.container)


class OutlinedMultiSelectionLiteFilter(MultiSelectionLiteFilterBase):
    """Multi-selection lite filter with OutlinedPushButton items

    A horizontally scrollable filter component that provides multi-selection.
    Items are displayed as OutlinedPushButton, and multiple can be selected at once.

    Signals
    -------
    currentItemsChanged : Signal(list)
        Emitted when the selection changes, passing the list of selected items.

    Examples
    --------
    Basic usage:

    filter = OutlinedMultiSelectionLiteFilter()
    filter.addItems(["Active", "Completed", "Pending", "Archived"])
    filter.currentItemsChanged.connect(lambda items: print(f"Selected: {items}"))
    """

    def _createButton(self, text: str):
        return OutlinedPushButton(text, self.container)
