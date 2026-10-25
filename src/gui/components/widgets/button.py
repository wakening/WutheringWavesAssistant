from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSequentialAnimationGroup,
    QSize,
    Qt,
    QUrl,
    Signal,
)
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QToolButton,
    QWidget,
)
from qfluentwidgets import (
    PrimaryPushButton, isDarkTheme, FluentStyleSheet, themeColor, setFont, FluentIconBase, Theme,
    RoundMenu, MenuAnimationType, PushButton, ThemeColor, TogglePushButton, qconfig, TransparentToolButton, ToolButton,
    PrimaryToolButton, ToggleToolButton
)
from qfluentwidgets.common.animation import TranslateYAnimation, BackgroundAnimationWidget
from qfluentwidgets.common.icon import toQIcon, drawIcon, Icon, FluentIcon as FIF
from qfluentwidgets.common.overload import singledispatchmethod


# from ...common.animation import (
#     BackgroundAnimationWidget,
#     BorderColorObject,
#     TranslateYAnimation,
# )
# from ...common.color import autoFallbackThemeColor
# from ...common.config import qconfig
# from ...common.font import setFont
# from ...common.icon import FluentIcon as FIF
# from ...common.icon import FluentIconBase, Icon, Theme, drawIcon, isDarkTheme, toQIcon
# from ...common.overload import singledispatchmethod
# from ...common.style_sheet import FluentStyleSheet, ThemeColor, themeColor
# from .menu import MenuAnimationType, RoundMenu


def validColor(color: QColor, default: QColor) -> QColor:
    return color if color.isValid() else default


def fallbackThemeColor(color: QColor):
    return color if color.isValid() else themeColor()


def autoFallbackThemeColor(light: QColor, dark: QColor):
    color = dark if isDarkTheme() else light
    return fallbackThemeColor(color)


class BorderColorObject(QObject):
    """Border color object for border animation"""

    def __init__(self, parent):
        super().__init__(parent)
        self._borderColor = (
            parent._normalBorderColor()
            if hasattr(parent, "_normalBorderColor")
            else QColor(0, 0, 0, 0)
        )

    @Property(QColor)
    def borderColor(self):
        return self._borderColor

    @borderColor.setter
    def borderColor(self, color: QColor):
        self._borderColor = color
        self.parent().update()


# class PushButton(QPushButton):
#     """Push button
#
#     Constructors
#     ------------
#     * PushButton(`parent`: QWidget = None)
#     * PushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
#     * PushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
#     """
#
#     @singledispatchmethod
#     def __init__(self, parent: QWidget = None):
#         super().__init__(parent)
#         FluentStyleSheet.BUTTON.apply(self)
#         self.isPressed = False
#         self.isHover = False
#         self.setIconSize(QSize(16, 16))
#         self.setIcon(None)
#         setFont(self)
#         self._postInit()
#
#     @__init__.register
#     def _(
#         self,
#         text: str,
#         parent: QWidget = None,
#         icon: QIcon | str | FluentIconBase = None,
#     ):
#         self.__init__(parent=parent)
#         self.setText(text)
#         self.setIcon(icon)
#
#     @__init__.register
#     def _(self, icon: QIcon, text: str, parent: QWidget = None):
#         self.__init__(text, parent, icon)
#
#     @__init__.register
#     def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
#         self.__init__(text, parent, icon)
#
#     def _postInit(self):
#         pass
#
#     def setIcon(self, icon: QIcon | str | FluentIconBase):
#         if icon is None or (isinstance(icon, QIcon) and icon.isNull()):
#             self.setProperty("hasIcon", False)
#         else:
#             self.setProperty("hasIcon", True)
#
#         self.setStyle(QApplication.style())
#         self._icon = icon or QIcon()
#         self.update()
#
#     def icon(self):
#         return toQIcon(self._icon)
#
#     def setProperty(self, name: str, value) -> bool:
#         if name != "icon":
#             return super().setProperty(name, value)
#
#         self.setIcon(value)
#         return True
#
#     def mousePressEvent(self, e):
#         self.isPressed = True
#         super().mousePressEvent(e)
#
#     def mouseReleaseEvent(self, e):
#         self.isPressed = False
#         super().mouseReleaseEvent(e)
#
#     def enterEvent(self, e):
#         self.isHover = True
#         self.update()
#
#     def leaveEvent(self, e):
#         self.isHover = False
#         self.update()
#
#     def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
#         """draw icon"""
#         drawIcon(icon, painter, rect, state)
#
#     def paintEvent(self, e):
#         super().paintEvent(e)
#         if self.icon().isNull():
#             return
#
#         painter = QPainter(self)
#         painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
#
#         if not self.isEnabled():
#             painter.setOpacity(0.3628)
#         elif self.isPressed:
#             painter.setOpacity(0.786)
#
#         w, h = self.iconSize().width(), self.iconSize().height()
#         y = (self.height() - h) / 2
#         mw = self.minimumSizeHint().width()
#         if mw > 0:
#             x = 12 + (self.width() - mw) // 2
#         else:
#             x = 12
#
#         if self.isRightToLeft():
#             x = self.width() - w - x
#
#         self._drawIcon(self._icon, painter, QRectF(x, y, w, h))
#
#
# class PrimaryPushButton(PushButton):
#     """Primary color push button
#
#     Constructors
#     ------------
#     * PrimaryPushButton(`parent`: QWidget = None)
#     * PrimaryPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
#     * PrimaryPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
#     """
#
#     def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
#         if isinstance(icon, FluentIconBase) and self.isEnabled():
#             # reverse icon color
#             theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
#             icon = icon.icon(theme)
#         elif not self.isEnabled():
#             painter.setOpacity(0.786 if isDarkTheme() else 0.9)
#             if isinstance(icon, FluentIconBase):
#                 icon = icon.icon(Theme.DARK)
#
#         PushButton._drawIcon(self, icon, painter, rect, state)


class ProgressPushButton(PrimaryPushButton):
    """Primary button with a determinate ring and a stop affordance.

    Click-to-start is opt-in; clicks while progressing emit stopRequested
    without resetting the task or its progress.
    """

    progressChanged = Signal(bool)
    valueChanged = Signal(int)
    stopRequested = Signal()

    def _postInit(self):
        super()._postInit()
        self._progressing = False
        self._autoProgress = False
        self._value = 0
        self._displayValue = 0.0
        self._progressAnimation = QPropertyAnimation(self, b"displayValue", self)
        self._progressAnimation.setDuration(150)
        self.clicked.connect(self._onProgressClick)

    def setAutoProgressEnabled(self, enabled: bool):
        """Whether an idle click enters progress mode (default: False)."""
        self._autoProgress = bool(enabled)

    def isAutoProgressEnabled(self):
        return self._autoProgress

    def setProgressing(self, progressing: bool):
        progressing = bool(progressing)
        if progressing == self._progressing:
            return
        self._progressing = progressing
        self.update()
        self.progressChanged.emit(progressing)

    def isProgressing(self):
        return self._progressing

    def _onProgressClick(self):
        if self._progressing:
            self.stopRequested.emit()
        elif self._autoProgress:
            self.setProgressing(True)

    def value(self):
        return self._value

    def setValue(self, value: int):
        value = max(0, min(100, int(value)))
        if value == self._value:
            return
        self._value = value
        self._progressAnimation.stop()
        self._progressAnimation.setStartValue(self._displayValue)
        self._progressAnimation.setEndValue(float(value))
        if self.isVisible():
            self._progressAnimation.start()
        else:
            self.displayValue = float(value)
        self.valueChanged.emit(value)

    @Property(float)
    def displayValue(self):
        return self._displayValue

    @displayValue.setter
    def displayValue(self, value):
        self._displayValue = value
        self.update()

    def hideEvent(self, event):
        self._progressAnimation.stop()
        self.displayValue = float(self._value)
        super().hideEvent(event)

    def paintEvent(self, event):
        if not self._progressing:
            return super().paintEvent(event)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ""
        option.icon = QIcon()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.style().drawControl(QStyle.CE_PushButton, option, painter, self)
        foreground = QColor(Qt.black if isDarkTheme() else Qt.white)
        if not self.isEnabled():
            painter.setOpacity(0.43)
        elif self.isDown():
            painter.setOpacity(0.63)
        diameter = min(21, max(0, self.height() - 8), max(0, self.width() - 8))
        ring = QRectF(
            (self.width() - diameter) / 2 + 1.5,
            (self.height() - diameter) / 2 + 1.5,
            diameter - 3,
            diameter - 3,
        )
        track = QColor(foreground)
        track.setAlphaF(0.35)
        painter.setPen(QPen(track, 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawEllipse(ring)
        painter.setPen(QPen(foreground, 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(ring, 90 * 16, -round(self._displayValue * 3.6 * 16))
        painter.setPen(Qt.NoPen)
        painter.setBrush(foreground)
        painter.drawRoundedRect(
            QRectF(self.width() / 2 - 4, self.height() / 2 - 4, 8, 8), 2, 2
        )


class IndeterminateProgressPushButton(PrimaryPushButton):
    """Primary button with an animated, indeterminate loading arc."""

    def _postInit(self):
        super()._postInit()
        self._spinning = False
        self._startAngle = 0
        self._spanAngle = 0

        # Match the two-phase sweep used by IndeterminateProgressRing.
        self.startAngleAni1 = QPropertyAnimation(self, b"startAngle", self)
        self.startAngleAni2 = QPropertyAnimation(self, b"startAngle", self)
        self.spanAngleAni1 = QPropertyAnimation(self, b"spanAngle", self)
        self.spanAngleAni2 = QPropertyAnimation(self, b"spanAngle", self)
        for animation, start, end in (
            (self.startAngleAni1, 0, 450),
            (self.startAngleAni2, 450, 1080),
            (self.spanAngleAni1, 0, 180),
            (self.spanAngleAni2, 180, 0),
        ):
            animation.setDuration(1000)
            animation.setStartValue(start)
            animation.setEndValue(end)

        startGroup = QSequentialAnimationGroup(self)
        startGroup.addAnimation(self.startAngleAni1)
        startGroup.addAnimation(self.startAngleAni2)
        spanGroup = QSequentialAnimationGroup(self)
        spanGroup.addAnimation(self.spanAngleAni1)
        spanGroup.addAnimation(self.spanAngleAni2)
        self.aniGroup = QParallelAnimationGroup(self)
        self.aniGroup.addAnimation(startGroup)
        self.aniGroup.addAnimation(spanGroup)
        self.aniGroup.setLoopCount(-1)
        self.setMinimumWidth(150)
        self.start()

    @Property(int)
    def startAngle(self):
        return self._startAngle

    @startAngle.setter
    def startAngle(self, angle):
        self._startAngle = angle
        self.update()

    @Property(int)
    def spanAngle(self):
        return self._spanAngle

    @spanAngle.setter
    def spanAngle(self, angle):
        self._spanAngle = angle
        self.update()

    def start(self):
        self._spinning = True
        if self.isVisible():
            self.aniGroup.start()
        self.update()

    def stop(self):
        self._spinning = False
        self.aniGroup.stop()
        self._startAngle = 0
        self._spanAngle = 0
        self.update()

    def isSpinning(self) -> bool:
        return self._spinning

    def showEvent(self, event):
        super().showEvent(event)
        if self._spinning:
            self.aniGroup.start()

    def hideEvent(self, event):
        self.aniGroup.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        if not self._spinning:
            super().paintEvent(event)
            return

        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.style().drawControl(QStyle.CE_PushButton, option, painter, self)

        color = QColor(Qt.black if isDarkTheme() else Qt.white)
        if not self.isEnabled():
            color.setAlphaF(0.43)
        elif self.isDown():
            color.setAlphaF(0.63)
        painter.setPen(QPen(color, 2, Qt.SolidLine, Qt.RoundCap))

        textWidth = self.fontMetrics().horizontalAdvance(self.text())
        groupWidth = 18 + 10 + textWidth
        x = max(12, (self.width() - groupWidth) / 2)
        y = (self.height() - 18) / 2
        painter.drawArc(
            QRectF(x + 2, y + 2, 14, 14),
            ((-self._startAngle + 180) % 360) * 16,
            -self._spanAngle * 16,
        )
        painter.setPen(color)
        painter.drawText(
            QRectF(x + 28, 0, textWidth + 1, self.height()), Qt.AlignCenter, self.text()
        )


# class TransparentPushButton(PushButton):
#     """Transparent push button
#
#     Constructors
#     ------------
#     * TransparentPushButton(`parent`: QWidget = None)
#     * TransparentPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
#     * TransparentPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
#     """
#
#
# class ToggleButton(PushButton):
#     """Toggle push button
#
#     Constructors
#     ------------
#     * ToggleButton(`parent`: QWidget = None)
#     * ToggleButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
#     * ToggleButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
#     """
#
#     def _postInit(self):
#         self.setCheckable(True)
#         self.setChecked(False)
#
#     def _drawIcon(self, icon, painter, rect):
#         if not self.isChecked():
#             return PushButton._drawIcon(self, icon, painter, rect)
#
#         PrimaryPushButton._drawIcon(self, icon, painter, rect, QIcon.On)
#
#
# TogglePushButton = ToggleButton
#
#
# class TransparentTogglePushButton(TogglePushButton):
#     """Transparent toggle push button
#
#     Constructors
#     ------------
#     * TransparentTogglePushButton(`parent`: QWidget = None)
#     * TransparentTogglePushButton(`text`: str, `parent`: QWidget = None,
#                                   `icon`: QIcon | str | FluentIconBase = None)
#     * TransparentTogglePushButton(`icon`: QIcon | FluentIconBase, `text`: str, `parent`: QWidget = None)
#     """
#
#
# class HyperlinkButton(PushButton):
#     """Hyperlink button
#
#     Constructors
#     ------------
#     * HyperlinkButton(`parent`: QWidget = None)
#     * HyperlinkButton(`url`: str, `text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
#     * HyperlinkButton(`icon`: QIcon | FluentIconBase, `url`: str, `text`: str, `parent`: QWidget = None)
#     """
#
#     @singledispatchmethod
#     def __init__(self, parent: QWidget = None):
#         super().__init__(parent)
#         self._url = QUrl()
#         FluentStyleSheet.BUTTON.apply(self)
#         self.setCursor(Qt.PointingHandCursor)
#         setFont(self)
#         self.clicked.connect(self._onClicked)
#
#     @__init__.register
#     def _(
#         self,
#         url: str,
#         text: str,
#         parent: QWidget = None,
#         icon: QIcon | FluentIconBase | str = None,
#     ):
#         self.__init__(parent)
#         self.setText(text)
#         self.url.setUrl(url)
#         self.setIcon(icon)
#
#     @__init__.register
#     def _(self, icon: QIcon, url: str, text: str, parent: QWidget = None):
#         self.__init__(url, text, parent, icon)
#
#     @__init__.register
#     def _(self, icon: FluentIconBase, url: str, text: str, parent: QWidget = None):
#         self.__init__(url, text, parent, icon)
#
#     def getUrl(self):
#         return self._url
#
#     def setUrl(self, url: str | QUrl):
#         self._url = QUrl(url)
#
#     def _onClicked(self):
#         if self.getUrl().isValid():
#             QDesktopServices.openUrl(self.getUrl())
#
#     def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
#         if isinstance(icon, FluentIconBase) and self.isEnabled():
#             icon = icon.icon(color=themeColor())
#         elif not self.isEnabled():
#             painter.setOpacity(0.3628 if isDarkTheme() else 0.36)
#
#         drawIcon(icon, painter, rect, state)
#
#     url = Property(QUrl, getUrl, setUrl)


class RadioButton(QRadioButton):
    """Radio button

    Constructors
    ------------
    * RadioButton(`parent`: QWidget = None)
    * RadioButton(`url`: text, `text`: str, `parent`: QWidget = None,
                  `icon`: QIcon | str | FluentIconBase = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._lightTextColor = QColor(0, 0, 0)
        self._darkTextColor = QColor(255, 255, 255)
        self.lightIndicatorColor = QColor()
        self.darkIndicatorColor = QColor()
        self.indicatorPos = QPoint(11, 12)
        self.isHover = False

        FluentStyleSheet.BUTTON.apply(self)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self._postInit()

    @__init__.register
    def _(self, text: str, parent: QWidget = None):
        self.__init__(parent)
        self.setText(text)

    def _postInit(self):
        pass

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self._drawIndicator(painter)
        self._drawText(painter)

    def _drawText(self, painter: QPainter):
        if not self.isEnabled():
            painter.setOpacity(0.36)

        painter.setFont(self.font())
        painter.setPen(self.textColor())
        painter.drawText(
            QRect(29, 0, self.width(), self.height()), Qt.AlignVCenter, self.text()
        )

    def _drawIndicator(self, painter: QPainter):
        if self.isChecked():
            if self.isEnabled():
                borderColor = autoFallbackThemeColor(
                    self.lightIndicatorColor, self.darkIndicatorColor
                )
            else:
                borderColor = (
                    QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 55)
                )

            filledColor = Qt.black if isDarkTheme() else Qt.white

            if self.isHover and not self.isDown():
                self._drawCircle(
                    painter, self.indicatorPos, 10, 4, borderColor, filledColor
                )
            else:
                self._drawCircle(
                    painter, self.indicatorPos, 10, 5, borderColor, filledColor
                )

        else:
            if self.isEnabled():
                if not self.isDown():
                    borderColor = (
                        QColor(255, 255, 255, 153)
                        if isDarkTheme()
                        else QColor(0, 0, 0, 153)
                    )
                else:
                    borderColor = (
                        QColor(255, 255, 255, 40)
                        if isDarkTheme()
                        else QColor(0, 0, 0, 55)
                    )

                if self.isDown():
                    filledColor = Qt.black if isDarkTheme() else Qt.white
                elif self.isHover:
                    filledColor = (
                        QColor(255, 255, 255, 11)
                        if isDarkTheme()
                        else QColor(0, 0, 0, 15)
                    )
                else:
                    filledColor = (
                        QColor(0, 0, 0, 26) if isDarkTheme() else QColor(0, 0, 0, 6)
                    )
            else:
                filledColor = Qt.transparent
                borderColor = (
                    QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 55)
                )

            self._drawCircle(
                painter, self.indicatorPos, 10, 1, borderColor, filledColor
            )

            if self.isEnabled() and self.isDown():
                borderColor = (
                    QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 24)
                )
                self._drawCircle(
                    painter, self.indicatorPos, 9, 4, borderColor, Qt.transparent
                )

    def _drawCircle(
        self,
        painter: QPainter,
        center: QPoint,
        radius,
        thickness,
        borderColor,
        filledColor,
    ):
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)

        # outer circle (border)
        outerRect = QRectF(
            center.x() - radius, center.y() - radius, 2 * radius, 2 * radius
        )
        path.addEllipse(outerRect)

        # inner center (filled)
        ir = radius - thickness
        innerRect = QRectF(center.x() - ir, center.y() - ir, 2 * ir, 2 * ir)
        innerPath = QPainterPath()
        innerPath.addEllipse(innerRect)

        path = path.subtracted(innerPath)

        # draw outer ring
        painter.setPen(Qt.NoPen)
        painter.fillPath(path, borderColor)

        # fill inner circle
        painter.fillPath(innerPath, filledColor)

    def textColor(self):
        return self.darkTextColor if isDarkTheme() else self.lightTextColor

    def getLightTextColor(self) -> QColor:
        return self._lightTextColor

    def getDarkTextColor(self) -> QColor:
        return self._darkTextColor

    def setLightTextColor(self, color: QColor):
        self._lightTextColor = QColor(color)
        self.update()

    def setDarkTextColor(self, color: QColor):
        self._darkTextColor = QColor(color)
        self.update()

    def setIndicatorColor(self, light, dark):
        self.lightIndicatorColor = QColor(light)
        self.darkIndicatorColor = QColor(dark)
        self.update()

    def setTextColor(self, light, dark):
        self.setLightTextColor(light)
        self.setDarkTextColor(dark)

    lightTextColor = Property(QColor, getLightTextColor, setLightTextColor)
    darkTextColor = Property(QColor, getDarkTextColor, setDarkTextColor)


class SubtitleRadioButton(RadioButton):
    """SubTitle Radio button

    Constructors
    ------------
    * SubtitleRadioButton(`parent`: QWidget = None)
    * SubtitleRadioButton(`text`: str, `subText`: str, parent`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._subText: str = None
        self.margin: int = 6

    @__init__.register
    def _(self, text: str, subText: str, parent: QWidget = None):
        self.__init__(parent)
        self.setText(text)
        self.setSubText(subText)

    def setSubText(self, text: str):
        self._subText = text
        self.update()

    def subText(self):
        return self._subText

    def sizeHint(self):
        fm = self.fontMetrics()
        textWidth = fm.boundingRect(self.text()).width() if self.text() else 0
        subTextWidth = fm.boundingRect(self._subText).width() if self._subText else 0
        width = 29 + max(textWidth, subTextWidth) + 10
        height = fm.height() * 2 + 8
        return QSize(width, height)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self._drawIndicator(painter)

        if not self.isEnabled():
            painter.setOpacity(0.36)

        width = self.width()
        height = self.height()

        painter.setFont(self.font())
        painter.setPen(self.textColor())
        painter.drawText(
            QRect(29, 0, width, height / 2),
            Qt.AlignVCenter,
            self.text(),
        )

        if not self._subText:
            return

        font = self.font()
        font.setPixelSize(12)
        color = QColor(self.textColor())
        color.setAlpha(128)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(
            29,
            height / 2 - 5,
            width,
            height / 2,
            Qt.AlignVCenter,
            self.subText(),
        )


# class ToolButton(QToolButton):
#     """Tool button
#
#     Constructors
#     ------------
#     * ToolButton(`parent`: QWidget = None)
#     * ToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#     @singledispatchmethod
#     def __init__(self, parent: QWidget = None):
#         super().__init__(parent)
#         FluentStyleSheet.BUTTON.apply(self)
#         self.isPressed = False
#         self.isHover = False
#         self.setIconSize(QSize(16, 16))
#         self.setIcon(QIcon())
#         setFont(self)
#         self._postInit()
#
#     @__init__.register
#     def _(self, icon: FluentIconBase, parent: QWidget = None):
#         self.__init__(parent)
#         self.setIcon(icon)
#
#     @__init__.register
#     def _(self, icon: QIcon, parent: QWidget = None):
#         self.__init__(parent)
#         self.setIcon(icon)
#
#     @__init__.register
#     def _(self, icon: str, parent: QWidget = None):
#         self.__init__(parent)
#         self.setIcon(icon)
#
#     def _postInit(self):
#         pass
#
#     def setIcon(self, icon: QIcon | str | FluentIconBase):
#         self._icon = icon
#         self.update()
#
#     def icon(self):
#         return toQIcon(self._icon)
#
#     def setProperty(self, name: str, value) -> bool:
#         if name != "icon":
#             return super().setProperty(name, value)
#
#         self.setIcon(value)
#         return True
#
#     def mousePressEvent(self, e):
#         self.isPressed = True
#         super().mousePressEvent(e)
#
#     def mouseReleaseEvent(self, e):
#         self.isPressed = False
#         super().mouseReleaseEvent(e)
#
#     def enterEvent(self, e):
#         self.isHover = True
#         self.update()
#
#     def leaveEvent(self, e):
#         self.isHover = False
#         self.update()
#
#     def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
#         """draw icon"""
#         drawIcon(icon, painter, rect, state)
#
#     def paintEvent(self, e):
#         super().paintEvent(e)
#         if self._icon is None:
#             return
#
#         painter = QPainter(self)
#         painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
#
#         if not self.isEnabled():
#             painter.setOpacity(0.43)
#         elif self.isPressed:
#             painter.setOpacity(0.63)
#
#         w, h = self.iconSize().width(), self.iconSize().height()
#         y = (self.height() - h) / 2
#         x = (self.width() - w) / 2
#         self._drawIcon(self._icon, painter, QRectF(x, y, w, h))
#
#
# class TransparentToolButton(ToolButton):
#     """Transparent background tool button
#
#     Constructors
#     ------------
#     * TransparentToolButton(`parent`: QWidget = None)
#     * TransparentToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """


class HyperlinkToolButton(TransparentToolButton):
    """Hyperlink tool button with theme color icon

    Constructors
    ------------
    * HyperlinkToolButton(`parent`: QWidget = None)
    * HyperlinkToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
    * HyperlinkToolButton(`icon`: QIcon | str | FluentIconBase, `url`: str, `parent`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._url = ""

    @__init__.register
    def _(self, icon: FluentIconBase, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: str, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: FluentIconBase, url: str, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)
        self._url = url

    @__init__.register
    def _(self, icon: QIcon, url: str, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)
        self._url = url

    @__init__.register
    def _(self, icon: str, url: str, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)
        self._url = url

    def setUrl(self, url: str):
        """Set the URL to open when clicked"""
        self._url = url

    def url(self) -> str:
        """Get the URL"""
        return self._url

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if self._url and self.isEnabled():
            QDesktopServices.openUrl(QUrl(self._url))

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
        if not self.isEnabled():
            painter.setOpacity(0.43 if isDarkTheme() else 0.5)

        if isinstance(icon, FluentIconBase):
            icon.render(painter, rect, theme=Theme.LIGHT, fill=themeColor().name())
        elif isinstance(icon, Icon):
            icon.fluentIcon.render(
                painter, rect, theme=Theme.LIGHT, fill=themeColor().name()
            )
        else:
            drawIcon(icon, painter, rect, state)


# class PrimaryToolButton(ToolButton):
#     """Primary color tool button
#
#     Constructors
#     ------------
#     * PrimaryToolButton(`parent`: QWidget = None)
#     * PrimaryToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#     def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
#         if isinstance(icon, FluentIconBase) and self.isEnabled():
#             # reverse icon color
#             theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
#             icon = icon.icon(theme)
#         elif isinstance(icon, Icon) and self.isEnabled():
#             theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
#             icon = icon.fluentIcon.icon(theme)
#         elif not self.isEnabled():
#             painter.setOpacity(0.786 if isDarkTheme() else 0.9)
#             if isinstance(icon, FluentIconBase):
#                 icon = icon.icon(Theme.DARK)
#
#         return drawIcon(icon, painter, rect, state)
#
#
# class ToggleToolButton(ToolButton):
#     """Toggle tool button
#
#     Constructors
#     ------------
#     * ToggleToolButton(`parent`: QWidget = None)
#     * ToggleToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#     def _postInit(self):
#         self.setCheckable(True)
#         self.setChecked(False)
#
#     def _drawIcon(self, icon, painter, rect):
#         if not self.isChecked():
#             return ToolButton._drawIcon(self, icon, painter, rect)
#
#         PrimaryToolButton._drawIcon(self, icon, painter, rect, QIcon.On)
#
#
# class TransparentToggleToolButton(ToggleToolButton):
#     """Transparent toggle tool button
#
#     Constructors
#     ------------
#     * TransparentToggleToolButton(`parent`: QWidget = None)
#     * TransparentToggleToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#
# class DropDownButtonBase:
#     """Drop down button base class"""
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._menu = None
#         self.arrowAni = TranslateYAnimation(self)
#
#     def setMenu(self, menu: RoundMenu):
#         self._menu = menu
#
#     def menu(self) -> RoundMenu:
#         return self._menu
#
#     def _showMenu(self):
#         if not self.menu():
#             return
#
#         menu = self.menu()
#         menu.view.setMinimumWidth(self.width())
#         menu.view.adjustSize()
#         menu.adjustSize()
#
#         # determine the animation type by choosing the maximum height of view
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
#     def _hideMenu(self):
#         if self.menu():
#             self.menu().hide()
#
#     def _drawDropDownIcon(self, painter, rect):
#         if isDarkTheme():
#             FIF.ARROW_DOWN.render(painter, rect)
#         else:
#             FIF.ARROW_DOWN.render(painter, rect, fill="#646464")
#
#     def paintEvent(self, e):
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
#         self._drawDropDownIcon(painter, rect)
#
#
# class DropDownPushButton(DropDownButtonBase, PushButton):
#     """Drop down push button
#
#     Constructors
#     ------------
#     * DropDownPushButton(`parent`: QWidget = None)
#     * DropDownPushButton(`text`: str, `parent`: QWidget = None,
#                          `icon`: QIcon | str | FluentIconBase = None)
#     * DropDownPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
#     """
#
#     def mouseReleaseEvent(self, e):
#         PushButton.mouseReleaseEvent(self, e)
#         self._showMenu()
#
#     def paintEvent(self, e):
#         PushButton.paintEvent(self, e)
#         DropDownButtonBase.paintEvent(self, e)
#
#
# class TransparentDropDownPushButton(DropDownPushButton):
#     """Transparent drop down push button
#
#     Constructors
#     ------------
#     * TransparentDropDownPushButton(`parent`: QWidget = None)
#     * TransparentDropDownPushButton(`text`: str, `parent`: QWidget = None,
#                                     `icon`: QIcon | str | FluentIconBase = None)
#     * TransparentDropDownPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
#     """
#
#
# class DropDownToolButton(DropDownButtonBase, ToolButton):
#     """Drop down tool button
#
#     Constructors
#     ------------
#     * DropDownToolButton(`parent`: QWidget = None)
#     * DropDownToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#     def mouseReleaseEvent(self, e):
#         ToolButton.mouseReleaseEvent(self, e)
#         self._showMenu()
#
#     def _drawIcon(self, icon, painter, rect: QRectF):
#         rect.moveLeft(12)
#         return super()._drawIcon(icon, painter, rect)
#
#     def paintEvent(self, e):
#         ToolButton.paintEvent(self, e)
#         DropDownButtonBase.paintEvent(self, e)
#
#
# class TransparentDropDownToolButton(DropDownToolButton):
#     """Transparent drop down tool button
#
#     Constructors
#     ------------
#     * TransparentDropDownToolButton(`parent`: QWidget = None)
#     * TransparentDropDownToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#
# class PrimaryDropDownButtonBase(DropDownButtonBase):
#     """Primary color drop down button base class"""
#
#     def _drawDropDownIcon(self, painter, rect):
#         theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
#         FIF.ARROW_DOWN.render(painter, rect, theme)
#
#
# class PrimaryDropDownPushButton(PrimaryDropDownButtonBase, PrimaryPushButton):
#     """Primary color drop down push button
#
#     Constructors
#     ------------
#     * PrimaryDropDownPushButton(`parent`: QWidget = None)
#     * PrimaryDropDownPushButton(`text`: str, `parent`: QWidget = None,
#                                 `icon`: QIcon | str | FluentIconBase = None)
#     * PrimaryDropDownPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
#     """
#
#     def mouseReleaseEvent(self, e):
#         PrimaryPushButton.mouseReleaseEvent(self, e)
#         self._showMenu()
#
#     def paintEvent(self, e):
#         PrimaryPushButton.paintEvent(self, e)
#         PrimaryDropDownButtonBase.paintEvent(self, e)
#
#
# class PrimaryDropDownToolButton(PrimaryDropDownButtonBase, PrimaryToolButton):
#     """Primary drop down tool button
#
#     Constructors
#     ------------
#     * PrimaryDropDownToolButton(`parent`: QWidget = None)
#     * PrimaryDropDownToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#     def mouseReleaseEvent(self, e):
#         PrimaryToolButton.mouseReleaseEvent(self, e)
#         self._showMenu()
#
#     def _drawIcon(self, icon, painter, rect: QRectF):
#         rect.moveLeft(12)
#         return super()._drawIcon(icon, painter, rect)
#
#     def paintEvent(self, e):
#         PrimaryToolButton.paintEvent(self, e)
#         PrimaryDropDownButtonBase.paintEvent(self, e)


class SplitDropButton(ToolButton):
    def _postInit(self):
        self.arrowAni = TranslateYAnimation(self)
        self.setIcon(FIF.ARROW_DOWN)
        self.setIconSize(QSize(10, 10))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

    def _drawIcon(self, icon, painter, rect):
        rect.translate(0, self.arrowAni.y)

        if self.isPressed:
            painter.setOpacity(0.5)
        elif self.isHover:
            painter.setOpacity(1)
        else:
            painter.setOpacity(0.63)

        super()._drawIcon(icon, painter, rect)


class PrimarySplitDropButton(PrimaryToolButton):
    def _postInit(self):
        self.arrowAni = TranslateYAnimation(self)
        self.setIcon(FIF.ARROW_DOWN)
        self.setIconSize(QSize(10, 10))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

    def _drawIcon(self, icon, painter, rect):
        rect.translate(0, self.arrowAni.y)

        if self.isPressed:
            painter.setOpacity(0.7)
        elif self.isHover:
            painter.setOpacity(0.9)
        else:
            painter.setOpacity(1)

        if isinstance(icon, FluentIconBase):
            icon = icon.icon(Theme.DARK if not isDarkTheme() else Theme.LIGHT)

        super()._drawIcon(icon, painter, rect)


class SplitWidgetBase(QWidget):
    """Split widget base class"""

    dropDownClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.flyout = None  # type: QWidget
        self.dropButton = SplitDropButton(self)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.dropButton)

        self.dropButton.clicked.connect(self.dropDownClicked)
        self.dropButton.clicked.connect(self.showFlyout)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def setWidget(self, widget: QWidget):
        """set the widget on left side"""
        self.hBoxLayout.insertWidget(0, widget, 1, Qt.AlignLeft)

    def setDropButton(self, button):
        """set drop dow button"""
        self.hBoxLayout.removeWidget(self.dropButton)
        self.dropButton.deleteLater()

        self.dropButton = button
        self.dropButton.clicked.connect(self.dropDownClicked)
        self.dropButton.clicked.connect(self.showFlyout)
        self.hBoxLayout.addWidget(button)

    def setDropIcon(self, icon: str | QIcon | FluentIconBase):
        """set the icon of drop down button"""
        self.dropButton.setIcon(icon)
        self.dropButton.removeEventFilter(self.dropButton.arrowAni)

    def setDropIconSize(self, size: QSize):
        """set the icon size of drop down button"""
        self.dropButton.setIconSize(size)

    def setFlyout(self, flyout):
        """set the widget pops up when drop down button is clicked

        Parameters
        ----------
        flyout: QWidget
            the widget pops up when drop down button is clicked.
            It should contain `exec(pos: QPoint)` method
        """
        self.flyout = flyout

    def showFlyout(self):
        """show flyout"""
        if not self.flyout:
            return

        w = self.flyout

        if isinstance(w, RoundMenu):
            w.view.setMinimumWidth(self.width())
            w.view.adjustSize()
            w.adjustSize()

        dx = w.layout().contentsMargins().left() if isinstance(w, RoundMenu) else 0
        x = -w.width() // 2 + dx + self.width() // 2
        y = self.height()
        w.exec(self.mapToGlobal(QPoint(x, y)))


class SplitPushButton(SplitWidgetBase):
    """Split push button

    Constructors
    ------------
    * SplitPushButton(`parent`: QWidget = None)
    * SplitPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
    """

    clicked = Signal()

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.button = PushButton(self)
        self.button.setObjectName("splitPushButton")
        self.button.clicked.connect(self.clicked)
        self.setWidget(self.button)
        self._postInit()

    @__init__.register
    def _(
        self,
        text: str,
        parent: QWidget = None,
        icon: QIcon | str | FluentIconBase = None,
    ):
        self.__init__(parent)
        self.setText(text)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    def _postInit(self):
        pass

    def text(self):
        return self.button.text()

    def setText(self, text: str):
        self.button.setText(text)
        self.adjustSize()

    def icon(self):
        return self.button.icon()

    def setIcon(self, icon: QIcon | FluentIconBase | str):
        self.button.setIcon(icon)

    def setIconSize(self, size: QSize):
        self.button.setIconSize(size)

    text_ = Property(str, text, setText)
    icon_ = Property(QIcon, icon, setIcon)


# class PrimarySplitPushButton(SplitPushButton):
#     """Primary split push button
#
#     Constructors
#     ------------
#     * PrimarySplitPushButton(`parent`: QWidget = None)
#     * PrimarySplitPushButton(`text`: str, `parent`: QWidget = None,
#                              `icon`: QIcon | str | FluentIconBase = None)
#     * PrimarySplitPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
#     """
#
#     def _postInit(self):
#         self.setDropButton(PrimarySplitDropButton(self))
#
#         self.hBoxLayout.removeWidget(self.button)
#         self.button.deleteLater()
#
#         self.button = PrimaryPushButton(self)
#         self.button.setObjectName("primarySplitPushButton")
#         self.button.clicked.connect(self.clicked)
#         self.setWidget(self.button)
#
#
# class SplitToolButton(SplitWidgetBase):
#     """Split tool button
#
#     Constructors
#     ------------
#     * SplitToolButton(`parent`: QWidget = None)
#     * SplitToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#     clicked = Signal()
#
#     @singledispatchmethod
#     def __init__(self, parent: QWidget = None):
#         super().__init__(parent=parent)
#         self.button = ToolButton(self)
#         self.button.setObjectName("splitToolButton")
#         self.button.clicked.connect(self.clicked)
#         self.setWidget(self.button)
#         self._postInit()
#
#     @__init__.register
#     def _(self, icon: FluentIconBase, parent: QWidget = None):
#         self.__init__(parent)
#         self.setIcon(icon)
#
#     @__init__.register
#     def _(self, icon: QIcon, parent: QWidget = None):
#         self.__init__(parent)
#         self.setIcon(icon)
#
#     @__init__.register
#     def _(self, icon: str, parent: QWidget = None):
#         self.__init__(parent)
#         self.setIcon(icon)
#
#     def _postInit(self):
#         pass
#
#     def icon(self):
#         return self.button.icon()
#
#     def setIcon(self, icon: QIcon | FluentIconBase | str):
#         self.button.setIcon(icon)
#
#     def setIconSize(self, size: QSize):
#         self.button.setIconSize(size)
#
#     icon_ = Property(QIcon, icon, setIcon)
#
#
# class PrimarySplitToolButton(SplitToolButton):
#     """Primary split push button
#
#     Constructors
#     ------------
#     * PrimarySplitToolButton(`parent`: QWidget = None)
#     * PrimarySplitToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
#     """
#
#     def _postInit(self):
#         self.setDropButton(PrimarySplitDropButton(self))
#
#         self.hBoxLayout.removeWidget(self.button)
#         self.button.deleteLater()
#
#         self.button = PrimaryToolButton(self)
#         self.button.setObjectName("primarySplitToolButton")
#         self.button.clicked.connect(self.clicked)
#         self.setWidget(self.button)


class RoundButtonBase(BackgroundAnimationWidget):
    """Round button base class

    Subclasses can set `isCircular = True` for fully circular shape,
    otherwise uses rounded rectangle with radius = height/2
    """

    isCircular = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _normalBackgroundColor(self):
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 15) if isDark else QColor(255, 255, 255, 178)

    def _hoverBackgroundColor(self):
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 21) if isDark else QColor(249, 249, 249, 128)

    def _pressedBackgroundColor(self):
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 8) if isDark else QColor(249, 249, 249, 76)

    def _disabledBackgroundColor(self):
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 10) if isDark else QColor(249, 249, 249, 76)

    def _drawBackground(self, painter, rect, r, isDark):
        """draw background and border"""
        borderColor = QColor(255, 255, 255, 13) if isDark else QColor(0, 0, 0, 19)
        bgColor = self.backgroundColor

        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)

        if self.isCircular:
            painter.drawEllipse(rect)
        else:
            painter.drawRoundedRect(rect, r, r)

        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        if self.isCircular:
            path.addEllipse(rect)
        else:
            path.addRoundedRect(rect, r, r)

        borderRect = rect.adjusted(1, 1, -1, -1)
        innerPath = QPainterPath()
        if self.isCircular:
            innerPath.addEllipse(borderRect)
        else:
            innerPath.addRoundedRect(borderRect, r - 1, r - 1)
        path = path.subtracted(innerPath)

        painter.setBrush(borderColor)
        painter.drawPath(path)

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """draw icon"""
        drawIcon(icon, painter, rect, state)

    def _drawText(self, painter, text, rect, isDark):
        """draw text"""
        painter.setPen(Qt.white if isDark else Qt.black)
        painter.drawText(rect, Qt.AlignCenter, text)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
            | QPainter.TextAntialiasing
        )
        isDark = isDarkTheme()

        if self.isCircular:
            size = min(self.width(), self.height())
            rect = QRectF(
                (self.width() - size) / 2, (self.height() - size) / 2, size, size
            )
            rect = rect.adjusted(1, 1, -1, -1)
            r = size / 2
        else:
            rect = self.rect().adjusted(1, 1, -1, -1)
            r = rect.height() / 2

        self._drawBackground(painter, rect, r, isDark)

        if not self.isEnabled():
            painter.setOpacity(
                0.43 if self.isCircular else (0.3628 if isDark else 0.36)
            )
        elif self.isPressed:
            painter.setOpacity(0.63 if self.isCircular else 0.786)

        if (
            hasattr(self, "_icon")
            and self._icon
            and not (isinstance(self._icon, QIcon) and self._icon.isNull())
        ):
            w, h = self.iconSize().width(), self.iconSize().height()
            if self.isCircular:
                x = (self.width() - w) / 2
                y = (self.height() - h) / 2
            else:
                y = (self.height() - h) / 2
                mw = self.minimumSizeHint().width()
                x = 12 + (self.width() - mw) // 2 if mw > 0 else 12
                if self.isRightToLeft():
                    x = self.width() - w - x

            self._drawIcon(self._icon, painter, QRectF(x, y, w, h))

        if not self.isCircular:
            painter.setFont(self.font())
            textRect = QRect(0, 0, self.width(), self.height())
            self._drawText(painter, self.text(), textRect, isDark)


class RoundPushButton(RoundButtonBase, PushButton):
    """Round push button

    Constructors
    ------------
    * RoundPushButton(`parent`: QWidget = None)
    * RoundPushButton(`text`: str, `parent`: QWidget = None,
                      `icon`: QIcon | str | FluentIconBase = None)
    * RoundPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
    """


class RoundToolButton(RoundButtonBase, ToolButton):
    """Round tool button - fully circular

    Constructors
    ------------
    * RoundToolButton(`parent`: QWidget = None)
    * RoundToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
    """

    isCircular = True

    def __init__(self, *args, **kwargs):
        self._hasBorder = True
        super().__init__(*args, **kwargs)

    def setHasBorder(self, hasBorder: bool):
        """Set whether to show border in normal state"""
        self._hasBorder = hasBorder
        self.update()

    def hasBorder(self) -> bool:
        """Get whether border is shown in normal state"""
        return self._hasBorder

    def _drawBackground(self, painter, rect, r, isDark):
        """draw background and border"""
        # If no border in normal state and not hover/pressed, skip drawing
        if not self._hasBorder and not self.isHover and not self.isPressed:
            return

        # Normal state with border
        if self._hasBorder and not self.isHover and not self.isPressed:
            super()._drawBackground(painter, rect, r, isDark)
            return

        # Background on hover/pressed (no border)
        if self.isPressed:
            bgColor = QColor(255, 255, 255, 8) if isDark else QColor(0, 0, 0, 6)
        else:  # hover
            bgColor = QColor(255, 255, 255, 21) if isDark else QColor(0, 0, 0, 9)

        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawEllipse(rect)


class OutlinedButtonBase(BackgroundAnimationWidget):
    """Outlined button base class

    Features:
    - Border only (no background fill except hover on unchecked)
    - Checkable state: checked -> border/icon/text become theme color
    - Border radius = height/2 (pill shape)
    - Background color animation on hover
    """

    isCircular = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCheckable(True)

    def mousePressEvent(self, e):
        self.isHover = False
        super().mousePressEvent(e)

    def _normalBackgroundColor(self):
        return QColor(0, 0, 0, 0)

    def _hoverBackgroundColor(self):
        if self.isChecked():
            return QColor(0, 0, 0, 0)
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 21) if isDark else QColor(0, 0, 0, 11)

    def _pressedBackgroundColor(self):
        if self.isChecked():
            return QColor(0, 0, 0, 0)
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 8) if isDark else QColor(0, 0, 0, 17)

    def _disabledBackgroundColor(self):
        if self.isChecked():
            return QColor(0, 0, 0, 0)
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 11) if isDark else QColor(249, 249, 249, 75)

    def _getBorderColor(self, isDark):
        """get border color based on state"""
        if self.isChecked():
            return themeColor()
        return QColor(255, 255, 255, 18) if isDark else QColor(0, 0, 0, 15)

    def _getTextColor(self, isDark):
        """get text/icon color"""
        if self.isChecked():
            return themeColor()
        return Qt.white if isDark else Qt.black

    def _drawBackground(self, painter, rect, r, isDark):
        """draw background and border"""
        bgColor = self.backgroundColor
        borderColor = self._getBorderColor(isDark)

        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(rect, r, r)

        # draw border
        painter.setPen(borderColor)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, r, r)

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """draw icon with theme color when checked"""
        if self.isChecked() and isinstance(icon, FluentIconBase):
            icon = icon.icon(color=themeColor())
        drawIcon(icon, painter, rect, state)

    def _drawText(self, painter, text, rect, isDark):
        """draw text"""
        color = self._getTextColor(isDark)
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignCenter, text)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
            | QPainter.TextAntialiasing
        )
        isDark = isDarkTheme()

        rect = self.rect().adjusted(1, 1, -1, -1)
        r = rect.height() / 2

        self._drawBackground(painter, rect, r, isDark)

        if not self.isEnabled():
            painter.setOpacity(0.3628 if isDark else 0.36)
        elif self.isPressed:
            painter.setOpacity(0.786)

        if (
            hasattr(self, "_icon")
            and self._icon
            and not (isinstance(self._icon, QIcon) and self._icon.isNull())
        ):
            w, h = self.iconSize().width(), self.iconSize().height()
            if self.isCircular:
                x = (self.width() - w) / 2
                y = (self.height() - h) / 2
            else:
                y = (self.height() - h) / 2
                mw = self.minimumSizeHint().width()
                x = 12 + (self.width() - mw) // 2 if mw > 0 else 12
                if self.isRightToLeft():
                    x = self.width() - w - x

            self._drawIcon(self._icon, painter, QRectF(x, y, w, h))

        if not self.isCircular:
            painter.setFont(self.font())

            # calculate text position considering icon
            hasIcon = (
                hasattr(self, "_icon")
                and self._icon
                and not (isinstance(self._icon, QIcon) and self._icon.isNull())
            )

            if hasIcon:
                iconW = self.iconSize().width()
                textRect = QRect(0, 0, self.width() - iconW - 8, self.height())
                textRect.moveLeft(iconW + 8)
            else:
                textRect = QRect(0, 0, self.width(), self.height())

            self._drawText(painter, self.text(), textRect, isDark)


class OutlinedPushButton(OutlinedButtonBase, PushButton):
    """Outlined push button

    Constructors
    ------------
    * OutlinedPushButton(`parent`: QWidget = None)
    * OutlinedPushButton(`text`: str, `parent`: QWidget = None,
                         `icon`: QIcon | str | FluentIconBase = None)
    * OutlinedPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
    """


class OutlinedToolButton(OutlinedButtonBase, ToolButton):
    """Outlined tool button

    Constructors
    ------------
    * OutlinedToolButton(`parent`: QWidget = None)
    * OutlinedToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
    """

    isCircular = True


class FilledButtonBase(BackgroundAnimationWidget):
    """Filled button base class with 5 color schemes

    Color schemes:
    - information: grey
    - success: green
    - attention: theme color
    - warning: yellow/orange
    - error: red

    Features:
    - Background and border color animation on hover/press
    """

    # Color scheme enum
    INFORMATION = "information"
    SUCCESS = "success"
    ATTENTION = "attention"
    WARNING = "warning"
    ERROR = "error"

    def __init__(self, *args, **kwargs):
        self._colorScheme = self.ATTENTION
        self._pressedAndReleased = False  # Track if pressed was released while hovering
        super().__init__(*args, **kwargs)

        # Border color animation
        self.borderColorObj = BorderColorObject(self)
        self.borderColorAni = QPropertyAnimation(
            self.borderColorObj, b"borderColor", self
        )
        self.borderColorAni.setDuration(120)

    def setColorScheme(self, scheme: str):
        """Set color scheme"""
        self._colorScheme = scheme
        self._updateBackgroundColor()
        self._updateBorderColor()

    def colorScheme(self):
        """Get color scheme"""
        return self._colorScheme

    def _getSchemeColors(self, isDark):
        """Get colors for current scheme

        Returns dict with:
        - bg: (normal, hover, pressed, disabled)
        - border: (normal, hover, pressed)
        - text: text color
        """
        scheme = self._colorScheme
        bgHover = QColor(0, 0, 0, 60) if not isDark else QColor(255, 255, 255, 67)
        bgPressed = QColor(0, 0, 0, 100) if not isDark else QColor(255, 255, 255, 30)
        borderHover = QColor(0, 0, 0, 128) if not isDark else QColor(255, 255, 255, 150)
        borderPressed = QColor(0, 0, 0, 0) if not isDark else QColor(255, 255, 255, 30)

        # Light resting fills use Fluent SystemFillSolidNeutral/Success/Caution/
        # Critical tokens. Keep the existing dark palette and interaction fills.
        # https://learn.microsoft.com/visualstudio/extensibility/ux-guidelines/theme-color-token-reference
        if scheme == self.INFORMATION:
            bgNormal = QColor(255, 255, 255, 100) if isDark else QColor("#8A8A8A")
            borderNormal = QColor(255, 255, 255, 150) if isDark else QColor("#8A8A8A")
            textColor = QColor(255, 255, 255)

        elif scheme == self.SUCCESS:
            bgNormal = QColor(103, 186, 71, 128) if isDark else QColor("#0F7B0F")
            borderNormal = (
                QColor(133, 197, 109, 254) if isDark else QColor("#0F7B0F").darker(115)
            )
            textColor = QColor(255, 255, 255)

        elif scheme == self.ATTENTION:
            bgNormal = ThemeColor.DARK_3.color() if isDarkTheme() else themeColor()
            borderNormal = (
                ThemeColor.LIGHT_1.color()
                if isDarkTheme()
                else ThemeColor.DARK_1.color()
            )
            textColor = QColor(255, 255, 255)

        elif scheme == self.WARNING:
            bgNormal = QColor(142, 129, 16, 254) if isDark else QColor("#9D5D00")
            borderNormal = (
                QColor(255, 255, 51, 254) if isDark else QColor("#9D5D00").darker(115)
            )
            textColor = QColor(255, 255, 255)

        elif scheme == self.ERROR:
            bgNormal = QColor(156, 31, 8, 128) if isDark else QColor("#C42B1C")
            borderNormal = (
                QColor(180, 45, 52, 254) if isDark else QColor("#C42B1C").darker(115)
            )
            textColor = QColor(255, 255, 255)

        bgDisabled = QColor(255, 255, 255, 10) if isDark else QColor(249, 249, 249, 76)
        textDisabled = QColor(255, 255, 255, 80) if isDark else QColor(0, 0, 0, 80)

        return {
            "bg": (bgNormal, bgHover, bgPressed, bgDisabled),
            "border": (borderNormal, borderHover, borderPressed),
            "text": textColor,
            "textDisabled": textDisabled,
        }

    def _normalBackgroundColor(self):
        isDark = isDarkTheme()
        colors = self._getSchemeColors(isDark)
        return colors["bg"][0]

    def _hoverBackgroundColor(self):
        isDark = isDarkTheme()
        colors = self._getSchemeColors(isDark)
        # Return normal background if pressed was released while hovering
        if self._pressedAndReleased:
            return colors["bg"][0]
        return colors["bg"][1]

    def _pressedBackgroundColor(self):
        isDark = isDarkTheme()
        colors = self._getSchemeColors(isDark)
        return colors["bg"][2]

    def _disabledBackgroundColor(self):
        isDark = isDarkTheme()
        colors = self._getSchemeColors(isDark)
        return colors["bg"][3]

    def mouseReleaseEvent(self, e):
        # Set flag if releasing while still hovering
        if self.isHover:
            self._pressedAndReleased = True
        super().mouseReleaseEvent(e)

    def leaveEvent(self, e):
        self._pressedAndReleased = False
        super().leaveEvent(e)

    def _normalBorderColor(self):
        isDark = isDarkTheme()
        colors = self._getSchemeColors(isDark)
        return colors["border"][0]

    def _hoverBorderColor(self):
        isDark = isDarkTheme()
        colors = self._getSchemeColors(isDark)
        return colors["border"][1]

    def _pressedBorderColor(self):
        isDark = isDarkTheme()
        colors = self._getSchemeColors(isDark)
        return colors["border"][2]

    def _updateBorderColor(self):
        if not self.isEnabled():
            color = QColor(0, 0, 0, 0)
        elif self.isPressed:
            color = self._pressedBorderColor()
        elif self.isHover:
            color = self._hoverBorderColor()
        else:
            color = self._normalBorderColor()

        self.borderColorAni.stop()
        self.borderColorAni.setEndValue(color)
        self.borderColorAni.start()

    def _updateBackgroundColor(self):
        super()._updateBackgroundColor()
        self._updateBorderColor()

    def getBorderColor(self):
        return self.borderColorObj.borderColor

    @property
    def borderColor(self):
        return self.getBorderColor()

    def _drawBackground(self, painter, rect, r, isDark):
        """draw background and border"""
        bgColor = self.backgroundColor
        borderColor = self.borderColor

        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(rect, r, r)

        # draw border (内缩 0.5px 使 1px 笔触完整居中，避免边缘被裁剪)
        if borderColor.alpha() > 0:
            painter.setPen(borderColor)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), r, r)

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """draw icon with theme color when checked"""
        isDark = isDarkTheme()
        colors = self._getSchemeColors(isDark)

        if isinstance(icon, FluentIconBase):
            icon = icon.icon(color=colors["text"])
        drawIcon(icon, painter, rect, state)

    def _drawText(self, painter, text, rect, isDark):
        """draw text"""
        colors = self._getSchemeColors(isDark)
        color = colors["text"] if self.isEnabled() else colors["textDisabled"]
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignCenter, text)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
            | QPainter.TextAntialiasing
        )
        isDark = isDarkTheme()

        rect = self.rect()
        r = 5  # Fixed border-radius like PushButton

        self._drawBackground(painter, rect, r, isDark)

        if not self.isEnabled():
            painter.setOpacity(0.3628 if isDark else 0.36)
        elif self.isPressed:
            painter.setOpacity(0.786)

        if (
            hasattr(self, "_icon")
            and self._icon
            and not (isinstance(self._icon, QIcon) and self._icon.isNull())
        ):
            w, h = self.iconSize().width(), self.iconSize().height()
            y = (self.height() - h) / 2
            if self.text().strip():
                # 带文字：icon 偏左、文字在右侧
                mw = self.minimumSizeHint().width()
                x = 12 + (self.width() - mw) // 2 if mw > 0 else 12
            else:
                # 纯 icon（如 FilledToolButton）：水平居中
                x = (self.width() - w) / 2
            if self.isRightToLeft():
                x = self.width() - w - x

            self._drawIcon(self._icon, painter, QRectF(x, y, w, h))

        painter.setFont(self.font())

        # calculate text position considering icon
        hasIcon = (
            hasattr(self, "_icon")
            and self._icon
            and not (isinstance(self._icon, QIcon) and self._icon.isNull())
        )

        if hasIcon:
            iconW = self.iconSize().width()
            textRect = QRect(0, 0, self.width() - iconW - 8, self.height())
            textRect.moveLeft(iconW + 8)
        else:
            textRect = QRect(0, 0, self.width(), self.height())

        self._drawText(painter, self.text(), textRect, isDark)


class FilledPushButton(FilledButtonBase, PushButton):
    """Filled push button

    Constructors
    ------------
    * FilledPushButton(`parent`: QWidget = None)
    * FilledPushButton(`text`: str, `parent`: QWidget = None,
                      `icon`: QIcon | str | FluentIconBase = None)
    * FilledPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
    """


class FilledToolButton(FilledButtonBase, ToolButton):
    """Filled tool button

    Constructors
    ------------
    * FilledToolButton(`parent`: QWidget = None)
    * FilledToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
    """


class PillButtonBase:
    """Pill button base class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        isDark = isDarkTheme()

        if not self.isChecked():
            rect = self.rect().adjusted(1, 1, -1, -1)
            borderColor = QColor(255, 255, 255, 18) if isDark else QColor(0, 0, 0, 15)

            if not self.isEnabled():
                bgColor = (
                    QColor(255, 255, 255, 11) if isDark else QColor(249, 249, 249, 75)
                )
            elif self.isPressed or self.isHover:
                bgColor = (
                    QColor(255, 255, 255, 21) if isDark else QColor(249, 249, 249, 128)
                )
            else:
                bgColor = (
                    QColor(255, 255, 255, 15) if isDark else QColor(243, 243, 243, 194)
                )

        else:
            if not self.isEnabled():
                bgColor = QColor(255, 255, 255, 40) if isDark else QColor(0, 0, 0, 55)
            elif self.isPressed:
                bgColor = (
                    ThemeColor.DARK_2.color() if isDark else ThemeColor.LIGHT_3.color()
                )
            elif self.isHover:
                bgColor = (
                    ThemeColor.DARK_1.color() if isDark else ThemeColor.LIGHT_1.color()
                )
            else:
                bgColor = themeColor()

            borderColor = Qt.transparent
            rect = self.rect()

        painter.setPen(borderColor)
        painter.setBrush(bgColor)

        r = rect.height() / 2
        painter.drawRoundedRect(rect, r, r)


class PillPushButton(TogglePushButton, PillButtonBase):
    """Pill push button

    Constructors
    ------------
    * PillPushButton(`parent`: QWidget = None)
    * PillPushButton(`text`: str, `parent`: QWidget = None,
                     `icon`: QIcon | str | FluentIconBase = None)
    * PillPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
    """

    def paintEvent(self, e):
        PillButtonBase.paintEvent(self, e)
        TogglePushButton.paintEvent(self, e)


class PillToolButton(ToggleToolButton, PillButtonBase):
    """Pill push button

    Constructors
    ------------
    * PillToolButton(`parent`: QWidget = None)
    * PillToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
    """

    def paintEvent(self, e):
        PillButtonBase.paintEvent(self, e)
        ToggleToolButton.paintEvent(self, e)


class TextButtonBase(BackgroundAnimationWidget):
    """Text button base class with 5 color schemes

    Color schemes:
    - information: grey
    - success: green
    - attention: theme color
    - warning: yellow/orange
    - error: red

    Features:
    - Transparent background
    - Only icon and text show different colors based on scheme
    - Text color animation on hover/press
    """

    # Color scheme enum
    INFORMATION = "information"
    SUCCESS = "success"
    ATTENTION = "attention"
    WARNING = "warning"
    ERROR = "error"

    def __init__(self, *args, **kwargs):
        self._colorScheme = self.ATTENTION
        super().__init__(*args, **kwargs)

        # Text color animation
        self.textColorObj = TextColorObject(self)
        self.textColorAni = QPropertyAnimation(self.textColorObj, b"textColor", self)
        self.textColorAni.setDuration(120)
        self._updateTextColor()

    def setColorScheme(self, scheme: str):
        """Set color scheme"""
        self._colorScheme = scheme
        self._updateTextColor()
        self.update()

    def colorScheme(self):
        """Get color scheme"""
        return self._colorScheme

    def _getTextColor(self, isDark, state="normal"):
        """Get text color for current scheme and state"""
        scheme = self._colorScheme

        # Base colors for each scheme
        if scheme == self.INFORMATION:
            normalColor = QColor(119, 119, 119) if isDark else QColor(121, 121, 121)
        elif scheme == self.SUCCESS:
            normalColor = QColor(127, 189, 105) if isDark else QColor(30, 130, 60)
        elif scheme == self.ATTENTION:
            normalColor = themeColor()
        elif scheme == self.WARNING:
            normalColor = QColor(254, 254, 51) if isDark else QColor(157, 93, 0)
        elif scheme == self.ERROR:
            normalColor = QColor(200, 50, 50) if isDark else QColor(200, 50, 50)
        else:
            normalColor = themeColor()

        # Adjust for state
        if state == "hover":
            # Slightly lighter/brighter on hover
            h, s, v, _ = normalColor.getHsvF()
            v = min(v * 1.1, 1.0)
            return QColor.fromHsvF(h, s, v)
        elif state == "pressed":
            # Darker on press
            h, s, v, _ = normalColor.getHsvF()
            v = max(v * 0.85, 0.0)
            return QColor.fromHsvF(h, s, v)
        elif state == "disabled":
            # Grayed out
            return QColor(255, 255, 255, 100) if isDark else QColor(0, 0, 0, 100)

        return normalColor

    def _normalTextColor(self):
        return self._getTextColor(isDarkTheme(), "normal")

    def _hoverTextColor(self):
        return self._getTextColor(isDarkTheme(), "hover")

    def _pressedTextColor(self):
        return self._getTextColor(isDarkTheme(), "pressed")

    def _disabledTextColor(self):
        return self._getTextColor(isDarkTheme(), "disabled")

    def _updateTextColor(self):
        """Update text color based on state"""
        if not self.isEnabled():
            color = self._disabledTextColor()
        elif self.isPressed:
            color = self._pressedTextColor()
        elif self.isHover:
            color = self._hoverTextColor()
        else:
            color = self._normalTextColor()

        self.textColorAni.stop()
        self.textColorAni.setEndValue(color)
        self.textColorAni.start()

    def textColor(self):
        return self.textColorObj.textColor

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """Draw icon with scheme color"""
        color = self.textColor()
        if isinstance(icon, FluentIconBase):
            icon = icon.icon(color=color)
        drawIcon(icon, painter, rect, state)

    def _normalBackgroundColor(self):
        """Transparent background by default"""
        return QColor(0, 0, 0, 0)

    def _hoverBackgroundColor(self):
        """Subtle hover overlay"""
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 9) if isDark else QColor(0, 0, 0, 9)

    def _pressedBackgroundColor(self):
        """Subtle pressed overlay"""
        isDark = isDarkTheme()
        return QColor(255, 255, 255, 6) if isDark else QColor(0, 0, 0, 6)

    def _disabledBackgroundColor(self):
        """Transparent when disabled"""
        return QColor(0, 0, 0, 0)


class TextColorObject(QObject):
    """Text color object for text color animation"""

    def __init__(self, parent):
        super().__init__(parent)
        self._textColor = (
            parent._normalTextColor()
            if hasattr(parent, "_normalTextColor")
            else QColor(0, 0, 0)
        )

    @Property(QColor)
    def textColor(self):
        return self._textColor

    @textColor.setter
    def textColor(self, color: QColor):
        self._textColor = color
        self.parent().update()


class TextPushButton(TextButtonBase, QPushButton):
    """Text push button with colored icon/text

    Constructors
    ------------
    * TextPushButton(`parent`: QWidget = None)
    * TextPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
    * TextPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        FluentStyleSheet.BUTTON.apply(self)
        self.setIconSize(QSize(16, 16))
        self._icon = QIcon()
        setFont(self)

    @__init__.register
    def _(
        self,
        text: str,
        parent: QWidget = None,
        icon: QIcon | str | FluentIconBase = None,
    ):
        self.__init__(parent)
        self.setText(text)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    def setIcon(self, icon: QIcon | str | FluentIconBase):
        if icon is None or (isinstance(icon, QIcon) and icon.isNull()):
            self.setProperty("hasIcon", False)
        else:
            self.setProperty("hasIcon", True)
        self.setStyle(QApplication.style())
        self._icon = icon or QIcon()
        self.update()

    def icon(self):
        return toQIcon(self._icon)

    def minimumSizeHint(self):
        """Return minimum size hint with proper padding"""
        fm = self.fontMetrics()
        textWidth = fm.boundingRect(self.text()).width() if self.text() else 0

        hasIcon = self._icon and not (
            isinstance(self._icon, QIcon) and self._icon.isNull()
        )
        if hasIcon:
            width = 12 + self.iconSize().width() + 8 + textWidth + 12
        else:
            width = textWidth + 24

        height = fm.height() + 11

        return QSize(width, height)

    def _updateBackgroundColor(self):
        # Override to also update text color
        super()._updateBackgroundColor()
        self._updateTextColor()

    def enterEvent(self, e):
        super().enterEvent(e)
        self._updateTextColor()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._updateTextColor()

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self._updateTextColor()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._updateTextColor()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        painter.setFont(self.font())

        # Draw background with animated color
        rect = self.rect().adjusted(1, 1, -1, -1)
        r = 5  # Fixed border-radius like PushButton

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.backgroundColor)
        painter.drawRoundedRect(rect, r, r)

        # Calculate layout
        hasIcon = self._icon and not (
            isinstance(self._icon, QIcon) and self._icon.isNull()
        )
        iconSize = self.iconSize()
        text = self.text()

        # Draw icon
        if hasIcon:
            w, h = iconSize.width(), iconSize.height()
            y = (self.height() - h) / 2

            # Calculate x position
            textWidth = self.fontMetrics().boundingRect(text).width() if text else 0
            totalWidth = w + (8 + textWidth if text else 0)
            x = (self.width() - totalWidth) / 2

            if self.isRightToLeft():
                x = self.width() - w - x

            self._drawIcon(self._icon, painter, QRectF(x, y, w, h))

        # Draw text
        if text:
            color = self.textColor()
            painter.setPen(color)

            if hasIcon:
                iconW = iconSize.width()
                textRect = QRect(
                    int(iconW + 8), 0, int(self.width() - iconW - 16), self.height()
                )
                if self.isRightToLeft():
                    textRect = QRect(
                        8, 0, int(self.width() - iconW - 16), self.height()
                    )
            else:
                textRect = self.rect()

            painter.drawText(textRect, Qt.AlignCenter, text)


class TextToolButton(TextButtonBase, QToolButton):
    """Text tool button with colored icon

    Constructors
    ------------
    * TextToolButton(`parent`: QWidget = None)
    * TextToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        FluentStyleSheet.BUTTON.apply(self)
        self.setIconSize(QSize(16, 16))
        self._icon = QIcon()
        setFont(self)

    @__init__.register
    def _(self, icon: FluentIconBase, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: str, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    def setIcon(self, icon: QIcon | str | FluentIconBase):
        self._icon = icon or QIcon()
        self.update()

    def icon(self):
        return toQIcon(self._icon)

    def _updateBackgroundColor(self):
        super()._updateBackgroundColor()
        self._updateTextColor()

    def enterEvent(self, e):
        super().enterEvent(e)
        self._updateTextColor()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._updateTextColor()

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self._updateTextColor()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._updateTextColor()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # Draw background with animated color
        rect = self.rect().adjusted(1, 1, -1, -1)
        r = 5  # Fixed border-radius

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.backgroundColor)
        painter.drawRoundedRect(rect, r, r)

        # Draw icon centered
        w, h = self.iconSize().width(), self.iconSize().height()
        x = (self.width() - w) / 2
        y = (self.height() - h) / 2
        self._drawIcon(self._icon, painter, QRectF(x, y, w, h))


class _LuminaGlowEffect(QGraphicsDropShadowEffect):
    """Keep the effect's source/cache rectangle stable while its blur animates."""

    def __init__(self, maximumBlur, parent=None):
        self._glowMargin = float(maximumBlur)
        super().__init__(parent)

    def boundingRectFor(self, rect):
        margin = self._glowMargin
        return rect.adjusted(-margin, -margin, margin, margin)


class LuminaPushButton(PushButton):
    """Lumina push button with glowing border effect

    Features:
    - Single-layer background/border drawing (no bottom shadow)
    - Persistent glow effect that expands on hover
    - Background does not change on hover
    - Text and icon color same as PushButton

    Constructors
    ------------
    * LuminaPushButton(`parent`: QWidget = None)
    * LuminaPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
    * LuminaPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
    """

    # Glow blur radius: normal (rest) and hover (expanded range)
    _normalBlur = 25
    _hoverBlur = 45

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Glow effect - always visible, blur radius expands on hover
        self._glowEffect = _LuminaGlowEffect(self._hoverBlur, self)
        self._glowEffect.setOffset(0, 0)
        self._glowEffect.setBlurRadius(LuminaPushButton._normalBlur)
        self._glowColor = QColor(*themeColor().getRgb()[:3], 80)
        self._glowEffect.setColor(self._glowColor)
        self.setGraphicsEffect(self._glowEffect)
        self._customGlowColor = False

        # Animations for glow alpha and blur radius
        self._glowAlphaAni = QPropertyAnimation(self, b"glowAlpha", self)
        self._glowAlphaAni.setDuration(150)
        self._glowBlurAni = QPropertyAnimation(self._glowEffect, b"blurRadius", self)
        self._glowBlurAni.setDuration(150)

        # Update glow color when theme changes
        qconfig.themeChanged.connect(self._updateGlowColor)

    def setGlowColor(self, color: QColor):
        """Set custom glow color

        Parameters
        ----------
        color : QColor
            The glow color (alpha will be managed internally)
        """
        alpha = self._glowColor.alpha()
        self._glowColor = QColor(color.red(), color.green(), color.blue(), alpha)
        self._glowEffect.setColor(self._glowColor)
        self._customGlowColor = True

    def glowColor(self) -> QColor:
        """Get current glow color"""
        return QColor(self._glowColor)

    def getGlowAlpha(self):
        return self._glowColor.alpha()

    def setGlowAlpha(self, alpha: int):
        self._glowColor.setAlpha(int(alpha))
        self._glowEffect.setColor(self._glowColor)

    glowAlpha = Property(int, getGlowAlpha, setGlowAlpha)

    def _updateGlowColor(self):
        if self._customGlowColor:
            return
        color = themeColor()
        alpha = self._glowColor.alpha()
        self._glowColor = QColor(*color.getRgb()[:3], alpha)
        self._glowEffect.setColor(self._glowColor)

    def _animateGlow(self, alpha: int, blur: int):
        """Animate glow alpha and blur radius to target values"""
        self._glowAlphaAni.stop()
        self._glowAlphaAni.setStartValue(self._glowColor.alpha())
        self._glowAlphaAni.setEndValue(alpha)
        self._glowAlphaAni.start()
        self._glowBlurAni.stop()
        self._glowBlurAni.setStartValue(self._glowEffect.blurRadius())
        self._glowBlurAni.setEndValue(blur)
        self._glowBlurAni.start()

    def enterEvent(self, e):
        super().enterEvent(e)
        # Only increase glow if enabled
        if not self.isEnabled():
            return
        # Expand glow range and intensity on hover
        self._animateGlow(200, LuminaPushButton._hoverBlur)

    def leaveEvent(self, e):
        super().leaveEvent(e)
        # Only restore glow if enabled
        if not self.isEnabled():
            return
        # Restore normal glow
        self._animateGlow(80, LuminaPushButton._normalBlur)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        # Only animate if enabled
        if not self.isEnabled():
            return
        # Collapse glow on press
        self._animateGlow(80, LuminaPushButton._normalBlur)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        # Only animate if enabled
        if not self.isEnabled():
            return
        # If still hovering, expand glow again
        if self.isHover:
            self._animateGlow(200, LuminaPushButton._hoverBlur)

    def setEnabled(self, enabled: bool):
        """Override to control glow effect when disabled"""
        super().setEnabled(enabled)
        if enabled:
            # Restore normal glow
            self._animateGlow(80, LuminaPushButton._normalBlur)
        else:
            # Dim glow when disabled
            self._animateGlow(30, LuminaPushButton._normalBlur)

    def setDisabled(self, disabled: bool = True):
        """Set disabled state (convenience method)"""
        self.setEnabled(not disabled)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        painter.setFont(self.font())

        isDark = isDarkTheme()
        rect = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        r = 8

        bgColor = QColor(45, 45, 45) if isDark else QColor(249, 249, 249)

        if isDark:
            borderColor = QColor(255, 255, 255, 50)
        else:
            if not self.isEnabled():
                borderColor = QColor(0, 0, 0, 15)
            else:
                borderColor = (
                    QColor(0, 0, 0, 1) if self.isHover else QColor(0, 0, 0, 15)
                )

        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(rect, r, r)

        painter.setPen(QPen(borderColor, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, r, r)

        if not self.isEnabled():
            painter.setOpacity(0.3628 if isDark else 0.36)
        elif self.isPressed:
            painter.setOpacity(0.786)

        # Draw icon
        hasIcon = (
            hasattr(self, "_icon")
            and self._icon
            and not (isinstance(self._icon, QIcon) and self._icon.isNull())
        )

        if hasIcon:
            w, h = self.iconSize().width(), self.iconSize().height()
            y = (self.height() - h) / 2
            mw = self.minimumSizeHint().width()
            x = 12 + (self.width() - mw) // 2 if mw > 0 else 12
            if self.isRightToLeft():
                x = self.width() - w - x
            self._drawIcon(self._icon, painter, QRectF(x, y, w, h))

        # Draw text
        if self.text():
            if not (not self.isEnabled() or self.isPressed):
                painter.setOpacity(1.0)

            textColor = QColor(255, 255, 255) if isDark else QColor(0, 0, 0)
            painter.setPen(textColor)

            if hasIcon:
                iconW = self.iconSize().width()
                textRect = QRect(
                    int(iconW + 8), 0, int(self.width() - iconW - 16), self.height()
                )
                if self.isRightToLeft():
                    textRect = QRect(
                        8, 0, int(self.width() - iconW - 16), self.height()
                    )
            else:
                textRect = self.rect()

            painter.drawText(textRect, Qt.AlignCenter, self.text())


class Chip(BackgroundAnimationWidget, QWidget):
    """Chip component with close button

    A PushButton-like component with a close button on the right side.

    Signals
    -------
    closed : Signal
        Emitted when the close button is clicked

    Constructors
    ------------
    * Chip(`parent`: QWidget = None)
    * Chip(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
    * Chip(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
    """

    closed = Signal()

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        # Initialize properties before super().__init__()
        self._isChecked = False
        self._text = ""
        self._icon = None

        super().__init__(parent)

        self._closeBtn = RoundToolButton(FIF.CANCEL_MEDIUM, self)
        self._closeBtn.setFixedSize(20, 20)
        self._closeBtn.setIconSize(QSize(10, 10))
        self._closeBtn.setHasBorder(False)
        self._closeBtn.clicked.connect(self.closed.emit)

        qconfig.themeChanged.connect(self._updateCloseBtnIcon)

        FluentStyleSheet.BUTTON.apply(self)
        setFont(self)

        self.setCursor(Qt.PointingHandCursor)

    @__init__.register
    def _(
        self,
        text: str,
        parent: QWidget = None,
        icon: QIcon | str | FluentIconBase = None,
    ):
        self.__init__(parent)
        self._text = text
        self._icon = icon

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    def _normalBackgroundColor(self):
        """Normal background color"""
        isDark = isDarkTheme()
        if self._isChecked:
            return themeColor()
        return QColor(255, 255, 255, 13) if isDark else QColor(249, 249, 249)

    def _hoverBackgroundColor(self):
        """Hover background color"""
        isDark = isDarkTheme()
        if self._isChecked:
            return themeColor()
        return QColor(255, 255, 255, 17) if isDark else QColor(249, 249, 249, 127)

    def _pressedBackgroundColor(self):
        """Pressed background color"""
        isDark = isDarkTheme()
        if self._isChecked:
            return themeColor()
        return QColor(255, 255, 255, 8) if isDark else QColor(249, 249, 249, 76)

    def _updateCloseBtnIcon(self):
        """Update close button icon color on theme change"""
        if self._isChecked:
            self._closeBtn.setIcon(
                FIF.CANCEL_MEDIUM.icon(Theme.LIGHT if isDarkTheme() else Theme.DARK)
            )
        else:
            self._closeBtn.setIcon(
                FIF.CANCEL_MEDIUM.icon(Theme.DARK if isDarkTheme() else Theme.LIGHT)
            )

    def setChecked(self, checked: bool):
        """Set checked state"""
        self._isChecked = checked
        # Update close button icon color
        if self._isChecked:
            self._closeBtn.setIcon(
                FIF.CANCEL_MEDIUM.icon(Theme.LIGHT if isDarkTheme() else Theme.DARK)
            )
        else:
            self._closeBtn.setIcon(
                FIF.CANCEL_MEDIUM.icon(Theme.DARK if isDarkTheme() else Theme.LIGHT)
            )
        # Trigger background animation
        self._updateBackgroundColor()

    def isChecked(self) -> bool:
        """Get checked state"""
        return self._isChecked

    def setText(self, text: str):
        """Set clip text"""
        self._text = text
        self.update()

    def text(self) -> str:
        """Get clip text"""
        return self._text

    def setIcon(self, icon: QIcon | str | FluentIconBase):
        """Set clip icon"""
        self._icon = icon
        self.update()

    def icon(self) -> QIcon:
        """Get clip icon"""
        return toQIcon(self._icon)

    def mouseReleaseEvent(self, e):
        """Toggle checked state on click"""
        super().mouseReleaseEvent(e)
        self.setChecked(not self._isChecked)

    def minimumSizeHint(self):
        """Return minimum size hint"""
        fm = self.fontMetrics()
        textWidth = fm.boundingRect(self._text).width() if self._text else 0

        hasIcon = self._icon and not (
            isinstance(self._icon, QIcon) and self._icon.isNull()
        )
        if hasIcon:
            width = 12 + 16 + 8 + textWidth + 8 + 20 + 8
        else:
            width = 12 + textWidth + 8 + 20 + 8

        height = 33  # Same as PushButton
        return QSize(width, height)

    def sizeHint(self):
        return self.minimumSizeHint()

    def resizeEvent(self, e):
        """Position close button on right side"""
        super().resizeEvent(e)
        self.setFixedHeight(33)
        closeSize = self._closeBtn.size()
        x = self.width() - closeSize.width() - 6
        y = (self.height() - closeSize.height()) // 2
        self._closeBtn.move(x, y)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        painter.setFont(self.font())

        isDark = isDarkTheme()
        rect = self.rect().adjusted(1, 1, -1, -1)
        r = 5

        bgColor = self.backgroundColor

        # Border color
        if self._isChecked:
            borderColor = themeColor()
            textColor = QColor(0, 0, 0) if isDark else QColor(255, 255, 255)
        else:
            borderColor = QColor(255, 255, 255, 20) if isDark else QColor(0, 0, 0, 19)
            textColor = QColor(255, 255, 255) if isDark else QColor(0, 0, 0)

        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(rect, r, r)

        # Draw border
        painter.setPen(QPen(borderColor, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, r, r)

        closeBtnWidth = self._closeBtn.width() + 8
        contentWidth = self.width() - closeBtnWidth

        hasIcon = self._icon and not (
            isinstance(self._icon, QIcon) and self._icon.isNull()
        )

        iconW = 16 if hasIcon else 0
        fm = self.fontMetrics()
        textWidth = fm.boundingRect(self._text).width() if self._text else 0

        minContentWidth = 12 + iconW + (8 if hasIcon else 0) + textWidth + 12

        if contentWidth > minContentWidth:
            startX = (contentWidth - minContentWidth) // 2 + 12
        else:
            startX = 12

        iconW = 0
        if hasIcon:
            iconW = 16
            w, h = iconW, 16
            y = (self.height() - h) / 2
            x = startX
            self._drawIcon(self._icon, painter, QRectF(x, y, w, h), textColor)

        if self._text:
            painter.setOpacity(1.0 if self.isEnabled() else 0.36)
            painter.setPen(textColor)

            if hasIcon:
                textX = startX + iconW + 8
                textRect = QRect(int(textX), 0, int(textWidth + 12), self.height())
            else:
                textRect = QRect(int(startX), 0, int(textWidth + 12), self.height())

            painter.drawText(textRect, Qt.AlignLeft | Qt.AlignVCenter, self._text)

    def _drawIcon(self, icon, painter, rect, textColor=None, state=QIcon.Off):
        """Draw icon with optional color reversal for checked state"""
        if self._isChecked and isinstance(icon, FluentIconBase):
            icon = icon.icon(Theme.LIGHT if isDarkTheme() else Theme.DARK)
        elif not self._isChecked and isinstance(icon, FluentIconBase):
            icon = icon.icon(Theme.DARK if isDarkTheme() else Theme.LIGHT)
        drawIcon(icon, painter, rect, state)


class Tag(QWidget):
    """Tag component for displaying status or category

    A decorative component with border, background, text and optional icon.
    Does not respond to hover, press or click events.

    Constructors
    ------------
    * Tag(`parent`: QWidget = None)
    * Tag(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
    * Tag(`icon`: QIcon | FluentIconBase, `text`: str, `parent`: QWidget = None)
    """

    INFORMATION = "information"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._text = ""
        self._icon = None
        self._type = Tag.INFORMATION
        FluentStyleSheet.BUTTON.apply(self)
        setFont(self)

    @__init__.register
    def _(
        self,
        text: str,
        parent: QWidget = None,
        icon: QIcon | str | FluentIconBase = None,
    ):
        self.__init__(parent)
        self._text = text
        self._icon = icon

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    def setText(self, text: str):
        """Set tag text"""
        self._text = text
        self.update()

    def text(self) -> str:
        """Get tag text"""
        return self._text

    def setIcon(self, icon: QIcon | str | FluentIconBase):
        """Set tag icon"""
        self._icon = icon
        self.update()

    def icon(self) -> QIcon:
        """Get tag icon"""
        return toQIcon(self._icon)

    def setType(self, tagType: str):
        """Set tag type

        Parameters
        ----------
        tagType : str
            Tag type, can be Tag.INFORMATION, Tag.SUCCESS, Tag.WARNING, Tag.ERROR, Tag.PROGRESS
        """
        self._type = tagType
        self.update()

    def type(self) -> str:
        """Get tag type"""
        return self._type

    def _getColors(self):
        """Get colors based on tag type and theme"""
        isDark = isDarkTheme()
        tagType = self._type

        # Color definitions for each type
        if tagType == Tag.INFORMATION:
            bgColor = QColor(40, 40, 40, 200) if isDark else QColor(255, 255, 255)
            borderColor = QColor(255, 255, 255, 80) if isDark else QColor(0, 0, 0, 40)
            textColor = QColor(189, 189, 189) if isDark else QColor(0, 0, 0)

        elif tagType == Tag.SUCCESS:
            bgColor = QColor(22, 35, 18, 254) if isDark else QColor(246, 255, 237, 127)
            borderColor = (
                QColor(104, 207, 86, 180) if isDark else QColor(104, 207, 86, 127)
            )
            textColor = QColor(104, 207, 86) if isDark else QColor(0, 176, 80)

        elif tagType == Tag.WARNING:
            bgColor = QColor(43, 22, 24, 254) if isDark else QColor(255, 242, 204, 127)
            borderColor = (
                QColor(255, 192, 0, 180) if isDark else QColor(255, 192, 0, 127)
            )
            textColor = QColor(255, 192, 0) if isDark else QColor(252, 173, 20)

        elif tagType == Tag.ERROR:
            bgColor = QColor(80, 0, 0, 120) if isDark else QColor(255, 0, 0, 20)
            borderColor = QColor(255, 80, 80, 180) if isDark else QColor(255, 0, 0, 70)
            textColor = QColor(255, 80, 80) if isDark else QColor(255, 0, 0)

        elif tagType == Tag.PROGRESS:
            bgColor = QColor(0, 90, 158, 80) if isDark else QColor(230, 243, 255, 200)
            borderColor = (
                QColor(0, 120, 215, 150) if isDark else QColor(0, 120, 215, 150)
            )
            textColor = QColor(100, 180, 255) if isDark else QColor(0, 90, 158)

        return bgColor, borderColor, textColor

    def minimumSizeHint(self):
        """Return minimum size hint"""
        fm = self.fontMetrics()
        textWidth = fm.boundingRect(self._text).width() if self._text else 0

        hasIcon = self._icon and not (
            isinstance(self._icon, QIcon) and self._icon.isNull()
        )
        if hasIcon:
            width = (
                8 + 16 + 6 + textWidth + 8
            )  # padding + icon + spacing + text + padding
        else:
            width = textWidth + 16  # padding + text + padding

        height = 33  # Fixed height for tag (same as PushButton)
        return QSize(width, height)

    def sizeHint(self):
        return self.minimumSizeHint()

    def resizeEvent(self, e):
        """Set fixed height"""
        super().resizeEvent(e)
        self.setFixedHeight(33)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        painter.setFont(self.font())

        rect = self.rect().adjusted(1, 1, -1, -1)
        r = 5  # Border radius

        # Get colors based on type
        bgColor, borderColor, textColor = self._getColors()

        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(rect, r, r)

        # Draw border
        painter.setPen(QPen(borderColor, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, r, r)

        # Calculate content area
        hasIcon = self._icon and not (
            isinstance(self._icon, QIcon) and self._icon.isNull()
        )

        iconW = 16 if hasIcon else 0
        fm = self.fontMetrics()
        textWidth = fm.boundingRect(self._text).width() if self._text else 0

        startX = 8

        # Draw icon with text color
        if hasIcon:
            iconH = 16
            x = startX
            y = (self.height() - iconH) // 2
            iconRect = QRect(x, y, iconW, iconH)

            if isinstance(self._icon, FluentIconBase):
                # Create icon with text color (color parameter is second arg)
                icon = self._icon.icon(color=textColor)
            else:
                icon = toQIcon(self._icon)

            drawIcon(icon, painter, iconRect)

        # Draw text
        if self._text:
            painter.setOpacity(1.0)
            painter.setPen(textColor)

            if hasIcon:
                textX = startX + iconW + 6
            else:
                textX = startX

            textRect = QRect(int(textX), 0, int(textWidth + 8), self.height())
            painter.drawText(textRect, Qt.AlignLeft | Qt.AlignVCenter, self._text)


class SubClipCloseButton(QPushButton):
    """Close button for SubClip"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("clipCloseButton")

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        # Draw background on hover/press
        isHover = self.underMouse()
        isPressed = self.isDown()

        if isPressed:
            painter.setBrush(
                QColor(255, 255, 255, 11) if isDarkTheme() else QColor(0, 0, 0, 11)
            )
        elif isHover:
            painter.setBrush(
                QColor(255, 255, 255, 20) if isDarkTheme() else QColor(0, 0, 0, 20)
            )
        else:
            painter.setBrush(Qt.NoBrush)

        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 5, 5)

        if isPressed:
            painter.setOpacity(0.6)
        painter.setPen(
            QPen(
                QColor(255, 255, 255, 200) if isDarkTheme() else QColor(0, 0, 0, 180),
                1.5,
            )
        )
        r = QRect(8, 8, 8, 8)
        painter.drawLine(r.topLeft(), r.bottomRight())
        painter.drawLine(r.topRight(), r.bottomLeft())


class SubClip(QWidget):
    """Small removable tag used for selections."""

    closed = Signal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._setUpUi()

    def _setUpUi(self):
        self.setObjectName("subClip")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(24)
        self._isPressed = False

        # Layout - no right margin so close button fits edge
        self.hLayout = QHBoxLayout(self)
        self.hLayout.setContentsMargins(8, 0, 0, 0)
        self.hLayout.setSpacing(4)

        # Text label
        self.textLabel = QLabel(self._text, self)
        self.textLabel.setObjectName("clipTextLabel")
        self.hLayout.addWidget(self.textLabel)

        # Close button
        self.closeButton = SubClipCloseButton(self)
        self.closeButton.clicked.connect(self._onClose)
        self.hLayout.addWidget(self.closeButton)

        # Apply style
        FluentStyleSheet.COMBO_BOX.apply(self)

        self.adjustSize()

    def mousePressEvent(self, e):
        self._isPressed = True
        self.setProperty("isPressed", True)
        self.setStyle(self.style())
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._isPressed = False
        self.setProperty("isPressed", False)
        self.setStyle(self.style())
        super().mouseReleaseEvent(e)

    def _onClose(self):
        self.closed.emit(self._text)

    def text(self) -> str:
        return self._text

    def sizeHint(self):
        return QSize(self.hLayout.totalMinimumSize().width() + 16, 24)
