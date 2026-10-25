"""Private, lazily loaded shortcut editor using the existing masked dialog."""

from PySide6.QtCore import QEvent, QKeyCombination, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from qfluentwidgets import MessageBoxBase

# from ..dialog_box.message_box_base import MessageBoxBase
from .shortcut_picker import _ALLOWED_MODIFIERS, _KeyCaps, _MODIFIER_KEYS


class _ShortcutPickerDialog(MessageBoxBase):
    def __init__(self, picker, parent):
        self._capturing = False
        self._finishing = False
        self._heldKeys = []
        self._modifiers = Qt.NoModifier
        super().__init__(parent)
        self._picker = picker
        self._ownerWindow = parent
        self.sequence = picker.keySequence()
        self.setWindowTitle(picker.dialogTitle())
        self.setWindowModality(Qt.WindowModal)
        self.titleLabel = QLabel(picker.dialogTitle(), self.widget)
        self.titleLabel.setStyleSheet('font-size:20px; font-weight:600;')
        self.titleLabel.setWordWrap(True)
        self.descriptionLabel = QLabel(picker.dialogDescription(), self.widget, objectName='contentLabel')
        self.descriptionLabel.setWordWrap(True)
        self.preview = QWidget(self.widget)
        previewLayout = QVBoxLayout(self.preview)
        previewLayout.setContentsMargins(0, 0, 0, 0)
        self.keyCaps = _KeyCaps(self.preview, large=True)
        self.keyCaps.setSequence(self.sequence)
        self.emptyLabel = QLabel(self.tr('Press a key combination'), self.preview)
        self.emptyLabel.setAlignment(Qt.AlignCenter)
        previewLayout.addWidget(self.keyCaps, 0, Qt.AlignCenter)
        previewLayout.addWidget(self.emptyLabel, 0, Qt.AlignCenter)
        self.emptyLabel.setVisible(self.sequence.isEmpty())
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.descriptionLabel)
        self.viewLayout.addWidget(self.preview, 1)
        self.yesButton.setText(self.tr('Save'))
        self.cancelButton.setText(self.tr('Cancel'))
        self.resetButton = QPushButton(self.tr('Reset'), self.buttonGroup, objectName='cancelButton')
        self.resetButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)
        self.resetButton.clicked.connect(self._reset)
        self.buttonLayout.insertWidget(1, self.resetButton, 1, Qt.AlignVCenter)
        for button in (self.yesButton, self.resetButton, self.cancelButton):
            button.setAutoDefault(False)
            button.setDefault(False)
        self._fitToOwner()

    def _fitToOwner(self):
        if self._ownerWindow is self._picker:
            # An unparented picker is itself a tiny top-level window: do not resize it.
            self.resize(600, 440)
        else:
            self.resize(self._ownerWindow.size())
        self.widget.setFixedSize(min(560, max(1, self.width() - 24)),
                                 min(400, max(1, self.height() - 24)))

    def _reset(self):
        self._heldKeys.clear()
        self._modifiers = Qt.NoModifier
        self._setDraft(self._picker.defaultKeySequence())

    def _setDraft(self, sequence):
        self.sequence = QKeySequence(sequence)
        self.keyCaps.setSequence(sequence)
        self.keyCaps.setVisible(not sequence.isEmpty())
        self.emptyLabel.setVisible(sequence.isEmpty())

    def showEvent(self, event):
        super().showEvent(event)
        self._capturing = True
        QApplication.instance().installEventFilter(self)
        self.setFocus(Qt.OtherFocusReason)

    def _stopCapture(self):
        if self._capturing:
            self._capturing = False
            QApplication.instance().removeEventFilter(self)
        self._heldKeys.clear()
        self._modifiers = Qt.NoModifier

    def done(self, result):
        if self._finishing:
            return
        self._finishing = True
        self._stopCapture()
        # Freeze the draft before the inherited fade-out finishes.
        super().done(result)

    def hideEvent(self, event):
        self._stopCapture()
        super().hideEvent(event)

    def eventFilter(self, obj, event):
        if self._capturing:
            kind = event.type()
            if kind == QEvent.ApplicationDeactivate:
                self._heldKeys.clear()
                self._modifiers = Qt.NoModifier
            elif obj is self._ownerWindow:
                if kind == QEvent.Resize:
                    self._fitToOwner()
                elif kind in (QEvent.Hide, QEvent.Close):
                    self.reject()
            inDialog = isinstance(obj, QWidget) and (obj is self or self.isAncestorOf(obj))
            if inDialog and kind in (QEvent.ShortcutOverride, QEvent.KeyPress, QEvent.KeyRelease):
                event.accept()
                if kind != QEvent.ShortcutOverride and not event.isAutoRepeat():
                    self._record(event)
                return True
            if kind == QEvent.Shortcut and self.isActiveWindow():
                # ApplicationShortcut contexts must not run while the editor records.
                event.accept()
                return True
        return super().eventFilter(obj, event)

    def _record(self, event):
        key = event.key()
        eventModifiers = event.modifiers()
        if key == Qt.Key_Backtab:
            key = Qt.Key_Tab
            eventModifiers |= Qt.ShiftModifier
        if key in (0, Qt.Key_unknown):
            return
        modifier = _MODIFIER_KEYS.get(key)
        if event.type() == QEvent.KeyRelease:
            if modifier is not None:
                self._modifiers &= ~modifier
            if key in self._heldKeys:
                self._heldKeys.remove(key)
            # Releases never erase the last captured chord from the preview.
            return
        if key == Qt.Key_Escape and self._picker.isEscapeCancelsCapture():
            self.reject()
            return
        self._modifiers = eventModifiers & _ALLOWED_MODIFIERS
        if modifier is not None:
            self._modifiers |= modifier
            mainKey = self._heldKeys[-1] if self._heldKeys else key
            modifiers = self._modifiers if self._heldKeys else self._modifiers & ~modifier
        else:
            if key in self._heldKeys:
                self._heldKeys.remove(key)
            self._heldKeys.append(key)
            mainKey, modifiers = key, self._modifiers
        self._setDraft(QKeySequence(QKeyCombination(modifiers, Qt.Key(mainKey))))
