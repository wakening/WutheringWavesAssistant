"""Theme-aware key caps and a single-chord shortcut picker (no global hooks)."""

from PySide6.QtCore import QKeyCombination, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QKeySequence, QPainter
from PySide6.QtWidgets import QDialog, QHBoxLayout, QSizePolicy, QWidget, QLabel
from qfluentwidgets import getFont, qconfig, themeColor, isDarkTheme, CardWidget, TransparentToolButton, FluentIcon

# from ...common.config import isDarkTheme, qconfig
# from ...common.font import getFont
# from ...common.icon import FluentIcon
# from ...common.style_sheet import themeColor
# from .button import TransparentToolButton
# from .card_widget import CardWidget


_MODIFIERS = (
    (Qt.ControlModifier, Qt.Key_Control, 'Ctrl'),
    (Qt.AltModifier, Qt.Key_Alt, 'Alt'),
    (Qt.ShiftModifier, Qt.Key_Shift, 'Shift'),
    (Qt.MetaModifier, Qt.Key_Meta, 'Meta'),
)
_MODIFIER_KEYS = {int(key): flag for flag, key, _ in _MODIFIERS}
_ALLOWED_MODIFIERS = (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier
                      | Qt.MetaModifier | Qt.KeypadModifier)


def _sequence(value):
    """Validate before mutation; PortableText is suitable for persistence."""
    if isinstance(value, str):
        result = QKeySequence.fromString(value, QKeySequence.PortableText)
    elif isinstance(value, (QKeySequence, QKeyCombination, int, Qt.Key)):
        result = QKeySequence(value)
    else:
        raise TypeError('keySequence must be a QKeySequence, QKeyCombination, key or string')
    if result.count() > 1:
        raise ValueError('ShortcutPicker captures a single key combination, not multiple strokes')
    if result.count() and result[0].key() in (Qt.Key_unknown, 0):
        raise ValueError('Invalid key sequence')
    if result.count() and result[0].keyboardModifiers() & ~_ALLOWED_MODIFIERS:
        raise ValueError('Unsupported keyboard modifiers')
    return result


def _tokens(sequence):
    if sequence.isEmpty():
        return []
    chord = sequence[0]
    key, modifiers = chord.key(), chord.keyboardModifiers()
    labels = [label for flag, modifierKey, label in _MODIFIERS
              if modifiers & flag or key == modifierKey]
    if modifiers & Qt.KeypadModifier:
        labels.append('Num')
    if int(key) not in _MODIFIER_KEYS:
        labels.append(QKeySequence(QKeyCombination(Qt.NoModifier, key)).toString(QKeySequence.NativeText))
    return labels


class _KeyCap(QWidget):
    def __init__(self, text, fontSize, height, parent):
        super().__init__(parent)
        self.text = text
        self.setFont(getFont(fontSize))
        self.setFixedSize(max(height, QFontMetrics(self.font()).horizontalAdvance(text) + 20), height)
        self.setAccessibleName(text)
        qconfig.themeChangedFinished.connect(self.update)
        qconfig.themeColorChanged.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(.4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(themeColor())
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 5, 5)
        painter.setPen(QColor('black' if isDarkTheme() else 'white'))
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)


class _KeyCaps(QWidget):
    def __init__(self, parent=None, large=False):
        super().__init__(parent)
        self._large = large
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(6 if not large else 8)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def setSequence(self, sequence):
        while self.row.count():
            widget = self.row.takeAt(0).widget()
            widget.hide()
            widget.deleteLater()
        for text in _tokens(sequence):
            # self.row.addWidget(_KeyCap(text, 20 if self._large else 15,
            #                           56 if self._large else 36, self))
            self.row.addWidget(_KeyCap(text, 20 if self._large else 15,
                                       56 if self._large else 28, self))
        self.row.invalidate()
        self.updateGeometry()
        self.setAccessibleName(sequence.toString(QKeySequence.NativeText) or self.tr('Not set'))


class MyShortcutPicker(CardWidget):
    """Display and capture one Qt key combination, including modifier-only keys.

    Clicking anywhere on the card opens a masked editor. Only Save commits its draft;
    Reset restores ``defaultKeySequence`` in the draft, and Cancel discards it.
    Escape cancels by default; disable ``escapeCancelsCapture`` to record Escape.
    This widget neither registers a shortcut nor captures OS-reserved combinations.
    """

    keySequenceChanged = Signal(QKeySequence)
    keySequenceSelected = Signal(QKeySequence)
    editingFinished = Signal()
    editingCanceled = Signal()

    def __init__(self, keySequence='Ctrl+Shift+A', text='', parent=None):
        if isinstance(keySequence, QWidget) and parent is None:
            parent, keySequence = keySequence, 'Ctrl+Shift+A'
        super().__init__(parent)
        self._mouseClickPending = False
        self.setClickEnabled(True)
        self.setBorderRadius(12)
        # self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.clicked.connect(self.showEditor)

        self._sequence = _sequence(keySequence)
        self._defaultSequence = QKeySequence(self._sequence)

        self._dialog = None
        self._dialogTitle = self.tr('Activate shortcut')
        self._dialogDescription = self.tr('Press a key combination to change this shortcut')
        self._escapeCancelsCapture = True

        self.keyCaps = _KeyCaps(self)
        self.keyCaps.setAttribute(Qt.WA_TransparentForMouseEvents)

        # self.editButton = TransparentToolButton(FluentIcon.EDIT, self)
        # self.editButton.setFixedSize(24, 36)
        # self.editButton.setIconSize(QSize(16, 16))
        # self.editButton.setAccessibleName(self.tr('Edit shortcut'))
        #
        # # The pencil is a visual hint, not a separate mouse/focus target.
        # self.editButton.setAttribute(Qt.WA_TransparentForMouseEvents)
        # self.editButton.setFocusPolicy(Qt.NoFocus)
        # self.editButton.clicked.connect(self.showEditor)

        self.textLabel = QLabel(text, self)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(6)
        row.addWidget(self.textLabel)
        row.addWidget(self.keyCaps)
        # row.addWidget(self.editButton)

        self.keyCaps.setSequence(self._sequence)
        self._updateAccessibleName()
        qconfig.themeChangedFinished.connect(self.update)

    def keySequence(self):
        return QKeySequence(self._sequence)

    def setKeySequence(self, keySequence):
        sequence = _sequence(keySequence)
        if sequence == self._sequence:
            return
        self._sequence = sequence
        self.keyCaps.setSequence(sequence)
        self._updateAccessibleName()
        self.updateGeometry()
        self.keySequenceChanged.emit(QKeySequence(sequence))

    def defaultKeySequence(self):
        return QKeySequence(self._defaultSequence)

    def setDefaultKeySequence(self, keySequence):
        self._defaultSequence = _sequence(keySequence)

    def reset(self):
        self.setKeySequence(self._defaultSequence)

    def clear(self):
        self.setKeySequence(QKeySequence())

    def setDialogTitle(self, title):
        self._dialogTitle = str(title)

    def dialogTitle(self):
        return self._dialogTitle

    def setDialogDescription(self, description):
        self._dialogDescription = str(description)

    def dialogDescription(self):
        return self._dialogDescription

    def setEscapeCancelsCapture(self, enabled):
        self._escapeCancelsCapture = bool(enabled)

    def isEscapeCancelsCapture(self):
        return self._escapeCancelsCapture

    def isEditing(self):
        return self._dialog is not None

    def showEditor(self):
        if not self.isEnabled() or not self.isVisible():
            return
        if self._dialog is not None:
            self._dialog.raise_()
            self._dialog.activateWindow()
            return
        # Lazy import avoids the dialog_box -> widgets -> dialog_box import cycle.
        from .widgets._shortcut_picker_dialog import _ShortcutPickerDialog
        dialog = _ShortcutPickerDialog(self, self.window())
        self._dialog = dialog
        dialog.finished.connect(self._finishEditing)
        dialog.finished.connect(dialog.deleteLater)
        self.destroyed.connect(dialog.reject)
        dialog.open()

    def cancelEditing(self):
        if self._dialog is not None:
            self._dialog.reject()

    def _finishEditing(self, result):
        dialog = self._dialog
        if dialog is None:
            return
        self._dialog = None
        selected = QKeySequence(dialog.sequence)
        if result == QDialog.Accepted:
            self.setKeySequence(selected)
            self.keySequenceSelected.emit(QKeySequence(selected))
            self.editingFinished.emit()
        else:
            self.editingCanceled.emit()
        if self.isVisible() and self.isEnabled():
            self.setFocus(Qt.OtherFocusReason)

    def _updateAccessibleName(self):
        self.setAccessibleName(self.tr('Shortcut') + ': ' +
                               (self._sequence.toString(QKeySequence.NativeText) or self.tr('Not set')))

    def hideEvent(self, event):
        self._mouseClickPending = False
        self.cancelEditing()
        super().hideEvent(event)

    def changeEvent(self, event):
        if not self.isEnabled():
            self._mouseClickPending = False
            self.cancelEditing()
        super().changeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled() and self.isClickEnabled():
            self._mouseClickPending = True
            self.setFocus(Qt.MouseFocusReason)
            super().mousePressEvent(event)
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            event.ignore()
            return
        activate = (self._mouseClickPending and self.isEnabled() and self.isClickEnabled()
                    and self.rect().contains(event.position().toPoint()))
        self._mouseClickPending = False
        if activate:
            super().mouseReleaseEvent(event)
        else:
            # CardWidget emits clicked on every release, including outside/right clicks.
            # Keep its animation but don't emit for a canceled drag or orphan release.
            self.isPressed = False
            self._updateBackgroundColor()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            if not event.isAutoRepeat() and self.isEnabled() and self.isClickEnabled():
                self.showEditor()
            event.accept()
        else:
            super().keyPressEvent(event)
