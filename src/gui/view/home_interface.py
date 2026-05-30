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

        self.galleryLabel = QLabel(f'鸣潮\nWuthering Waves Assistant', self)

        # # 创建阴影效果
        # shadow = QGraphicsDropShadowEffect(self.galleryLabel)
        # shadow.setBlurRadius(20)  # 阴影模糊半径
        # shadow.setColor(QColor("black"))  # 阴影颜色
        # shadow.setOffset(1.2, 1.2)  # 阴影偏移量
        # self.galleryLabel.setGraphicsEffect(shadow)
        # self.galleryLabel.setStyleSheet("color: white;font-size: 30px; font-weight: 600;")

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

        self.mainLayout = QVBoxLayout(self)

        # 顶部 Banner
        self.banner = BannerWidget(self)

        # 中间滚动区域
        self.scrollArea = ScrollArea(self)
        self.view = QWidget(self)
        self.scrollLayout = QVBoxLayout(self.view)

        # 底部固定区域
        self.runView = None

        self.__initWidget()
        self.loadSamples()

    def __initWidget(self):
        self.view.setObjectName('view')
        self.setObjectName('homeInterface')
        # StyleSheet.HOME_INTERFACE.apply(self)

        self.mainLayout.setContentsMargins(0, 0, 0, 36)
        self.mainLayout.setSpacing(10)

        # ScrollArea 设置
        self.scrollArea.setWidget(self.view)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(10)
        self.scrollLayout.setAlignment(Qt.AlignTop)

        # 布局结构
        self.mainLayout.addWidget(self.banner)
        self.mainLayout.addWidget(self.scrollArea, 1)

    def loadSamples(self):
        """ load samples """
        # basic input samples
        basicInputView = SampleCardView(
            self.tr("Basic flow samples"), self.view)
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="自动刷boss",
            content=self.tr(
                "支持任意分辨率，建议1280x720最低画质省电"),
            routeKey="basicInputInterface",
            index=0,
            task_name="AutoBossProcessTask",
            # checked=True,
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="自动拾取",
            content=self.tr("自动拾取路过的声骸、草药、食材、宝箱\n任意分辨率"),
            routeKey="basicInputInterface",
            index=8,
            task_name="AutoPickupProcessTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="沉浸式剧情",
            content=self.tr(
                "剧情党使用，自动选择对话\n解放双手，体验完整人生，任意分辨率"),
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
            title="沿着节拍启航 自动音游",
            content=self.tr(
                "启动脚本，回到游戏点击开始，挂机别动直到结束"),
            routeKey="basicInputInterface",
            index=13,
            task_name="SoarToTheBeatMacroReplayTask",
        )

        from src.util import file_util
        macro_SoarToTheBeat = str(file_util.get_assets_macro_SoarToTheBeat())
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="沿着节拍启航 录制按键",
            content=self.tr(
                "启动脚本，回到游戏点击开始，正常操作即可，快捷键ESC可退出并保存，直接点停止不保存。鼠标悬停显示更多说明"
            ),
            routeKey="basicInputInterface",
            index=14,
            task_name="SoarToTheBeatMacroRecordTask",
            tooltip=self.tr(
                f"保存路径: {macro_SoarToTheBeat}"
                # "将文件重命名为与template目录内歌曲同名，将优先使用你的宏，禁止修改模板文件。"
            )
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="声骸融合",
            content=self.tr(
                "融合背包内未锁定的声骸\n任意分辨率"),
            routeKey="basicInputInterface",
            index=15,
            task_name="EchoMergeProcessTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="每日任务beta",
            content=self.tr(
                "测试中，仅开放部分关卡"),
            routeKey="basicInputInterface",
            index=16,
            task_name="DailyTask",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="施工中...",
            content=self.tr(
                ""),
            routeKey="basicInputInterface",
            index=17,
            task_name="",
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title="施工中...",
            content=self.tr(
                ""),
            routeKey="basicInputInterface",
            index=18,
            task_name="",
        )

        self.scrollLayout.addWidget(basicInputView)

        self.runView = SampleCardView(self.tr("Run"), self)

        runWidget = self.runView.addRun(
            icon=":/gallery/images/controls/ProgressRing.png",
            title="运行",
            content=self.tr(
                ""),
            routeKey="basicInputInterface",
            index=-1
        )

        # 固定在最底部（不在 scrollArea 里）
        self.mainLayout.addWidget(self.runView)

        for card in basicInputView.card_group:
            card.task_selected.connect(runWidget.update_task) # 连接信号

