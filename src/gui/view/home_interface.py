# coding:utf-8
import json

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPainterPath, QLinearGradient, QFont, QPalette
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect, QGraphicsTextItem, \
    QGraphicsScene, QGraphicsView, QGraphicsOpacityEffect

from qfluentwidgets import ScrollArea, isDarkTheme, FluentIcon
from ..common.config import cfg, HELP_URL, REPO_URL, EXAMPLE_URL, FEEDBACK_URL
from ..common.icon import Icon, FluentIconBase
from ..components.sample_card import SampleCardView
from ..common.style_sheet import StyleSheet


class BannerWidget(QWidget):
    """ Banner widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.setFixedHeight(336)
        self.setFixedHeight(130)

        self.vBoxLayout = QVBoxLayout(self)

        # self.galleryLabel = QLabel(f'鸣潮 2.2.0', self)
        self.galleryLabel = QLabel(f'鸣潮 2.2.0\nWuthering Waves Assistant Alpha', self)

        # # 创建阴影效果 TODO 不生效，Qt5有用
        # shadow = QGraphicsDropShadowEffect()
        # shadow.setBlurRadius(20)  # 阴影模糊半径
        # shadow.setColor(QColor("black"))  # 阴影颜色
        # shadow.setOffset(1.2, 1.2)  # 阴影偏移量
        # self.galleryLabel.setGraphicsEffect(shadow)

        # self.banner = QPixmap(':/gallery/images/header1.png')

        self.galleryLabel.setObjectName('galleryLabel')

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(30, 30, 0, 0)
        self.vBoxLayout.addWidget(self.galleryLabel)
        self.vBoxLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    # def paintEvent(self, e):
    #     super().paintEvent(e)
    #     painter = QPainter(self)
    #     painter.setRenderHints(
    #         QPainter.SmoothPixmapTransform | QPainter.Antialiasing)
    #     painter.setPen(Qt.NoPen)
    #
    #     path = QPainterPath()
    #     path.setFillRule(Qt.WindingFill)
    #     w, h = self.width(), self.height()
    #     path.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
    #     path.addRect(QRectF(0, h-50, 50, 50))
    #     path.addRect(QRectF(w-50, 0, 50, 50))
    #     path.addRect(QRectF(w-50, h-50, 50, 50))
    #     path = path.simplified()
    #
    #     # init linear gradient effect
    #     gradient = QLinearGradient(0, 0, 0, h)
    #
    #     # draw background color
    #     if not isDarkTheme():
    #         gradient.setColorAt(0, QColor(207, 216, 228, 255))
    #         gradient.setColorAt(1, QColor(207, 216, 228, 0))
    #     else:
    #         gradient.setColorAt(0, QColor(0, 0, 0, 255))
    #         gradient.setColorAt(1, QColor(0, 0, 0, 0))
    #
    #     painter.fillPath(path, QBrush(gradient))
    #
    #     # # draw banner image
    #     # pixmap = self.banner.scaled(
    #     #     self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    #     # painter.fillPath(path, QBrush(pixmap))


class HomeInterface(ScrollArea):
    """ Home interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        StyleSheet.HOME_INTERFACE.apply(self)
        self.banner = BannerWidget(self)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.__initWidget()
        self.loadSamples()

    def __initWidget(self):
        self.view.setObjectName('view')
        self.setObjectName('homeInterface')
        # StyleSheet.HOME_INTERFACE.apply(self)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 36)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.addWidget(self.banner)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

    def loadSamples(self):
        """ load samples """
        # basic input samples
        basicInputView = SampleCardView(
            self.tr("Basic flow samples"), self.view)
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="自动刷boss",
            content=self.tr(
                "旧版迁移的功能，老用户将原config.yaml覆盖到启动目录即可，后续会做全自动连招，支持1280x720，最低画质"),
            routeKey="basicInputInterface",
            index=0,
            task_name="AutoBossProcessTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="自动拾取",
            content=self.tr("自动拾取路过的声骸、草药、食材、宝箱\n任意分辨率，建议最低画质（窗口化），60fps，开DLSS"),
            routeKey="basicInputInterface",
            index=8,
            task_name="AutoPickupProcessTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="沉浸式剧情（推荐）",
            content=self.tr(
                "自动选择对话，解放双手，体验完整人生\n任意分辨率，建议全屏最高画质"),
            routeKey="basicInputInterface",
            index=9,
            task_name="AutoStoryEnjoyProcessTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="跳过剧情",
            content=self.tr(
                "SKIP，SKIP，SKIP，跳过赛博人生\n任意分辨率"),
            routeKey="basicInputInterface",
            index=10,
            task_name="AutoStorySkipProcessTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="每日任务 完成一半",
            content=self.tr(
                "自动完成每日活跃度任务，领取奖励"),
            routeKey="basicInputInterface",
            index=13,
            task_name="DailyActivityProcessTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="刷体力 完成一半",
            content=self.tr(
                "刷无音区、材料本"),
            routeKey="basicInputInterface",
            index=14,
            task_name="DailyActivityProcessTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="背包声骸锁定，未迁移，优先级低",
            content=self.tr(
                "配置需要的声骸属性，自动将背包内符合的声骸上锁"),
            routeKey="basicInputInterface",
            index=15,
            task_name="",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="声骸合成五合一，不迁移，会做一百的",
            content=self.tr(
                "合成声骸，自动锁定需要的声骸"),
            routeKey="basicInputInterface",
            index=16,
            task_name="",
        )
        self.vBoxLayout.addWidget(basicInputView)

        runView = SampleCardView(
            self.tr("Run"), self.view)
        runWidget = runView.addRun(
            icon=":/gallery/images/controls/ProgressRing.png",
            title="运行",
            content=self.tr(
                ""),
            routeKey="basicInputInterface",
            index=-1
        )
        self.vBoxLayout.addWidget(runView)

        for card in basicInputView.card_group:
            card.task_selected.connect(runWidget.update_task) # 连接信号

