import logging
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal, QSize, QEvent, QCoreApplication
from PySide6.QtGui import QIcon, QColor, QIntValidator
from PySide6.QtWidgets import (QWidget, QLabel, QFileDialog, QFrame, QVBoxLayout, QButtonGroup, QHBoxLayout,
                               QPushButton, QApplication, QSizePolicy, QFormLayout, QCheckBox, QGridLayout)
from qfluentwidgets import (FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition,
                            InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit, InfoBar,
                            SettingCardGroup, ScrollArea, ExpandLayout, ExpandSettingCard, FluentIconBase,
                            OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
                            SingleDirectionScrollArea, PrimaryPushButton, FluentStyleSheet,
                            LineEdit, SettingCard, ComboBox, ConfigItem,
                            PushButton, ToolButton, MessageBox, SearchLineEdit, TransparentPushButton, ToggleToolButton,
                            DropDownPushButton, TogglePushButton, ToolTipFilter)

from src.core.enemy import EnemyVersion
from src.gui.common.config import paramConfig, BossNameEnum
from src.gui.common.globals import globalParam, globalSignal
from src.gui.common.style_sheet import StyleSheet
from src.gui.common.task import BaseTask, ValidationResult, TaskId
from src.gui.components.check_box import CheckCard
from src.gui.components.widgets.exclusive_filter import ExclusiveLiteFilter

logger = logging.getLogger(__name__)


@dataclass
class QEnemy:
    id: BossNameEnum
    name: str
    version: EnemyVersion
    background: bool
    enable: bool


class EchoTask(BaseTask):

    def __init__(self, id: str, name: str, widget):
        super().__init__(id, name)
        self.widget = widget

    def validate(self, **kwargs) -> ValidationResult:
        return ValidationResult(success=True)

    def submitTask(self, start: bool):
        if start:
            result = self.validate()
            if result.success:
                self._createTopRightInfoBar(self.tr('Task: '), self.name, 5000)
                self.submit(start)
            return result
        self.submit(start)
        return None

    def _createTopRightInfoBar(self, title: str, content: str, duration: int):
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self.widget.parent()
        )


class BossRushTask(EchoTask):

    def __init__(self, widget):
        super().__init__(TaskId.AutoBossProcessTask, "BossRush", widget)

    def validate(self, **kwargs) -> ValidationResult:
        context = self.__class__.__name__
        try:
            # logger.debug(f"paramConfig: {paramConfig.toDict}")
            if not paramConfig.bossName.value:
                return ValidationResult(
                    success=False,
                    message=QCoreApplication.translate(context, "未选择boss")
                )
            return ValidationResult(success=True)
        except Exception as e:
            logger.error(e)
        return ValidationResult(
            success=False,
            message=QCoreApplication.translate(context, "参数异常")
        )

    def submitTask(self, start: bool):
        if start:
            result = self.validate()
            if result.success:
                msg = str([x.value for x in paramConfig.bossName.value])
                self._createTopRightInfoBar(self.tr('Boss: '), msg, 5000)
                self.submit(start)
            return result
        self.submit(start)
        return None


class BossRushWidget(QWidget):
    enemyChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.task = BossRushTask(self)

        self.latestVersion = EnemyVersion.V3_7
        self.enemyList = [
            QEnemy(
                id=BossNameEnum.SuhsinTheInevitable,
                name=self.tr("Suhsin the Inevitable"),
                version=EnemyVersion.V3_7,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.CalamityEffigy,
                name=self.tr("Calamity Effigy"),
                version=EnemyVersion.V3_6,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.ThousandPuppetPavilion,
                name=self.tr("Thousand-Puppet Pavilion"),
                version=EnemyVersion.V3_5,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.MyriadSnareRustfireChassis,
                name=self.tr("Myriad Snare: Rustfire Chassis"),
                version=EnemyVersion.V3_5,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareAdamSmasher,
                name=self.tr("Nightmare: Adam Smasher"),
                version=EnemyVersion.V3_4,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Denia,
                name=self.tr("Denia"),
                version=EnemyVersion.V3_3,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NamelessExplorer,
                name=self.tr("Nameless Explorer"),
                version=EnemyVersion.V3_1,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Sigillum,
                name=self.tr("Sigillum"),
                version=EnemyVersion.V3_1,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.ReactorHusk,
                name=self.tr("Reactor Husk"),
                version=EnemyVersion.V3_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Hyvatia,
                name=self.tr("Hyvatia"),
                version=EnemyVersion.V3_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.ThrenodianLeviathan,
                name=self.tr("Threnodian: Leviathan"),
                version=EnemyVersion.V2_7,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.TheFalseSovereign,
                name=self.tr("The False Sovereign"),
                version=EnemyVersion.V2_6,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.LadyOfTheSea,
                name=self.tr("Lady of the Sea"),
                version=EnemyVersion.V2_6,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Fenrico,
                name=self.tr("Fenrico"),
                version=EnemyVersion.V2_5,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareHecate,
                name=self.tr("Nightmare: Hecate"),
                version=EnemyVersion.V2_5,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.LionessOfGlory,
                name=self.tr("Lioness of Glory"),
                version=EnemyVersion.V2_4,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareKelpie,
                name=self.tr("Nightmare: Kelpie"),
                version=EnemyVersion.V2_4,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Fleurdelys,
                name=self.tr("Fleurdelys"),
                version=EnemyVersion.V2_2,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareLampylumenMyriad,
                name=self.tr("Nightmare: Lampylumen Myriad"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareMourningAix,
                name=self.tr("Nightmare: Mourning Aix"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareInfernoRider,
                name=self.tr("Nightmare: Inferno Rider"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareCrownless,
                name=self.tr("Nightmare: Crownless"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareThunderingMephis,
                name=self.tr("Nightmare: Thundering Mephis"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareTempestMephis,
                name=self.tr("Nightmare: Tempest Mephis"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareImpermanenceHeron,
                name=self.tr("Nightmare: Impermanence Heron"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.NightmareFeilianBeringal,
                name=self.tr("Nightmare: Feilian Beringal"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.DragonOfDirge,
                name=self.tr("Dragon of Dirge"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Lorelei,
                name=self.tr("Lorelei"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Hecate,
                name=self.tr("Hecate"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.SentryConstruct,
                name=self.tr("Sentry Construct"),
                version=EnemyVersion.V2_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.FallacyOfNoReturn,
                name=self.tr("Fallacy of No Return"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Jue,
                name=self.tr("Jué"),
                version=EnemyVersion.V1_1,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Crownless,
                name=self.tr("Crownless"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.FeilianBeringal,
                name=self.tr("Feilian Beringal"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.TempestMephis,
                name=self.tr("Tempest Mephis"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.ThunderingMephis,
                name=self.tr("Thundering Mephis"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.MourningAix,
                name=self.tr("Mourning Aix"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.MechAbomination,
                name=self.tr("Mech Abomination"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.ImpermanenceHeron,
                name=self.tr("Impermanence Heron"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.InfernoRider,
                name=self.tr("Inferno Rider"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.BellBorneGeochelone,
                name=self.tr("Bell-Borne Geochelone"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.LampylumenMyriad,
                name=self.tr("Lampylumen Myriad"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
            QEnemy(
                id=BossNameEnum.Dreamless,
                name=self.tr("Dreamless"),
                version=EnemyVersion.V1_0,
                background=False,
                enable=True,
            ),
        ]
        self.enemyIdMapping = {i.id: i for i in self.enemyList}

        self.mainLayout = QVBoxLayout(self)

        self.flowLayout = FlowLayout(isTight=True)
        self.enemyGroup = QButtonGroup(self)
        self.enemyGroup.setExclusive(True)

        self.toolbarLayout = QHBoxLayout()
        self.searchEdit = SearchLineEdit(self)
        self.searchEdit.setPlaceholderText(self.tr("Search"))
        self.searchEdit.setClearButtonEnabled(True)
        self.enemyFilter = ExclusiveLiteFilter()
        self.enemyFilter.addItems(['All', '3.0', '2.0', '1.0'])

        self.aboutButton = PushButton(self.tr("About"), self)

        self.checkCards: dict[BossNameEnum, CheckCard] = {}
        for item in self.enemyList:
            if not item.enable:
                continue
            checkCard = CheckCard(item.name, parent=self)
            checkCard.setChecked(False)
            if item.background or self.latestVersion == item.version:
                checkCard.setBackground()
            checkCard.setProperty("boss", item.id)
            self.checkCards[item.id] = checkCard

        self.__initWidget()

    def __initWidget(self):
        # initialize style sheet
        self.setObjectName('view')
        # StyleSheet.PARAM_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        self.searchEdit.setMaximumWidth(300)

        self.toolbarLayout.addWidget(self.searchEdit)
        self.toolbarLayout.addSpacing(15)
        self.toolbarLayout.addWidget(self.enemyFilter)
        self.toolbarLayout.addWidget(self.aboutButton)
        self.toolbarLayout.addStretch()
        self.toolbarLayout.setContentsMargins(0, 0, 0, 0)

        for checkCard in self.checkCards.values():
            self.enemyGroup.addButton(checkCard.checkbox)
            self.flowLayout.addWidget(checkCard)
        self.flowLayout.setSpacing(0)
        self.flowLayout.setContentsMargins(0, 10, 0, 10)

        self.mainLayout.addLayout(self.toolbarLayout)
        # self.mainLayout.addWidget(self.enemyFilter)
        self.mainLayout.addLayout(self.flowLayout)
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(16, 10, 16, 10)

    def __connectSignalToSlot(self):
        for boss, card in self.checkCards.items():
            card.stateChanged.connect(lambda state, cb=card: self.__onCardStateChanged(cb, state))

        self.aboutButton.clicked.connect(self.__showAboutFlyout)

        self.enemyFilter.currentTextChanged.connect(self.__onEnemyFilterChanged)

        self.searchEdit.textChanged.connect(self.__onTextChanged)
        self.searchEdit.searchSignal.connect(self.__onTextChanged)
        self.searchEdit.clearSignal.connect(self.__onClear)

    def __loadConfig(self):
        value = paramConfig.get(paramConfig.bossName)
        # logger.warning(f"{value}")
        if value and len(value) > 0 and self.checkCards.get(value[0]) is not None:
            card = self.checkCards.get(value[0])
        else:
            card = self.checkCards.get(BossNameEnum.Dreamless)
        card.blockSignals(True)
        card.setChecked(True)
        card.blockSignals(False)

    def __onCardStateChanged(self, cb, state):
        logger.debug(f"checkbox: {cb.checkbox.text()}, isChecked: {cb.checkbox.isChecked()}")
        enemyId = cb.property("boss")
        paramConfig.set(paramConfig.bossName, [enemyId])
        self.enemyChanged.emit(self.enemyIdMapping.get(enemyId).name or '')

    def __onEnemyFilterChanged(self, text: str):
        logger.debug(f"__onEnemyFilterChanged: {text}")
        if not text or text == "All":
            for id, card in self.checkCards.items():
                card.setVisible(True)
        else:
            for id, card in self.checkCards.items():
                enemy = self.enemyIdMapping.get(id)
                if text == "1.0":
                    card.setVisible(enemy.version.is_v1())
                    continue
                if text == "2.0":
                    card.setVisible(enemy.version.is_v2())
                    continue
                if text == "3.0":
                    card.setVisible(enemy.version.is_v3())
                    continue
                card.setVisible(True)
        self.__refreshFlowlayout()

    def __onTextChanged(self, text: str):
        logger.debug(f"__onTextChanged: {text}")
        if not text:
            if self.enemyFilter.currentItem() == "All":
                self.__onEnemyFilterChanged("All")
            else:
                self.enemyFilter.setCurrentItem("All")
            return
        keyword = text.strip().lower()
        for id, card in self.checkCards.items():
            enemy = self.enemyIdMapping.get(id)
            if enemy is None or not enemy.enable or not enemy.name:
                continue
            card.setVisible(keyword in enemy.name.lower())
        self.__refreshFlowlayout()

    def __onClear(self):
        if self.enemyFilter.currentItem() == "All":
            self.__onEnemyFilterChanged("All")
        else:
            self.enemyFilter.setCurrentItem("All")

    def __showAboutFlyout(self):
        texts = [
            self.tr("任意配队，人数不限，建议带奶，建议1280x720最低画质挂机还省电。"),
            self.tr("若游戏内没有1280x720分辨率选项，或修改后游戏微闪一下没有反应，这是游戏的问题，换成其他修改后有效的小分辨率，如1600x900。"),
            self.tr("萌新建议降低索拉等级刷梦魇boss，通过5合1获取1c3c。"),
        ]
        Flyout.create(
            # icon=InfoBarIcon.INFORMATION,
            title=self.tr('About:'),
            content="\n".join(texts),
            target=self.aboutButton,
            parent=self.window()
        )

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.__refreshFlowlayout()

    def __refreshFlowlayout(self):
        self.flowLayout.invalidate()
        self.flowLayout.activate()


class EchoMergeTask(EchoTask):

    def __init__(self, widget):
        super().__init__(TaskId.EchoMergeProcessTask, "EchoMerge", widget)


class EchoMergeWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.task = EchoMergeTask(self)

        self.mainLayout = QVBoxLayout(self)

        # self.checkbox = CheckBox(self.tr("声骸融合: "), self)
        self.descLabel = QLabel(self.tr("Fuse unlocked Echoes in the inventory, any resolution"), self)
        self.descLabel.setWordWrap(True)

        self.descLayout = QHBoxLayout()
        self.descLayout.addWidget(self.descLabel)
        self.descLayout.setContentsMargins(16, 0, 0, 0)

        # self.mainLayout.addWidget(self.checkbox)
        self.mainLayout.addLayout(self.descLayout)


class EchoWidget(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.container = QWidget(self)
        self.mainLayout = QVBoxLayout(self.container)

        self.tipsLabel = QLabel(self.tr("Please select the features you want to use."), self.container)

        self.bossRushLayout = QHBoxLayout()
        self.bossRushCheckBox = CheckBox(self.tr("Boss Farming:"), self.container)
        self.bossRushCheckBox.setChecked(True)
        self.bossNameLabel = QLabel(self.container)

        self.bossRushWidget = BossRushWidget(self.container)

        self.echoMergeCheckBox = CheckBox(self.tr("Echo Fusion:"), self.container)
        self.echoMergeWidget = EchoMergeWidget(self.container)

        self.group = QButtonGroup(self.container)
        self.group.setExclusive(True)
        self.group.addButton(self.bossRushCheckBox)
        self.group.addButton(self.echoMergeCheckBox)

        self.__initWidget()

        self.currentTask = self.bossRushWidget.task

    def __initWidget(self):
        # self.resize(1000, 800)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        # self.setObjectName('paramInterface')

        # initialize style sheet
        self.bossRushCheckBox.setObjectName("titleCheckBox")
        self.echoMergeCheckBox.setObjectName("titleCheckBox")
        self.container.setObjectName('view')
        StyleSheet.HOME_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        self.bossRushLayout.addWidget(self.bossRushCheckBox)
        self.bossRushLayout.addSpacing(2)
        self.bossRushLayout.addWidget(self.bossNameLabel)
        self.bossRushLayout.addStretch()

        self.mainLayout.addWidget(self.tipsLabel)
        self.mainLayout.addSpacing(20)
        self.mainLayout.addLayout(self.bossRushLayout)
        self.mainLayout.addWidget(self.bossRushWidget)
        self.mainLayout.addWidget(self.echoMergeCheckBox)
        self.mainLayout.addWidget(self.echoMergeWidget)
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(16, 10, 16, 10)

    def __connectSignalToSlot(self):
        self.bossRushCheckBox.stateChanged.connect(
            lambda _: self.__onTaskChecked(self.bossRushCheckBox, self.bossRushWidget.task))
        self.echoMergeCheckBox.stateChanged.connect(
            lambda _: self.__onTaskChecked(self.echoMergeCheckBox, self.echoMergeWidget.task))

        self.bossRushWidget.enemyChanged.connect(lambda enemyName: self.bossNameLabel.setText(enemyName))

    def __onTaskChecked(self, checkbox, currentTask):
        # logger.debug(f"echo __onTaskChecked: {checkbox.isChecked()}, {currentTask}")
        if checkbox.isChecked():
            self.currentTask = currentTask
            globalSignal.taskChangedSignal.emit(currentTask)
            # logger.debug(f"Current task: {self.currentTask}")

    def __loadConfig(self):
        enemyIdList = paramConfig.get(paramConfig.bossName)
        if enemyIdList and (enemy := self.bossRushWidget.enemyIdMapping.get(enemyIdList[0])) and enemy.name:
            self.bossNameLabel.setText(enemy.name)
