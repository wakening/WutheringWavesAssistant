"""Hierarchical single and multiple selection combo boxes."""
from __future__ import annotations

from typing import Iterable
import re

from PySide6.QtCore import (
    QAbstractItemModel, QEasingCurve, QEvent, QIdentityProxyModel, QModelIndex, QPoint, QPointF,
    QParallelAnimationGroup, QPersistentModelIndex, QPropertyAnimation, QRect, QRectF, Qt, Signal,
)
from PySide6.QtGui import QColor, QFontMetrics, QIcon, QPainter, QPalette, QStandardItem, QStandardItemModel, QTextLayout, QTextOption
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QStyle,
    QStyleOptionViewItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QWidget,
)
from qfluentwidgets import (
    TreeItemDelegate,
    TreeView,
    FluentStyleSheet,
    setFont,
    SearchLineEdit,
    BodyLabel,
    isDarkTheme,
    FluentIcon as FIF,
)


# from ...common.font import setFont
# from ...common.icon import FluentIcon as FIF, isDarkTheme
# from ...common.style_sheet import FluentStyleSheet
from .button import SubClip
# from .tree_view import TreeView, TreeItemDelegate
# from .line_edit import SearchLineEdit
# from .label import BodyLabel


class _SearchTreeDelegate(TreeItemDelegate):
    """Keep the existing tree style; decorate literal matches without HTML."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.text = ""

    def paint(self, painter, option, index):
        query = self.parent().property("treeSearchText") or ""
        super().paint(painter, option, index)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        # Keep the QSS padding and checkbox spacing, but paint the text ourselves.
        # Avoid re-entering QStyleSheetStyle during a Python paint callback;
        # the native delegate still draws the row, icon and checkbox normally.
        offset = 66 if index.data(Qt.ItemDataRole.CheckStateRole) is not None else 20
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(icon, QIcon) and not icon.isNull():
            offset += 24
        textRect = QStyle.visualRect(opt.direction, opt.rect, opt.rect.adjusted(offset, 0, -8, 0))
        displayed = QFontMetrics(opt.font).elidedText(str(index.data() or ""), Qt.TextElideMode.ElideRight, textRect.width())
        painter.save()
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        painter.setPen(opt.palette.color(QPalette.ColorRole.Text))
        if not index.flags() & Qt.ItemFlag.ItemIsEnabled:
            painter.setOpacity(0.36)
        layout = QTextLayout(displayed, opt.font)
        textOption = QTextOption()
        textOption.setTextDirection(opt.direction)
        textOption.setAlignment(Qt.AlignmentFlag.AlignLeading)
        layout.setTextOption(textOption)
        formats = []
        for match in re.finditer(re.escape(query), displayed, re.IGNORECASE) if query else ():
            formatRange = QTextLayout.FormatRange()
            formatRange.start = len(displayed[:match.start()].encode("utf-16-le")) // 2
            formatRange.length = len(match.group().encode("utf-16-le")) // 2
            formatRange.format.setBackground(QColor(255, 207, 64, 100))
            formats.append(formatRange)
        layout.setFormats(formats)
        layout.beginLayout()
        line = layout.createLine()
        if line.isValid():
            line.setLineWidth(textRect.width())
        layout.endLayout()
        if line.isValid():
            layout.draw(painter, QPointF(textRect.x(), textRect.y() + (textRect.height() - line.height()) / 2))
        painter.restore()


def _pathText(index: QModelIndex) -> str:
    parts = []
    while index.isValid():
        parts.append(str(index.data(Qt.ItemDataRole.DisplayRole) or ""))
        index = index.parent()
    return "/".join(reversed(parts))


class _LeafOnlyModel(QIdentityProxyModel):
    """Keep parent nodes expandable, but never selectable or checkable."""

    def flags(self, index: QModelIndex):
        flags = super().flags(index)
        if index.isValid() and self.hasChildren(index):
            flags &= ~Qt.ItemFlag.ItemIsSelectable
            flags &= ~Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.CheckStateRole and index.isValid() and self.hasChildren(index):
            return None
        return super().data(index, role)

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.CheckStateRole and index.isValid() and self.hasChildren(index):
            return False
        return super().setData(index, value, role)


class _MultiLeafModel(_LeafOnlyModel):
    """Expose parent checkboxes as bulk actions without selecting parents."""

    def flags(self, index: QModelIndex):
        flags = super().flags(index)
        if index.isValid() and self.hasChildren(index):
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.CheckStateRole and index.isValid() and self.hasChildren(index):
            leaves = self.parent()._leafDescendants(self.mapToSource(index))
            selected = set(self.parent().selectedIndexes())
            checkedCount = sum(leaf in selected for leaf in leaves)
            if checkedCount == 0:
                return Qt.CheckState.Unchecked
            if checkedCount == len(leaves):
                return Qt.CheckState.Checked
            return Qt.CheckState.PartiallyChecked
        return super().data(index, role)

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.CheckStateRole and index.isValid() and self.hasChildren(index):
            return False  # Parent checkboxes are handled by the view's click/keyboard events.
        return super().setData(index, value, role)


class TreeComboBox(QPushButton):
    """A combo box backed by a hierarchical QAbstractItemModel.

    The default model is a QStandardItemModel. ``addItem`` accepts a parent
    QModelIndex to create nested entries. Existing models can be supplied with
    ``setModel``; the first column's DisplayRole is shown in the button.
    """

    currentModelIndexChanged = Signal(QModelIndex)
    currentTextChanged = Signal(str)
    activated = Signal(QModelIndex)
    searchTextChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model: QAbstractItemModel | None = None
        self._viewModel = self._createViewModel()
        self._current = QPersistentModelIndex()
        self._hadCurrent = False
        self._lastText = ""
        self._placeholderText = ""
        self._maxVisibleItems = -1
        self._popup: QFrame | None = None
        self._popupAnimation: QParallelAnimationGroup | None = None
        self._tree: TreeView | None = None
        self._branchPress = False
        self._searchEnabled = True
        self._searchText = ""
        self._search = None
        self._emptySearch = None
        self._filtering = False
        self._expandedBeforeSearch = []
        self._currentBeforeSearch = QPersistentModelIndex()

        FluentStyleSheet.COMBO_BOX.apply(self)
        setFont(self)
        self.setMinimumWidth(220)
        self.setModel(QStandardItemModel(self))
        self.clicked.connect(self._togglePopup)

    def _createViewModel(self):
        return _LeafOnlyModel(self)

    def setModel(self, model: QAbstractItemModel):
        if model is None:
            raise ValueError("model must be a QAbstractItemModel")
        if model is self._model:
            return

        if self._model is not None:
            for signal, slot in (
                (self._model.dataChanged, self._onModelDataChanged),
                (self._model.rowsRemoved, self._onRowsRemoved),
                (self._model.rowsInserted, self._onRowsInserted),
                (self._model.rowsMoved, self._refreshDisplay),
                (self._model.modelReset, self._onModelReset),
                (self._model.layoutChanged, self._refreshDisplay),
            ):
                signal.disconnect(slot)

        self.hidePopup()
        self._filtering = False
        self._expandedBeforeSearch = []
        self._currentBeforeSearch = QPersistentModelIndex()
        self._model = model
        self._viewModel.setSourceModel(model)
        self._current = QPersistentModelIndex()
        self._hadCurrent = False
        model.dataChanged.connect(self._onModelDataChanged)
        model.rowsRemoved.connect(self._onRowsRemoved)
        model.rowsInserted.connect(self._onRowsInserted)
        model.rowsMoved.connect(self._refreshDisplay)
        model.modelReset.connect(self._onModelReset)
        model.layoutChanged.connect(self._refreshDisplay)
        if self._tree is not None:
            self._tree.setModel(self._viewModel)
        self._refreshDisplay()

    def model(self) -> QAbstractItemModel:
        return self._model

    def addItem(self, text: str, parent: QModelIndex = QModelIndex(), userData=None,
                icon: QIcon | None = None) -> QModelIndex:
        """Append an item to the default model, optionally below ``parent``."""
        if not isinstance(self._model, QStandardItemModel):
            raise TypeError("addItem requires a QStandardItemModel")
        if parent.isValid() and (parent.model() is not self._model or parent.column() != 0):
            raise ValueError("parent index must be in column 0 of this model")

        item = QStandardItem(text)
        item.setEditable(False)
        if userData is not None:
            item.setData(userData, Qt.ItemDataRole.UserRole)
        if icon is not None:
            item.setIcon(icon)
        parentItem = self._model.itemFromIndex(parent) if parent.isValid() else self._model.invisibleRootItem()
        parentItem.appendRow(item)
        return item.index()

    def addItems(self, texts: Iterable[str], parent: QModelIndex = QModelIndex()):
        return [self.addItem(text, parent) for text in texts]

    def clear(self):
        if not isinstance(self._model, QStandardItemModel):
            raise TypeError("clear requires a QStandardItemModel")
        self._model.clear()

    def setPlaceholderText(self, text: str):
        self._placeholderText = text
        self._refreshDisplay()

    def placeholderText(self) -> str:
        return self._placeholderText

    def setMaxVisibleItems(self, count: int):
        self._maxVisibleItems = max(1, count) if count >= 0 else -1

    def maxVisibleItems(self) -> int:
        return self._maxVisibleItems

    def setSearchEnabled(self, enabled: bool):
        if self._searchEnabled == bool(enabled):
            return
        self.hidePopup()
        self._searchEnabled = bool(enabled)
        if not enabled:
            self.setSearchText("")
        if self._search is not None:
            self._search.setVisible(bool(enabled))
        self._applySearch()

    def isSearchEnabled(self) -> bool:
        return self._searchEnabled

    def setSearchText(self, text: str):
        if self._searchText == text:
            return
        self._searchText = text
        if self._search is not None and self._search.text() != text:
            self._search.setText(text)
        self._applySearch()
        self.searchTextChanged.emit(text)

    def searchText(self) -> str:
        return self._searchText

    def searchLineEdit(self):
        return self._search

    def _applySearch(self):
        if self._tree is None or self._emptySearch is None:
            return
        query = self._searchText.strip() if self._searchEnabled else ""
        wasFiltering = self._filtering
        if not wasFiltering and query:
            self._currentBeforeSearch = QPersistentModelIndex(self._tree.currentIndex())
            self._expandedBeforeSearch = []
            def save(parent=QModelIndex()):
                for row in range(self._viewModel.rowCount(parent)):
                    index = self._viewModel.index(row, 0, parent)
                    if self._tree.isExpanded(index):
                        self._expandedBeforeSearch.append(QPersistentModelIndex(index))
                    save(index)
            save()
        self._filtering = bool(query)
        self._tree.setProperty("treeSearchText", query)
        def filterRows(parent=QModelIndex(), ancestorMatches=False):
            anyVisible = False
            for row in range(self._viewModel.rowCount(parent)):
                index = self._viewModel.index(row, 0, parent)
                matches = ancestorMatches or not query or query.casefold() in str(index.data() or "").casefold()
                childMatches = filterRows(index, matches)
                visible = matches or childMatches
                self._tree.setRowHidden(row, parent, not visible)
                if query and visible and self._viewModel.hasChildren(index):
                    self._tree.expand(index)
                anyVisible |= visible
            return anyVisible
        anyVisible = filterRows()
        if wasFiltering and not query:
            if self.currentModelIndex().isValid():
                self._tree.setCurrentIndex(self._viewModel.mapFromSource(self.currentModelIndex()))
            elif self._currentBeforeSearch.isValid():
                self._tree.setCurrentIndex(QModelIndex(self._currentBeforeSearch))
            self._currentBeforeSearch = QPersistentModelIndex()
            self._tree.collapseAll()
            for index in self._expandedBeforeSearch:
                if index.isValid():
                    self._tree.expand(QModelIndex(index))
            self._expandedBeforeSearch = []
        self._emptySearch.setVisible(not anyVisible)
        self._tree.setVisible(anyVisible)
        index = self._tree.currentIndex()
        visible = index.isValid()
        while index.isValid():
            visible &= not self._tree.isRowHidden(index.row(), index.parent())
            index = index.parent()
        if not visible:
            first = QModelIndex()
            for row in range(self._viewModel.rowCount()):
                if not self._tree.isRowHidden(row, QModelIndex()):
                    first = self._viewModel.index(row, 0)
                    break
            self._tree.setCurrentIndex(first)
        self._tree.viewport().update()

    def currentModelIndex(self) -> QModelIndex:
        return QModelIndex(self._current) if self._current.isValid() else QModelIndex()

    def setCurrentModelIndex(self, index: QModelIndex):
        if index.isValid() and (index.model() is not self._model or index.column() != 0):
            raise ValueError("index must be in column 0 of this combo box's model")
        if index.isValid() and self._model.hasChildren(index):
            raise ValueError("only leaf nodes can be selected")
        if index == self.currentModelIndex():
            return
        oldText = self.currentText()
        self._current = QPersistentModelIndex(index)
        self._hadCurrent = index.isValid()
        self._refreshDisplay()
        self.currentModelIndexChanged.emit(self.currentModelIndex())
        if oldText != self.currentText():
            self.currentTextChanged.emit(self.currentText())

    def currentText(self) -> str:
        return _pathText(self.currentModelIndex())

    def currentData(self, role: int = Qt.ItemDataRole.UserRole):
        return self.currentModelIndex().data(role)

    def _onModelReset(self):
        hadCurrent = self._hadCurrent
        self._current = QPersistentModelIndex()
        self._hadCurrent = False
        self._refreshDisplay()
        if hadCurrent:
            self.currentModelIndexChanged.emit(QModelIndex())
            self.currentTextChanged.emit("")

    def _onRowsRemoved(self, *_):
        if self._hadCurrent and not self._current.isValid():
            self._hadCurrent = False
            self.currentModelIndexChanged.emit(QModelIndex())
            self.currentTextChanged.emit("")
        self._refreshDisplay()

    def _onRowsInserted(self, *_):
        index = self.currentModelIndex()
        if index.isValid() and self._model.hasChildren(index):
            self.setCurrentModelIndex(QModelIndex())
        self._applySearch()

    def _onModelDataChanged(self, *_):
        oldText = self._lastText
        self._refreshDisplay()
        if oldText != self._lastText:
            self.currentTextChanged.emit(self._lastText)

    def _refreshDisplay(self, *_):
        self._applySearch()
        hasSelection = self.currentModelIndex().isValid()
        self._lastText = self.currentText()
        self.setText(self._lastText if hasSelection else self._placeholderText)
        if self.property("isPlaceholderText") != (not hasSelection):
            self.setProperty("isPlaceholderText", not hasSelection)
            self.style().unpolish(self)
            self.style().polish(self)

    def _createPopup(self):
        self._popup = QFrame(self, Qt.WindowType.Popup)
        self._popup.setObjectName("treeComboPopup")
        FluentStyleSheet.COMBO_BOX.apply(self._popup)
        self._popup.installEventFilter(self)
        self._popupAnimation = QParallelAnimationGroup(self._popup)
        self._slideAnimation = QPropertyAnimation(self._popup, b"pos", self._popupAnimation)
        self._opacityAnimation = QPropertyAnimation(self._popup, b"windowOpacity", self._popupAnimation)
        for animation in (self._slideAnimation, self._opacityAnimation):
            animation.setDuration(160)
            animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            self._popupAnimation.addAnimation(animation)
        layout = QVBoxLayout(self._popup)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        self._search = SearchLineEdit(self._popup)
        self._search.setObjectName("treeComboSearch")
        self._search.setPlaceholderText(self.tr("Search items"))
        self._search.setAccessibleName(self.tr("Search items"))
        self._search.setFixedHeight(30)
        setFont(self._search, 12)
        self._search.setText(self._searchText)
        self._search.setVisible(self._searchEnabled)
        self._search.installEventFilter(self)
        self._search.textChanged.connect(self.setSearchText)
        layout.addWidget(self._search)
        self._tree = TreeView(self._popup)
        self._tree.setItemDelegate(_SearchTreeDelegate(self._tree))
        self._tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self._tree.setModel(self._viewModel)
        self._tree.setHeaderHidden(True)
        self._tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.viewport().installEventFilter(self)
        self._tree.clicked.connect(self._onTreeClicked)
        self._tree.activated.connect(self._onTreeClicked)
        layout.addWidget(self._tree)
        self._emptySearch = BodyLabel(self.tr("No matching items"), self._popup)
        self._emptySearch.setObjectName("treeComboEmptySearch")
        self._emptySearch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._emptySearch.setMinimumHeight(34)
        self._emptySearch.hide()
        layout.addWidget(self._emptySearch)

    def showPopup(self):
        if self._popup is None:
            self._createPopup()
        if self._model.rowCount() == 0:
            return
        if self._popup.isVisible():
            return

        self._popup.ensurePolished()
        self._tree.setModel(self._viewModel)
        self._tree.expandAll()
        self._tree.setLayoutDirection(self.layoutDirection())
        self._search.setLayoutDirection(self.layoutDirection())
        current = self.currentModelIndex()
        if current.isValid():
            self._tree.setCurrentIndex(self._viewModel.mapFromSource(current))
        self._applySearch()

        margins = self._popup.layout().contentsMargins()
        chromeHeight = margins.top() + margins.bottom() + 2 * self._popup.frameWidth()
        searchHeight = self._search.height() + self._popup.layout().spacing() if self._searchEnabled else 0
        desiredHeight = max(34, self._visibleRowsHeight()) + chromeHeight + searchHeight
        popupWidth = max(self.width(), 240)
        screen = QApplication.screenAt(self.mapToGlobal(QPoint(0, 0))) or QApplication.primaryScreen()
        available = screen.availableGeometry()
        popupWidth = min(popupWidth, available.width())
        below = self.mapToGlobal(QPoint(0, self.height()))
        above = self.mapToGlobal(QPoint(0, 0))
        screenTop = available.top() + 8
        screenBottom = available.bottom() - 8
        spaceBelow = max(0, screenBottom - below.y() + 1)
        spaceAbove = max(0, above.y() - screenTop)
        opensAbove = desiredHeight > spaceBelow and spaceAbove > spaceBelow
        popupHeight = min(desiredHeight, max(1, spaceAbove if opensAbove else spaceBelow))
        y = above.y() - popupHeight if opensAbove else below.y()
        y = max(screenTop, min(y, screenBottom - popupHeight + 1))
        x = max(available.left(), min(below.x(), available.right() - popupWidth + 1))
        endPos = QPoint(x, y)
        startPos = endPos + QPoint(0, 8 if opensAbove else -8)
        self._popupAnimation.stop()
        self._popup.setGeometry(x, y, popupWidth, popupHeight)
        self._popup.move(startPos)
        self._popup.setWindowOpacity(0)
        self._popup.show()
        # Give the native popup window focus so the owner becomes inactive.
        self._popup.activateWindow()
        self._slideAnimation.setStartValue(startPos)
        self._slideAnimation.setEndValue(endPos)
        self._opacityAnimation.setStartValue(0)
        self._opacityAnimation.setEndValue(1)
        self._popupAnimation.start()
        (self._search if self._searchEnabled else self._tree).setFocus()

    def _visibleRowsHeight(self) -> int:
        count = 0

        def measure(parent: QModelIndex = QModelIndex()) -> int:
            nonlocal count
            height = 0
            for row in range(self._viewModel.rowCount(parent)):
                if self._tree.isRowHidden(row, parent):
                    continue
                if 0 <= self._maxVisibleItems <= count:
                    break
                index = self._viewModel.index(row, 0, parent)
                height += max(1, self._tree.sizeHintForIndex(index).height())
                count += 1
                if self._tree.isExpanded(index):
                    height += measure(index)
            return height

        return measure()

    def hidePopup(self):
        if self._popup is not None:
            self._popup.hide()

    def _togglePopup(self):
        if self._popup is not None and self._popup.isVisible():
            self.hidePopup()
        else:
            self.showPopup()

    def _onTreeClicked(self, index: QModelIndex):
        if self._consumeBranchClick():
            return
        if not index.isValid() or self._viewModel.hasChildren(index) or not (self._viewModel.flags(index) & Qt.ItemFlag.ItemIsEnabled):
            return
        sourceIndex = self._viewModel.mapToSource(index.siblingAtColumn(0))
        self.setCurrentModelIndex(sourceIndex)
        self.activated.emit(sourceIndex)
        self.hidePopup()

    def _consumeBranchClick(self) -> bool:
        wasBranch = self._branchPress
        self._branchPress = False
        return wasBranch

    def eventFilter(self, obj, event):
        if obj is self._search and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.hidePopup()
                self.setFocus()
                return True
            if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self._tree.isVisible():
                    self._tree.setFocus()
                return True
        if obj is self._popup and event.type() == QEvent.Type.Hide:
            self._popupAnimation.stop()
            self._popup.setWindowOpacity(1)
        if self._tree is not None and obj is self._tree.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            self._branchPress = False
            index = self._tree.indexAt(event.pos())
            if index.isValid() and self._viewModel.hasChildren(index):
                depth = 0
                parent = index.parent()
                while parent.isValid():
                    depth += 1
                    parent = parent.parent()
                arrowLeft = depth * self._tree.indentation() + 20
                self._branchPress = arrowLeft < event.pos().x() < arrowLeft + 10
        return super().eventFilter(obj, event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange and self._search is not None:
            self._search.setPlaceholderText(self.tr("Search items"))
            self._search.setAccessibleName(self.tr("Search items"))
            self._emptySearch.setText(self.tr("No matching items"))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.width() - 22, self.height() / 2 - 5, 10, 10)
        if isDarkTheme():
            FIF.ARROW_DOWN.render(painter, rect)
        else:
            FIF.ARROW_DOWN.render(painter, rect, fill="#646464")


class MultiSelectionTreeComboBox(TreeComboBox):
    """Hierarchical multi-select combo box with removable selection chips.

    Only leaf nodes are returned as selections. Parent checkboxes select or
    clear all descendant leaves without selecting the parent itself. Displayed
    labels use leaf names; model indexes keep duplicate names distinct.
    """

    selectionChanged = Signal(list)
    selectedTextChanged = Signal(list)

    def __init__(self, parent=None):
        self._selected: list[QPersistentModelIndex] = []
        self._lastSelectedTexts: list[str] = []
        self._updatingChecks = False
        self._chipsMode = True
        self._chipsScrollArea: QScrollArea | None = None
        self._parentCheckPress = False
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMinimumHeight(36)

    def _createViewModel(self):
        return _MultiLeafModel(self)

    def setModel(self, model: QAbstractItemModel):
        self._selected.clear()
        super().setModel(model)

    def addItem(self, text: str, parent: QModelIndex = QModelIndex(), userData=None,
                icon: QIcon | None = None) -> QModelIndex:
        index = super().addItem(text, parent, userData, icon)
        if parent.isValid():
            parentItem = self._model.itemFromIndex(parent)
            parentItem.setCheckable(False)
            parentItem.setData(None, Qt.ItemDataRole.CheckStateRole)
        self._model.itemFromIndex(index).setCheckable(True)
        return index

    def _onModelReset(self):
        self._selected.clear()
        self._refreshDisplay()
        self.selectionChanged.emit([])
        self.selectedTextChanged.emit([])

    def _onRowsRemoved(self, parent, *_):
        before = len(self._selected)
        self._selected = [index for index in self._selected if index.isValid() and not self._model.hasChildren(QModelIndex(index))]
        self._refreshDisplay()
        if len(self._selected) != before:
            self._emitSelectionChanged()
        self._notifyParentChecks(parent)

    def _onRowsInserted(self, parent, *args):
        super()._onRowsInserted(parent, *args)
        selected = self.selectedIndexes()
        if len(selected) != len(self._selected):
            self.setSelectedIndexes(selected)
        self._notifyParentChecks(parent)

    def _onModelDataChanged(self, *_):
        if self._updatingChecks:
            return
        oldTexts = self._lastSelectedTexts
        self._refreshDisplay()
        if oldTexts != self._lastSelectedTexts:
            self.selectedTextChanged.emit(self._lastSelectedTexts)

    def selectedIndexes(self) -> list[QModelIndex]:
        return [QModelIndex(index) for index in self._selected if index.isValid() and not self._model.hasChildren(QModelIndex(index))]

    def selectedTexts(self) -> list[str]:
        return [str(index.data(Qt.ItemDataRole.DisplayRole) or "") for index in self.selectedIndexes()]

    def selectedData(self, role: int = Qt.ItemDataRole.UserRole) -> list:
        return [index.data(role) for index in self._selected if index.isValid()]

    def setSelectedIndexes(self, indexes: Iterable[QModelIndex]):
        oldSelected = self.selectedIndexes()
        selected = []
        for index in indexes:
            if index.isValid() and (index.model() is not self._model or index.column() != 0):
                raise ValueError("all indexes must be in column 0 of this combo box's model")
            if index.isValid() and self._model.hasChildren(index):
                raise ValueError("only leaf nodes can be selected")
            if index.isValid():
                persistent = QPersistentModelIndex(index)
                if persistent not in selected:
                    selected.append(persistent)
        if selected == self._selected:
            return
        self._selected = selected
        self._syncCheckStates()
        self._refreshDisplay()
        for index in set(oldSelected + self.selectedIndexes()):
            self._notifyParentChecks(index.parent())
        self._emitSelectionChanged()

    def _leafDescendants(self, parent: QModelIndex) -> list[QModelIndex]:
        leaves = []
        for row in range(self._model.rowCount(parent)):
            index = self._model.index(row, 0, parent)
            if self._model.hasChildren(index):
                leaves.extend(self._leafDescendants(index))
            elif self._model.flags(index) & Qt.ItemFlag.ItemIsEnabled:
                leaves.append(index)
        return leaves

    def _setDescendantsSelected(self, parent: QModelIndex, checked: bool):
        leaves = self._leafDescendants(parent)
        selected = self.selectedIndexes()
        if checked:
            selected.extend(index for index in leaves if index not in selected)
        else:
            selected = [index for index in selected if index not in leaves]
        self.setSelectedIndexes(selected)

    def _notifyParentChecks(self, parent: QModelIndex):
        while parent.isValid():
            index = self._viewModel.mapFromSource(parent)
            self._viewModel.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            parent = parent.parent()

    def clearSelection(self):
        self.setSelectedIndexes([])

    def setChipsMode(self, enabled: bool = True):
        self._chipsMode = enabled
        self._refreshDisplay()

    def isChipsMode(self) -> bool:
        return self._chipsMode

    def _createPopup(self):
        super()._createPopup()
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tree.setExpandsOnDoubleClick(False)
        self._tree.installEventFilter(self)

    def _syncCheckStates(self):
        if not isinstance(self._model, QStandardItemModel):
            return

        selected = self.selectedIndexes()
        def update(parent: QModelIndex = QModelIndex()):
            for row in range(self._model.rowCount(parent)):
                index = self._model.index(row, 0, parent)
                item = self._model.itemFromIndex(index)
                if item.isCheckable():
                    state = Qt.CheckState.Checked if index in selected else Qt.CheckState.Unchecked
                    if item.checkState() != state:
                        item.setCheckState(state)
                update(index)
        self._updatingChecks = True
        try:
            update()
        finally:
            self._updatingChecks = False

    def _onTreeClicked(self, index: QModelIndex):
        if self._consumeBranchClick():
            self._parentCheckPress = False
            return
        if not index.isValid() or not (self._viewModel.flags(index) & Qt.ItemFlag.ItemIsEnabled):
            self._parentCheckPress = False
            return
        if self._viewModel.hasChildren(index):
            if self._parentCheckPress:
                checked = self._viewModel.data(index, Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
                self._setDescendantsSelected(self._viewModel.mapToSource(index), not checked)
            self._parentCheckPress = False
            return
        index = self._viewModel.mapToSource(index.siblingAtColumn(0))
        selected = self.selectedIndexes()
        if index in selected:
            selected.remove(index)
        else:
            selected.append(index)
        self.setSelectedIndexes(selected)

    def _emitSelectionChanged(self):
        self.selectionChanged.emit(self.selectedIndexes())
        self.selectedTextChanged.emit(self.selectedTexts())

    def _refreshDisplay(self, *_):
        self._applySearch()
        self._selected = [index for index in self._selected if index.isValid() and not self._model.hasChildren(QModelIndex(index))]
        texts = self.selectedTexts()
        self._lastSelectedTexts = texts
        hasSelection = bool(texts)
        self.setText("" if hasSelection and self._chipsMode else ", ".join(texts) if hasSelection else self._placeholderText)
        if self.property("isPlaceholderText") != (not hasSelection):
            self.setProperty("isPlaceholderText", not hasSelection)
            self.style().unpolish(self)
            self.style().polish(self)

        if not self._chipsMode or not hasSelection:
            if self._chipsScrollArea is not None:
                self._chipsScrollArea.hide()
            return

        if self._chipsScrollArea is None:
            self._createChipsContainer()
        while self._chipsLayout.count():
            item = self._chipsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for index in self.selectedIndexes():
            chip = SubClip(str(index.data(Qt.ItemDataRole.DisplayRole) or ""), self._chipsContainer)
            chip.setFixedHeight(26)
            persistent = QPersistentModelIndex(index)
            chip.closed.connect(lambda _text, key=persistent: self._removeChip(key))
            self._chipsLayout.addWidget(chip)
        self._chipsLayout.addStretch()
        self._chipsContainer.updateGeometry()
        self._chipsScrollArea.show()

    def _createChipsContainer(self):
        self._chipsScrollArea = QScrollArea(self)
        self._chipsScrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self._chipsScrollArea.setWidgetResizable(True)
        self._chipsScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._chipsScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._chipsScrollArea.setStyleSheet("background: transparent; border: none;")
        self._chipsScrollArea.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._chipsContainer = QWidget()
        self._chipsContainer.setStyleSheet("background: transparent;")
        self._chipsLayout = QHBoxLayout(self._chipsContainer)
        self._chipsLayout.setContentsMargins(2, 0, 2, 0)
        self._chipsLayout.setSpacing(4)
        self._chipsScrollArea.setWidget(self._chipsContainer)
        self._chipsScrollArea.viewport().installEventFilter(self)
        self._chipsContainer.installEventFilter(self)
        self._positionChips()

    def _positionChips(self):
        if self._chipsScrollArea is not None:
            self._chipsScrollArea.setGeometry(8, 0, max(0, self.width() - 37), self.height())

    def _removeChip(self, index: QPersistentModelIndex):
        self.setSelectedIndexes([i for i in self.selectedIndexes() if i != QModelIndex(index)])

    def eventFilter(self, obj, event):
        if self._tree is not None and obj is self._tree.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            index = self._tree.indexAt(event.pos())
            self._parentCheckPress = False
            if index.isValid() and self._viewModel.hasChildren(index):
                rowRect = self._tree.visualRect(index)
                checkRect = QRect(rowRect.x() + 23, rowRect.center().y() - 9, 19, 19)
                self._parentCheckPress = checkRect.contains(event.pos())
        if self._tree is not None and obj is self._tree and event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Space:
            index = self._tree.currentIndex()
            if index.isValid() and self._viewModel.hasChildren(index):
                checked = self._viewModel.data(index, Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
                self._setDescendantsSelected(self._viewModel.mapToSource(index), not checked)
                return True
        if obj in (getattr(self, "_chipsContainer", None), getattr(self._chipsScrollArea, "viewport", lambda: None)()):
            if event.type() == QEvent.Type.MouseButtonRelease:
                self._togglePopup()
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._positionChips()
