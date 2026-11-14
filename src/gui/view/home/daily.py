import logging
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize, QEvent, QCoreApplication
from PySide6.QtGui import QIcon, QColor, QIntValidator
from PySide6.QtWidgets import (QWidget, QLabel, QFileDialog, QFrame, QVBoxLayout, QButtonGroup, QHBoxLayout,
                               QPushButton, QApplication, QSizePolicy, QFormLayout, QCheckBox, QGridLayout,
                               QGraphicsDropShadowEffect)
from qfluentwidgets import (FluentIcon as FIF, OptionsSettingCard, SwitchSettingCard, SwitchButton, IndicatorPosition,
                            InfoBarPosition, FlowLayout, FluentIcon, Flyout, InfoBarIcon, ListWidget, TextEdit, InfoBar,
                            SettingCardGroup, ScrollArea, ExpandLayout, ExpandSettingCard, FluentIconBase,
                            OptionsConfigItem, CheckBox, ExpandGroupSettingCard, RadioButton, MaskDialogBase,
                            SingleDirectionScrollArea, PrimaryPushButton, FluentStyleSheet,
                            LineEdit, SettingCard, ComboBox, ConfigItem,
                            PushButton, ToolButton, MessageBox, ToggleToolButton)

from src.core.i18n import I18nText
from src.core.resonator import Resonator
from src.core.resource import Resource
from src.gui.common.config import paramConfig
from src.gui.common.globals import globalParam, globalSignal
from src.gui.common.style_sheet import StyleSheet
from src.gui.common.task import TaskId, BaseTask, ValidationResult
from src.gui.components.widgets.combo_box import MultiSelectionComboBox

logger = logging.getLogger(__name__)


@dataclass
class QForgeryChallenge:
    """副本参数，字段都用于页面翻译展示用，逻辑相关应使用id获取dungeon对象处理"""
    id: str
    name: str
    region: str
    reward: str
    weapon: str
    enable: bool


@dataclass
class QBossChallenge:
    id: str
    name: str
    region: str
    reward: str
    enable: bool


@dataclass
class QTacetSuppression:
    id: str
    name: str
    region: str
    rewards: list[str]
    enable: bool


@dataclass
class QWeeklyChallenge:
    id: str
    name: str
    enemy: str
    region: str
    reward: str
    enable: bool


@dataclass
class QTacetDiscordNest:
    id: str
    name: str
    region_id: str
    region: str
    rewards: list[str]
    enable: bool


@dataclass
class QNightmarePurification:
    id: str
    name: str
    rewards: list[str]
    enable: bool


@dataclass
class QResonator:
    id: str
    name: str
    weeklyChallenge: str
    tacetSuppression: list[str]
    forgeryChallenge: list[str]
    bossChallenge: str
    gather: str
    tacetDiscordNest: list[str]
    nightmarePurification: list[str]
    enable: bool


class ElidedMultiSelectionComboBox(MultiSelectionComboBox):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # 关键：让布局忽略按钮的 sizeHint，宽度完全由外部布局决定。
        # 这样 setText 再长也不会把按钮撑开；动态宽度由父布局控制。
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

    def _updateDisplayText(self):
        """文本模式下按当前宽度做省略显示"""
        if not self._selectedIndices:
            self._updateTextState(True)
            self.setText(self._placeholderText or "")
            return

        self._updateTextState(False)
        full = ", ".join(self.selectedTexts())

        fm = self.fontMetrics()
        # 右侧箭头画在 width()-22 处、宽 10，留 30 左右空间即可
        avail = max(0, self.width() - 50)
        self.setText(fm.elidedText(full, Qt.ElideRight, avail))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_selectedIndices"):
            self._updateDisplay()


class DailyTask(BaseTask):

    def __init__(self, widget):
        super().__init__(TaskId.DailyTask, "DailyTask")
        self.widget = widget

    def validate(self, **kwargs) -> ValidationResult:
        return ValidationResult(success=True)

    def submitTask(self, start: bool):
        if start:
            result = self.validate()
            if result.success:
                # msg = str([x.value for x in paramConfig.bossName.value])
                # self.__createTopRightInfoBar(self.tr('Boss Rush: '), msg, 5000)
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


class DailyWidget(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__initData()
        self.task = DailyTask(self)

        self.container = QWidget(self)
        self.mainLayout = QVBoxLayout(self.container)

        self.waveplateLabel = QLabel(self.tr("Waveplates:"), self.container)
        self.nestLabel = QLabel(self.tr("Nest:"), self.container)
        self.claimRewardsLabel = QLabel(self.tr("Claim Rewards:"), self.container)

        self.upLabels = []
        self.bountifulCrescendo = []
        self.chordCleansing = []

        self.gridLayout = QGridLayout()
        self.__initGridLayout()

        self.contentBottomLayout = QHBoxLayout()
        self.resetButton = PushButton(self.tr("Reset"), self.container)
        self.aboutButton = PushButton(self.tr('About'), self.container)

        self.__initWidget()

        self.currentTask = self.task

    def __initData(self):
        #------- 通用参数 -------

        # 地区
        self.mengzhou = self.tr("Mengzhou")
        self.lahaiRoi = self.tr("Lahai-Roi")
        self.rinascita = self.tr("Rinascita")
        self.theBlackShores = self.tr("The Black Shores")
        self.jinzhou = self.tr("Jinzhou")

        # 武器
        self.sword = self.tr('Sword')
        self.rectifier = self.tr('Rectifier')
        self.broadblade = self.tr('Broadblade')
        self.gauntlets = self.tr('Gauntlets')
        self.pistols = self.tr('Pistols')

        #------- 副本参数，新的在前 -------

        # 周本
        self.weeklyChallengeList = [
            QWeeklyChallenge(
                id=I18nText.OrdinanceOfTheInevitable,
                name=self.tr("Ordinance of the Inevitable"),
                enemy=self.tr("Suhsin the Inevitable"),
                region=self.mengzhou,
                reward=self.tr("Remnant of the Wheel"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.CourtOfShackledSouls,
                name=self.tr("Court of Shackled Souls"),
                enemy=self.tr("Thousand-Puppet Pavilion"),
                region=self.mengzhou,
                reward=self.tr("Skyward Glazed Heart"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.SeedOfIllusoryOrigin,
                name=self.tr("Seed of Illusory Origin"),
                enemy=self.tr("Denia"),
                region=self.lahaiRoi,
                reward=self.tr("We Who Question"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.GateOfTheLostStar,
                name=self.tr("Gate of the Lost Star"),
                enemy=self.tr("Sigillum"),
                region=self.lahaiRoi,
                reward=self.tr("Gold in Memory"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.CinderniteApocalypse,
                name=self.tr("Cindernite Apocalypse"),
                enemy=self.tr("Threnodian: Leviathan"),
                region=self.rinascita,
                reward=self.tr("Curse of the Abyss"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.TheWheelOfBrokenFate,
                name=self.tr("The Wheel of Broken Fate"),
                enemy=self.tr("Fleurdelys"),
                region=self.rinascita,
                reward=self.tr("When Irises Bloom"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.BeyondTheCrimsonCurtain,
                name=self.tr("Beyond the Crimson Curtain"),
                enemy=self.tr("Hecate"),
                region=self.rinascita,
                reward=self.tr("The Netherworld's Stare"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.TheFatedConfrontation,
                name=self.tr("The Fated Confrontation"),
                enemy=self.tr("Jué"),
                region=self.jinzhou,
                reward=self.tr("Sentinel's Dagger"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.StatueOfTheCrownless,
                name=self.tr("Statue of the Crownless"),
                enemy=self.tr("Dreamless"),
                region=self.jinzhou,
                reward=self.tr("Dreamless Feather"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.ChaoticJuncture,
                name=self.tr("Chaotic Juncture"),
                enemy=self.tr("Scar"),
                region=self.jinzhou,
                reward=self.tr("Unending Destruction"),
                enable=True,
            ),
            QWeeklyChallenge(
                id=I18nText.BellOfArchaicChants,
                name=self.tr("Bell of Archaic Chants"),
                enemy=self.tr("Bell-Borne Geochelone"),
                region=self.jinzhou,
                reward=self.tr("Monument Bell"),
                enable=True,
            ),
        ]

        # 武器、角色升级素材
        self.forgeryChallengeList = [
            QForgeryChallenge(
                id=I18nText.WingfallChasm,
                name=self.tr("Wingfall Chasm"),
                region=self.mengzhou,
                reward=self.tr("Polarizer"),
                weapon=self.sword,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.SilentChasm,
                name=self.tr("Silent Chasm"),
                region=self.mengzhou,
                reward=self.tr("String"),
                weapon=self.rectifier,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.SplitChasm,
                name=self.tr("Split Chasm"),
                region=self.mengzhou,
                reward=self.tr("Carved Crystal"),
                weapon=self.broadblade,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.ErodedChasm,
                name=self.tr("Eroded Chasm"),
                region=self.mengzhou,
                reward=self.tr("Waveworn Shard"),
                weapon=self.gauntlets,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.AshenChasm,
                name=self.tr("Ashen Chasm"),
                region=self.mengzhou,
                reward=self.tr("Combustor"),
                weapon=self.pistols,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.FallenSanctum,
                name=self.tr("Fallen Sanctum"),
                region=self.lahaiRoi,
                reward=self.tr("Polarizer"),
                weapon=self.sword,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.LessonInSunset,
                name=self.tr("Lesson in Sunset"),
                region=self.lahaiRoi,
                reward=self.tr("String"),
                weapon=self.rectifier,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.StrickenSanctum,
                name=self.tr("Stricken Sanctum"),
                region=self.lahaiRoi,
                reward=self.tr("Carved Crystal"),
                weapon=self.broadblade,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.LessonInVoid,
                name=self.tr("Lesson in Void"),
                region=self.lahaiRoi,
                reward=self.tr("Waveworn Shard"),
                weapon=self.gauntlets,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.LessonInEmbers,
                name=self.tr("Lesson in Embers"),
                region=self.lahaiRoi,
                reward=self.tr("Combustor"),
                weapon=self.pistols,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.GardenOfSalvation,
                name=self.tr("Garden of Salvation"),
                region=self.rinascita,
                reward=self.tr("Metallic Drip"),
                weapon=self.sword,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.AbyssOfInitiation,
                name=self.tr("Abyss of Initiation"),
                region=self.rinascita,
                reward=self.tr("Helix"),
                weapon=self.rectifier,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.GardenOfAdoration,
                name=self.tr("Garden of Adoration"),
                region=self.rinascita,
                reward=self.tr("Waveworn Residue"),
                weapon=self.broadblade,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.AbyssOfSacrifice,
                name=self.tr("Abyss of Sacrifice"),
                region=self.rinascita,
                reward=self.tr("Cadence"),
                weapon=self.gauntlets,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.AbyssOfConfession,
                name=self.tr("Abyss of Confession"),
                region=self.rinascita,
                reward=self.tr("Phlogiston"),
                weapon=self.pistols,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.FlamingRemnants,
                name=self.tr("Flaming Remnants"),
                region=self.jinzhou,
                reward=self.tr("Metallic Drip"),
                weapon=self.sword,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.MistyForest,
                name=self.tr("Misty Forest"),
                region=self.jinzhou,
                reward=self.tr("Helix"),
                weapon=self.rectifier,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.ErodedRuins,
                name=self.tr("Eroded Ruins"),
                region=self.jinzhou,
                reward=self.tr("Waveworn Residue"),
                weapon=self.broadblade,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.MoonlitGroves,
                name=self.tr("Moonlit Groves"),
                region=self.jinzhou,
                reward=self.tr("Cadence"),
                weapon=self.gauntlets,
                enable=True,
            ),
            QForgeryChallenge(
                id=I18nText.MarigoldWoods,
                name=self.tr("Marigold Woods"),
                region=self.jinzhou,
                reward=self.tr("Phlogiston"),
                weapon=self.pistols,
                enable=True,
            ),
        ]

        # 共鸣者突破材料
        self.bossChallengeList = [
            QBossChallenge(
                id=I18nText.EnemyCalamityEffigy,
                name=self.tr("Calamity Effigy"),
                region=self.mengzhou,
                reward=self.tr("Forged Empyrean's Sigh"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyMyriadSnareRustfireChassis,
                name=self.tr("Myriad Snare: Rustfire Chassis"),
                region=self.mengzhou,
                reward=self.tr("Solidarity's Loneflame"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyNightmareAdamSmasher,
                name=self.tr("Nightmare: Adam Smasher"),
                region=self.lahaiRoi,
                reward=self.tr("Nightmare Flashdrive"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyNamelessExplorer,
                name=self.tr("Nameless Explorer"),
                region=self.lahaiRoi,
                reward=self.tr("Our Choice"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyHyvatia,
                name=self.tr("Hyvatia"),
                region=self.lahaiRoi,
                reward=self.tr("Suncoveter's Reach"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyReactorHusk,
                name=self.tr("Reactor Husk"),
                region=self.lahaiRoi,
                reward=self.tr("Burning Judgment"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyLadyOfTheSea,
                name=self.tr("Lady of the Sea"),
                region=self.rinascita,
                reward=self.tr("Abyssal Husk"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyTheFalseSovereign,
                name=self.tr("The False Sovereign"),
                region=self.rinascita,
                reward=self.tr("Blighted Crown of Puppet King"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyFenrico,
                name=self.tr("Fenrico"),
                region=self.rinascita,
                reward=self.tr("Truth in Lies"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyLionessOfGlory,
                name=self.tr("Lioness of Glory"),
                region=self.rinascita,
                reward=self.tr("Unfading Glory"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyDragonOfDirge,
                name=self.tr("Dragon of Dirge"),
                region=self.rinascita,
                reward=self.tr("Blazing Bone"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyLorelei,
                name=self.tr("Lorelei"),
                region=self.rinascita,
                reward=self.tr("Cleansing Conch"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemySentryConstruct,
                name=self.tr("Sentry Construct"),
                region=self.rinascita,
                reward=self.tr("Platinum Core"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyFallacyOfNoReturn,
                name=self.tr("Fallacy of No Return"),
                region=self.theBlackShores,
                reward=self.tr("Topological Confinement"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyCrownless,
                name=self.tr("Crownless"),
                region=self.jinzhou,
                reward=self.tr("Strife Tacet Core"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyFeilianBeringal,
                name=self.tr("Feilian Beringal"),
                region=self.jinzhou,
                reward=self.tr("Hidden Thunder Tacet Core"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyTempestMephis,
                name=self.tr("Tempest Mephis"),
                region=self.jinzhou,
                reward=self.tr("Thundering Tacet Core"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyThunderingMephis,
                name=self.tr("Thundering Mephis"),
                region=self.jinzhou,
                reward=self.tr("Rage Tacet Core"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyMourningAix,
                name=self.tr("Mourning Aix"),
                region=self.jinzhou,
                reward=self.tr("Roaring Rock Fist"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyMechAbomination,
                name=self.tr("Mech Abomination"),
                region=self.jinzhou,
                reward=self.tr("Elegy Tacet Core"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyImpermanenceHeron,
                name=self.tr("Impermanence Heron"),
                region=self.jinzhou,
                reward=self.tr("Gold-Dissolving Feather"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyInfernoRider,
                name=self.tr("Inferno Rider"),
                region=self.jinzhou,
                reward=self.tr("Sound-Keeping Tacet Core"),
                enable=True,
            ),
            QBossChallenge(
                id=I18nText.EnemyLampylumenMyriad,
                name=self.tr("Lampylumen Myriad"),
                region=self.jinzhou,
                reward=self.tr("Group Abomination Tacet Core"),
                enable=True,
            ),
        ]

        # 无音区
        self.tacetSuppressionList = [
            QTacetSuppression(
                id=I18nText.TacetFieldHeartOfStillness,
                name=self.tr("Heart of Stillness", "Tacet Field"),
                region=self.mengzhou,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldHeartOfFlames,
                name=self.tr("Heart of Flames", "Tacet Field"),
                region=self.mengzhou,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.WesternFangPeaksTacetField,
                name=self.tr("Western Fang Peaks", "Tacet Field"),
                region=self.mengzhou,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.EasternXuanPeaksTacetField,
                name=self.tr("Eastern Xuan Peaks", "Tacet Field"),
                region=self.mengzhou,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldSolisiaLanding,
                name=self.tr("Solisia Landing", "Tacet Field"),
                region=self.lahaiRoi,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldFrostlandsTransitPort,
                name=self.tr("Frostlands Transit Port", "Tacet Field"),
                region=self.lahaiRoi,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldMountGjallar,
                name=self.tr("Mount Gjallar", "Tacet Field"),
                region=self.lahaiRoi,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldMawburrowDesert,
                name=self.tr("Mawburrow Desert", "Tacet Field"),
                region=self.lahaiRoi,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldStagnantRun,
                name=self.tr("Stagnant Run", "Tacet Field"),
                region=self.lahaiRoi,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldMournfellCanyon,
                name=self.tr("Mournfell Canyon", "Tacet Field"),
                region=self.rinascita,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldBeohrWaters,
                name=self.tr("Beohr Waters", "Tacet Field"),
                region=self.rinascita,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldRiccioliIslands,
                name=self.tr("Riccioli Islands", "Tacet Field"),
                region=self.rinascita,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldFagaceaePeninsula,
                name=self.tr("Fagaceae Peninsula", "Tacet Field"),
                region=self.rinascita,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldPenitentsEnd,
                name=self.tr("Penitent's End", "Tacet Field"),
                region=self.rinascita,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldCentralPlains,
                name=self.tr("Central Plains", "Tacet Field"),
                region=self.jinzhou,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldDesorockHighlandI,
                name=self.tr("Desorock Highland I", "Tacet Field"),
                region=self.jinzhou,
                rewards=[],
                enable=False,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldTigersMaw,
                name=self.tr("Tiger's Maw", "Tacet Field"),
                region=self.jinzhou,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldWhiningAixsMire,
                name=self.tr("Whining Aix's Mire", "Tacet Field"),
                region=self.jinzhou,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldPortCityOfGuixu,
                name=self.tr("Port City of Guixu", "Tacet Field"),
                region=self.jinzhou,
                rewards=[],
                enable=True,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldDesorockHighlandII,
                name=self.tr("Desorock Highland II", "Tacet Field"),
                region=self.jinzhou,
                rewards=[],
                enable=False,
            ),
            QTacetSuppression(
                id=I18nText.TacetFieldDimForest,
                name=self.tr("Dim Forest", "Tacet Field"),
                region=self.jinzhou,
                rewards=[],
                enable=True,
            ),
        ]

        # 残象聚落
        self.tacetDiscordNestMengzhou = [
            QTacetDiscordNest(
                id=I18nText.SimulacrumNexusTacetDiscordNest,
                name=self.tr("Simulacrum Nexus", "Tacet Discord Nest"),
                region_id=I18nText.Mengzhou,
                region=self.mengzhou,
                rewards=[],
                enable=True,
            ),
            QTacetDiscordNest(
                id=I18nText.SouthernYuanHillsTacetDiscordNest,
                name=self.tr("Southern Yuan Hills", "Tacet Discord Nest"),
                region_id=I18nText.Mengzhou,
                region=self.mengzhou,
                rewards=[],
                enable=True,
            ),
        ]

        self.tacetDiscordNestLahaiRoi = [
            QTacetDiscordNest(
                id=I18nText.StarblindCrashsiteTacetDiscordNest,
                name=self.tr("Starblind Crashsite", "Tacet Discord Nest"),
                region_id=I18nText.LahaiRoi,
                region=self.lahaiRoi,
                rewards=[],
                enable=True,
            ),
            QTacetDiscordNest(
                id=I18nText.RebirthUplandsTacetDiscordNest,
                name=self.tr("Rebirth Uplands", "Tacet Discord Nest"),
                region_id=I18nText.LahaiRoi,
                region=self.lahaiRoi,
                rewards=[],
                enable=True,
            ),
            QTacetDiscordNest(
                id=I18nText.StagnantRunTacetDiscordNest,
                name=self.tr("Stagnant Run", "Tacet Discord Nest"),
                region_id=I18nText.LahaiRoi,
                region=self.lahaiRoi,
                rewards=[],
                enable=True,
            ),
        ]

        # 梦魇聚落
        self.nightmarePurificationList = [
            QNightmarePurification(
                id=I18nText.HonamiCityNightmareNest,
                name=self.tr("Honami City Nightmare Nest", "Nightmare Nest"),
                rewards=[],
                enable=True,
            ),
            QNightmarePurification(
                id=I18nText.ThreeHeroesCrestNightmareNest,
                name=self.tr("Three Heroes' Crest: Nightmare Nest", "Nightmare Nest"),
                rewards=[],
                enable=True,
            ),
            QNightmarePurification(
                id=I18nText.TidelineVergeNightmareNest,
                name=self.tr("Tideline Verge Nightmare Nest", "Nightmare Nest"),
                rewards=[],
                enable=True,
            ),
            QNightmarePurification(
                id=I18nText.TheWastelandsNightmareNest,
                name=self.tr("The Wastelands Nightmare Nest", "Nightmare Nest"),
                rewards=[],
                enable=True,
            ),
            QNightmarePurification(
                id=I18nText.FallenGraveNightmareNest,
                name=self.tr("Fallen Grave Nightmare Nest", "Nightmare Nest"),
                rewards=[],
                enable=True,
            ),
        ]

        # 培养目标，保持与游戏内一致
        self.resonatorList = [
            QResonator(
                id=I18nText.Lily,
                name=self.tr("Lily"),
                weeklyChallenge=self.tr("Sigillum"),
                tacetSuppression=[self.tr("Heart of Stillness", "Tacet Field")],
                forgeryChallenge=[self.tr("Ashen Chasm"), self.tr("Lesson in Embers")],
                bossChallenge=self.tr("Hyvatia"),
                gather=self.tr("Reverie Lily"),
                tacetDiscordNest=[self.tr("Simulacrum Nexus", "Tacet Discord Nest")],
                nightmarePurification=[],
                enable=True,
            ),
            QResonator(
                id=I18nText.Suoming,
                name=self.tr("Suoming"),
                weeklyChallenge=self.tr("Suhsin the Inevitable"),
                tacetSuppression=[self.tr("Heart of Stillness", "Tacet Field"), self.tr("Heart of Flames", "Tacet Field")],
                forgeryChallenge=[self.tr("Wingfall Chasm"), self.tr("Fallen Sanctum")],
                bossChallenge=self.tr("Calamity Effigy"),
                gather=self.tr("Miasmic Branch"),
                tacetDiscordNest=[self.tr("Simulacrum Nexus", "Tacet Discord Nest")],
                nightmarePurification=[],
                enable=True,
            ),
            QResonator(
                id=I18nText.Hsin,
                name=self.tr("Hsin"),
                weeklyChallenge=self.tr("Suhsin the Inevitable"),
                tacetSuppression=[self.tr("Heart of Stillness", "Tacet Field"), self.tr("Heart of Flames", "Tacet Field")],
                forgeryChallenge=[self.tr("Silent Chasm"), self.tr("Lesson in Sunset")],
                bossChallenge=self.tr("Myriad Snare: Rustfire Chassis"),
                gather=self.tr("Bloom of Hearkening"),
                tacetDiscordNest=[self.tr("Simulacrum Nexus", "Tacet Discord Nest")],
                nightmarePurification=[],
                enable=True,
            ),
            QResonator(
                id=I18nText.Jingran,
                name=self.tr("Jingran"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Qingxiao,
                name=self.tr("Qingxiao"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Suisui,
                name=self.tr("Suisui"),
                weeklyChallenge=self.tr("Thousand-Puppet Pavilion"),
                tacetSuppression=[self.tr("Eastern Xuan Peaks", "Tacet Field"),
                                  self.tr("Western Fang Peaks", "Tacet Field")],
                forgeryChallenge=[self.tr("Silent Chasm"), self.tr("Lesson in Sunset")],
                bossChallenge=self.tr("Myriad Snare: Rustfire Chassis"),
                gather=self.tr("Flowborne Dream"),
                tacetDiscordNest=[self.tr("Southern Yuan Hills", "Tacet Discord Nest")],
                nightmarePurification=[],
                enable=True,
            ),
            QResonator(
                id=I18nText.YangyangXuanling,
                name=self.tr("Yangyang: Xuanling"),
                weeklyChallenge=self.tr("Thousand-Puppet Pavilion"),
                tacetSuppression=[self.tr("Eastern Xuan Peaks", "Tacet Field"),
                                  self.tr("Western Fang Peaks", "Tacet Field")],
                forgeryChallenge=[self.tr("Wingfall Chasm"), self.tr("Fallen Sanctum")],
                bossChallenge=self.tr("Myriad Snare: Rustfire Chassis"),
                gather=self.tr("Cloudperch Seed"),
                tacetDiscordNest=[self.tr("Southern Yuan Hills", "Tacet Discord Nest")],
                nightmarePurification=[],
                enable=True,
            ),
            QResonator(
                id=I18nText.Rebecca,
                name=self.tr("Rebecca"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Lucy,
                name=self.tr("Lucy"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Hiyuki,
                name=self.tr("Hiyuki"),
                weeklyChallenge=self.tr("Denia"),
                tacetSuppression=[self.tr("Solisia Landing", "Tacet Field")],
                forgeryChallenge=[self.tr("Wingfall Chasm"), self.tr("Fallen Sanctum")],
                bossChallenge=self.tr("Nameless Explorer"),
                gather=self.tr("Redbell"),
                tacetDiscordNest=[self.tr("Stagnant Run", "Tacet Discord Nest"), self.tr("Rebirth Uplands", "Tacet Discord Nest")],
                nightmarePurification=[],
                enable=True,
            ),
            QResonator(
                id=I18nText.Lucilla,
                name=self.tr("Lucilla"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Sigrika,
                name=self.tr("Sigrika"),
                weeklyChallenge=self.tr("Sigillum"),
                tacetSuppression=[self.tr("Frostlands Transit Port", "Tacet Field")],
                forgeryChallenge=[self.tr("Eroded Chasm"), self.tr("Lesson in Void")],
                bossChallenge=self.tr("Nameless Explorer"),
                gather=self.tr("Arithmetic Shell"),
                tacetDiscordNest=[self.tr("Stagnant Run", "Tacet Discord Nest"), self.tr("Rebirth Uplands", "Tacet Discord Nest")],
                nightmarePurification=[],
                enable=True,
            ),
            QResonator(
                id=I18nText.Denia,
                name=self.tr("Denia"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Mornye,
                name=self.tr("Mornye"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Lynae,
                name=self.tr("Lynae"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Buling,
                name=self.tr("Buling"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Chisa,
                name=self.tr("Chisa"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Qiuyuan,
                name=self.tr("Qiuyuan"),
                weeklyChallenge=self.tr("Threnodian: Leviathan"),
                tacetSuppression=[self.tr("Mournfell Canyon", "Tacet Field")],
                forgeryChallenge=[self.tr("Garden of Salvation"), self.tr("Flaming Remnants")],
                bossChallenge=self.tr("Fenrico"),
                gather=self.tr("Wintry Bell"),
                tacetDiscordNest=[],
                nightmarePurification=[self.tr("Tideline Verge", "Nightmare Nest")],
                enable=True,
            ),
            QResonator(
                id=I18nText.Galbrena,
                name=self.tr("Galbrena"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.LuukHerssen,
                name=self.tr("Luuk Herssen"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Aemeath,
                name=self.tr("Aemeath"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Augusta,
                name=self.tr("Augusta"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Iuno,
                name=self.tr("Iuno"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Lupa,
                name=self.tr("Lupa"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Phoebe,
                name=self.tr("Phoebe"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Brant,
                name=self.tr("Brant"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Phrolova,
                name=self.tr("Phrolova"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Cartethyia,
                name=self.tr("Cartethyia"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Zanni,
                name=self.tr("Zanni"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Ciaccona,
                name=self.tr("Ciaccona"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Cantarella,
                name=self.tr("Cantarella"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Roccia,
                name=self.tr("Roccia"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Carlotta,
                name=self.tr("Carlotta"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Youhu,
                name=self.tr("Youhu"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Lumi,
                name=self.tr("Lumi"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Camellya,
                name=self.tr("Camellya"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Shorekeeper,
                name=self.tr("Shorekeeper"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Zhezhi,
                name=self.tr("Zhezhi"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Changli,
                name=self.tr("Changli"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.XiangliYao,
                name=self.tr("Xiangli Yao"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Jinhsi,
                name=self.tr("Jinhsi"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Jianxin,
                name=self.tr("Jianxin"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Calcharo,
                name=self.tr("Calcharo"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Yinlin,
                name=self.tr("Yinlin"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Yuanwu,
                name=self.tr("Yuanwu"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Lingyang,
                name=self.tr("Lingyang"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Mortefi,
                name=self.tr("Mortefi"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Aalto,
                name=self.tr("Aalto"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Jiyan,
                name=self.tr("Jiyan"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Danjin,
                name=self.tr("Danjin"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Taoqi,
                name=self.tr("Taoqi"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Encore,
                name=self.tr("Encore"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Sanhua,
                name=self.tr("Sanhua"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Baizhi,
                name=self.tr("Baizhi"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Rover,
                name=self.tr("Rover"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Verina,
                name=self.tr("Verina"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Chixia,
                name=self.tr("Chixia"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
            QResonator(
                id=I18nText.Yangyang,
                name=self.tr("Yangyang"),
                weeklyChallenge='',
                tacetSuppression=[],
                forgeryChallenge=[],
                bossChallenge='',
                gather='',
                tacetDiscordNest=[],
                nightmarePurification=[],
                enable=False,
            ),
        ]

    def __initGridLayout(self):
        # self.weeklyChallengeCheckBox.setStyleSheet("QCheckBox { border: 2px solid red; }")
        self.weeklyChallengeCheckBox = CheckBox(self.tr("Weekly Challenge:"), self.container)
        self.weeklyChallengeComboBox = ComboBox(self.container)
        self.weeklyChallengeComboBox.addItem(self.tr("Not selected"), userData=None)
        for item in self.weeklyChallengeList:
            text = self.tr("{name} - {enemy}").format(name=item.name, enemy=item.enemy)
            self.weeklyChallengeComboBox.addItem(text, userData=item.id)
            self.weeklyChallengeComboBox.setItemEnabled(self.weeklyChallengeComboBox.count() - 1, item.enable)

        self.tacetSuppressionCheckBox = CheckBox(self.tr("Echo Materials:"), self.container)
        self.tacetSuppressionComboBox = ComboBox(self.container)
        self.tacetSuppressionComboBox.addItem(self.tr("Not selected"), userData=None)
        for item in self.tacetSuppressionList:
            self.tacetSuppressionComboBox.addItem(f"{item.name} - {item.region}", userData=item.id)
            self.tacetSuppressionComboBox.setItemEnabled(self.tacetSuppressionComboBox.count() - 1, item.enable)

        self.forgeryChallengeCheckBox = CheckBox(self.tr("Weapon and Skill Materials:"), self.container)
        self.forgeryChallengeComboBox = ComboBox(self.container)
        self.forgeryChallengeComboBox.addItem(self.tr("Not selected"), userData=None)
        for item in self.forgeryChallengeList:
            text = self.tr("{name} - {weapon} - {region}").format(name=item.name, weapon=item.weapon, region=item.region)
            self.forgeryChallengeComboBox.addItem(text, userData=item.id)
            self.forgeryChallengeComboBox.setItemEnabled(self.forgeryChallengeComboBox.count() - 1, item.enable)

        self.bossChallengeCheckBox = CheckBox(self.tr("Ascension Materials:"), self.container)
        self.bossChallengeComboBox = ComboBox(self.container)
        self.bossChallengeComboBox.addItem(self.tr("Not selected"), userData=None)
        for item in self.bossChallengeList:
            self.bossChallengeComboBox.addItem(item.name, userData=item.id)
            self.bossChallengeComboBox.setItemEnabled(self.bossChallengeComboBox.count() - 1, item.enable)

        self.tacetDiscordNestCheckBox = CheckBox(self.tr("Tacet Discord Nest:"), self.container)
        self.tacetDiscordNestComboBox = ComboBox(self.container)
        self.tacetDiscordNestComboBox.addItem(self.tr("Not selected"), userData=None)
        self.tacetDiscordNestComboBox.addItem(self.tr("Select all"), userData="All")
        self.tacetDiscordNestComboBox.addItem(self.tr("Select all of Mengzhou"), userData=I18nText.Mengzhou)
        for item in self.tacetDiscordNestMengzhou:
            text = self.tr("{name} - {region}").format(name=item.name, region=item.region)
            self.tacetDiscordNestComboBox.addItem(text, userData=item.id)
            self.tacetDiscordNestComboBox.setItemEnabled(self.tacetDiscordNestComboBox.count() - 1, item.enable)
        self.tacetDiscordNestComboBox.addItem(self.tr("Select all of Lahai-Roi"), userData=I18nText.LahaiRoi)
        for item in self.tacetDiscordNestLahaiRoi:
            self.tacetDiscordNestComboBox.addItem(f"{item.name} - {item.region}", userData=item.id)
            self.tacetDiscordNestComboBox.setItemEnabled(self.tacetDiscordNestComboBox.count() - 1, item.enable)

        self.nightmarePurificationCheckBox = CheckBox(self.tr("Nightmare Nest:"), self.container)
        self.nightmarePurificationComboBox = ElidedMultiSelectionComboBox(self.container)
        self.nightmarePurificationComboBox.setPlaceholderText(self.tr("Not selected"))
        for item in self.nightmarePurificationList:
            self.nightmarePurificationComboBox.addItem(item.name, userData=item.id)

        self.activityCheckBox = CheckBox(self.tr("Activity:"), self.container)
        self.activityComboBox = ComboBox(self.container)
        self.activityComboBox.addItem(self.tr(r"Daily / Weekly Activity, Phantasma Dreamland"), userData="Auto")

        self.mailCheckBox = CheckBox(self.tr("Mail:"), self.container)
        self.mailComboBox = ComboBox(self.container)
        self.mailComboBox.addItem(self.tr("Auto"), userData="Auto")

        self.pioneerPodcastCheckBox = CheckBox(self.tr("Pioneer Podcast:"), self.container)
        self.pioneerPodcastComboBox = ComboBox(self.container)
        self.pioneerPodcastComboBox.addItem(self.tr("Auto"), userData="Auto")

        # 培养目标
        self.focusWeeklyChallenge = QLabel(self.container)
        self.focusTacetSuppression = QLabel(self.container)
        self.focusForgeryChallenge = QLabel(self.container)
        self.focusBossChallenge = QLabel(self.container)
        self.focusGather = QLabel(self.container)
        self.focusTacetDiscordNest = QLabel(self.container)
        self.focusNightmarePurification = QLabel(self.container)

        self.focusResonatorLayout = QHBoxLayout()
        self.focusResonatorTitle = QLabel(self.tr("Resonator: "), self.container)
        self.focusResonatorComboBox = ComboBox(self.container)
        self.focusResonatorComboBox.addItem(self.tr("Not selected"), userData=None)
        iam = Resonator.id_avatar_mappings()
        for item in self.resonatorList:
            if not item.enable:
                continue
            avatar = None
            if avatars := iam.get(item.id):
                avatar = QIcon(str(Resource.Unpacked.IconRoleHead150 / avatars[0]))
            self.focusResonatorComboBox.addItem(item.name, avatar, userData=item.id)
        self.focusResonatorComboBox.setCurrentIndex(0)

        self.buttonGroup = [
            self.tacetSuppressionCheckBox,
            self.forgeryChallengeCheckBox,
            self.bossChallengeCheckBox,
        ]
        self.buttonGroupOpen = [
            paramConfig.tacetSuppressionOpen,
            paramConfig.forgeryChallengeOpen,
            paramConfig.bossChallengeOpen,
        ]
        self.buttonGroupComboBox = [
            self.tacetSuppressionComboBox,
            self.forgeryChallengeComboBox,
            self.bossChallengeComboBox,
        ]

    def __create_up_label(self, register: Optional[list] = None) -> QLabel:
        upLabel = QLabel("UP↑", self.container)
        upLabel.setVisible(False)
        upLabel.setStyleSheet("""
            QLabel {
                color: #FDEF8E;
                font-weight: bold;
            }
        """)
        shadow = QGraphicsDropShadowEffect(upLabel)
        shadow.setBlurRadius(12)  # 阴影模糊半径
        # shadow.setColor(QColor("black"))  # 阴影颜色
        shadow.setColor(QColor(0, 0, 0, 220))  # 阴影颜色
        shadow.setOffset(1.2, 1.2)  # 阴影偏移量
        upLabel.setGraphicsEffect(shadow)
        self.upLabels.append(upLabel)
        if register is not None:
            register.append(upLabel)
        return upLabel

    def __initWidget(self):
        # self.resize(1000, 800)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        # self.setObjectName('paramInterface')

        # self.resetButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        # initialize style sheet
        self.container.setObjectName('view')
        StyleSheet.PARAM_INTERFACE.apply(self)

        self.weeklyChallengeCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.tacetSuppressionCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.forgeryChallengeCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.bossChallengeCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.nightmarePurificationCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.tacetDiscordNestCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.activityCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.mailCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # self.focusWeeklyChallenge.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        self.contentBottomLayout.addWidget(self.resetButton)
        self.contentBottomLayout.addWidget(self.aboutButton)
        self.contentBottomLayout.addStretch()
        self.contentBottomLayout.setSpacing(15)
        # self.contentBottomLayout.setContentsMargins(110, 0, 0, 0)
        self.contentBottomLayout.setContentsMargins(0, 0, 0, 0)

        self.focusResonatorLayout.addWidget(self.focusResonatorTitle, 14)
        self.focusResonatorLayout.addStretch(1)
        self.focusResonatorLayout.addWidget(self.focusResonatorComboBox, 24)
        self.focusResonatorLayout.addStretch(1)
        self.focusResonatorLayout.setContentsMargins(0, 0, 0, 0)

        # grid
        row = 0

        # self.gridLayout.addWidget(self.contentTitleLabel, row, 0, 1, 2)
        self.gridLayout.addWidget(self.waveplateLabel, row, 0, 1, 2)
        self.gridLayout.addLayout(self.focusResonatorLayout, row, 3)

        row += 1
        self.gridLayout.addWidget(self.__create_up_label(), row, 0)
        self.gridLayout.addWidget(self.weeklyChallengeCheckBox, row, 1)
        self.gridLayout.addWidget(self.weeklyChallengeComboBox, row, 2)
        self.gridLayout.addWidget(self.focusWeeklyChallenge, row, 3)
        # self.gridLayout.addWidget(self.weeklyChallengeSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.__create_up_label(self.chordCleansing), row, 0)
        self.gridLayout.addWidget(self.tacetSuppressionCheckBox, row, 1)
        self.gridLayout.addWidget(self.tacetSuppressionComboBox, row, 2)
        self.gridLayout.addWidget(self.focusTacetSuppression, row, 3)
        # self.gridLayout.addWidget(self.tacetSuppressionSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.__create_up_label(self.bountifulCrescendo), row, 0)
        self.gridLayout.addWidget(self.forgeryChallengeCheckBox, row, 1)
        self.gridLayout.addWidget(self.forgeryChallengeComboBox, row, 2)
        self.gridLayout.addWidget(self.focusForgeryChallenge, row, 3)
        # self.gridLayout.addWidget(self.forgeryChallengeSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.__create_up_label(), row, 0)
        self.gridLayout.addWidget(self.bossChallengeCheckBox, row, 1)
        self.gridLayout.addWidget(self.bossChallengeComboBox, row, 2)
        self.gridLayout.addWidget(self.focusBossChallenge, row, 3)
        # self.gridLayout.addWidget(self.bossChallengeSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.nestLabel, row, 0, 1, 2)
        self.gridLayout.addWidget(self.focusGather, row, 3)

        row += 1
        self.gridLayout.addWidget(self.tacetDiscordNestCheckBox, row, 1)
        self.gridLayout.addWidget(self.tacetDiscordNestComboBox, row, 2)
        self.gridLayout.addWidget(self.focusTacetDiscordNest, row, 3)
        # self.gridLayout.addWidget(self.tacetDiscordNestSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.nightmarePurificationCheckBox, row, 1)
        self.gridLayout.addWidget(self.nightmarePurificationComboBox, row, 2)
        self.gridLayout.addWidget(self.focusNightmarePurification, row, 3)
        # self.gridLayout.addWidget(self.nightmarePurificationSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.claimRewardsLabel, row, 0, 1, 2)

        row += 1
        self.gridLayout.addWidget(self.activityCheckBox, row, 1)
        self.gridLayout.addWidget(self.activityComboBox, row, 2)
        # self.gridLayout.addWidget(self.activitySettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.mailCheckBox, row, 1)
        self.gridLayout.addWidget(self.mailComboBox, row, 2)
        # self.gridLayout.addWidget(self.mailSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.pioneerPodcastCheckBox, row, 1)
        self.gridLayout.addWidget(self.pioneerPodcastComboBox, row, 2)
        # self.gridLayout.addWidget(self.pioneerPodcastSettingButton, row, 2)

        row += 1
        self.gridLayout.addLayout(self.contentBottomLayout, row, 2)

        # # 参数：row=0（从第0行开始）, column=2（第3列）, rowSpan=3（跨3行）, columnSpan=1（占1列）
        # self.gridLayout.addLayout(self.focusResonatorLayout, 0, 3, row, 1)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setHorizontalSpacing(10)
        # self.gridLayout.setVerticalSpacing(8)
        self.gridLayout.setAlignment(Qt.AlignVCenter)

        # column stretch
        self.gridLayout.setColumnStretch(0, 0)
        self.gridLayout.setColumnStretch(1, 0)
        self.gridLayout.setColumnStretch(2, 7)
        self.gridLayout.setColumnStretch(3, 3)

        self.mainLayout.addLayout(self.gridLayout)
        self.mainLayout.addStretch()
        # self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setContentsMargins(20, 0, 15, 0)
        # self.mainLayout.setAlignment(Qt.AlignTop)

    def __connectSignalToSlot(self):
        self.weeklyChallengeCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.weeklyChallengeOpen, checked))
        for idx, cb in enumerate(self.buttonGroup):
            cb.toggled.connect(lambda checked, c=cb, i=idx: self.__onCheckboxGroupChanged(c, i, checked))
        self.nightmarePurificationCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.nightmarePurificationOpen, checked))
        self.tacetDiscordNestCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.tacetDiscordNestOpen, checked))
        self.activityCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.activityOpen, checked))
        self.mailCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.mailOpen, checked))
        self.pioneerPodcastCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.pioneerPodcastOpen, checked))

        self.weeklyChallengeComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.weeklyChallenge, self.weeklyChallengeComboBox.currentData()))
        self.tacetSuppressionComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.tacetSuppression, self.tacetSuppressionComboBox.currentData()))
        self.forgeryChallengeComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.forgeryChallenge, self.forgeryChallengeComboBox.currentData()))
        self.bossChallengeComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.bossChallenge, self.bossChallengeComboBox.currentData()))
        self.nightmarePurificationComboBox.selectionChanged.connect(self.__onNightmarePurificationSelectionChanged)
        self.tacetDiscordNestComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.tacetDiscordNest, self.tacetDiscordNestComboBox.currentData()))
        self.activityComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.activity, self.activityComboBox.currentData()))
        self.mailComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.mail, self.mailComboBox.currentData()))
        self.pioneerPodcastComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.pioneerPodcast, self.pioneerPodcastComboBox.currentData()))

        self.resetButton.clicked.connect(self.__onResetButtonClicked)
        self.aboutButton.clicked.connect(self.__showAboutFlyout)

        self.focusResonatorComboBox.currentIndexChanged.connect(self.__onFocusResonatorIndexChanged)

        globalSignal.doubleDropSignal.connect(self.__onDoubleDrop)

    def __loadConfig(self):
        self.weeklyChallengeCheckBox.setChecked(paramConfig.get(paramConfig.weeklyChallengeOpen))
        self.tacetSuppressionCheckBox.setChecked(paramConfig.get(paramConfig.tacetSuppressionOpen))
        self.forgeryChallengeCheckBox.setChecked(paramConfig.get(paramConfig.forgeryChallengeOpen))
        self.bossChallengeCheckBox.setChecked(paramConfig.get(paramConfig.bossChallengeOpen))
        self.nightmarePurificationCheckBox.setChecked(paramConfig.get(paramConfig.nightmarePurificationOpen))
        self.tacetDiscordNestCheckBox.setChecked(paramConfig.get(paramConfig.tacetDiscordNestOpen))
        self.activityCheckBox.setChecked(paramConfig.get(paramConfig.activityOpen))
        self.mailCheckBox.setChecked(paramConfig.get(paramConfig.mailOpen))
        self.pioneerPodcastCheckBox.setChecked(paramConfig.get(paramConfig.pioneerPodcastOpen))

        self.weeklyChallengeComboBox.setCurrentIndex(
            self.weeklyChallengeComboBox.findData(paramConfig.get(paramConfig.weeklyChallenge)))
        self.tacetSuppressionComboBox.setCurrentIndex(
            self.tacetSuppressionComboBox.findData(paramConfig.get(paramConfig.tacetSuppression)))
        self.forgeryChallengeComboBox.setCurrentIndex(
            self.forgeryChallengeComboBox.findData(paramConfig.get(paramConfig.forgeryChallenge)))
        self.bossChallengeComboBox.setCurrentIndex(
            self.bossChallengeComboBox.findData(paramConfig.get(paramConfig.bossChallenge)))

        if nests := paramConfig.get(paramConfig.nightmarePurification):
            if isinstance(nests, str):
                nests = [nests]
            elif isinstance(nests, list):
                pass
            else:
                nests = []
            indices = {i for i, item in enumerate(self.nightmarePurificationComboBox.items) if item.userData in nests}
            self.nightmarePurificationComboBox.setSelectedIndices(indices)

        self.tacetDiscordNestComboBox.setCurrentIndex(
            self.tacetDiscordNestComboBox.findData(paramConfig.get(paramConfig.tacetDiscordNest)))
        self.activityComboBox.setCurrentIndex(
            self.activityComboBox.findData(paramConfig.get(paramConfig.activity)))
        self.mailComboBox.setCurrentIndex(
            self.mailComboBox.findData(paramConfig.get(paramConfig.mail)))
        self.pioneerPodcastComboBox.setCurrentIndex(
            self.pioneerPodcastComboBox.findData(paramConfig.get(paramConfig.pioneerPodcast)))

        index = self.focusResonatorComboBox.findData(paramConfig.get(paramConfig.focusResonator))
        if index >= 0:
            self.focusResonatorComboBox.setCurrentIndex(index)

    def __onResetButtonClicked(self):
        self.weeklyChallengeComboBox.setCurrentIndex(0)
        self.weeklyChallengeCheckBox.setChecked(False)

        self.tacetSuppressionComboBox.setCurrentIndex(0)
        self.tacetSuppressionCheckBox.setChecked(False)

        self.forgeryChallengeComboBox.setCurrentIndex(0)
        self.forgeryChallengeCheckBox.setChecked(False)

        self.bossChallengeComboBox.setCurrentIndex(0)
        self.bossChallengeCheckBox.setChecked(False)

        self.nightmarePurificationComboBox.setSelectedIndices(set())
        self.nightmarePurificationCheckBox.setChecked(False)

        self.tacetDiscordNestComboBox.setCurrentIndex(0)
        self.tacetDiscordNestCheckBox.setChecked(False)

        self.activityComboBox.setCurrentIndex(0)
        self.activityCheckBox.setChecked(False)

        self.mailComboBox.setCurrentIndex(0)
        self.mailCheckBox.setChecked(False)

        self.pioneerPodcastComboBox.setCurrentIndex(0)
        self.pioneerPodcastCheckBox.setChecked(False)

    def __onCheckboxGroupChanged(self, cb, idx, checked):
        # logger.info(f"onCheckboxGroupChanged: {cb.text()} {checked}")
        for i in range(len(self.buttonGroup)):
            if checked:
                if i == idx:
                    self.buttonGroupComboBox[i].setEnabled(True)
                    paramConfig.set(self.buttonGroupOpen[i], True)
                else:
                    self.buttonGroupComboBox[i].setEnabled(False)
                    self.buttonGroup[i].blockSignals(True)
                    self.buttonGroup[i].setChecked(False)
                    self.buttonGroup[i].blockSignals(False)
                    paramConfig.set(self.buttonGroupOpen[i], False)
            else:
                self.buttonGroupComboBox[i].setEnabled(True)
                paramConfig.set(self.buttonGroupOpen[i], False)

    def __onNightmarePurificationSelectionChanged(self, indices: set[int]):
        selected = [self.nightmarePurificationComboBox.items[i].userData for i in sorted(indices)]
        paramConfig.set(paramConfig.nightmarePurification, selected)

    def __updateFocusResonatorInfo(self, resonator_id: str | None):
        for resonator in self.resonatorList:
            if resonator.id != resonator_id:
                continue
            self.focusWeeklyChallenge.setText(resonator.weeklyChallenge)
            self.focusTacetSuppression.setText(", ".join(resonator.tacetSuppression))
            self.focusForgeryChallenge.setText(", ".join(resonator.forgeryChallenge))
            self.focusBossChallenge.setText(resonator.bossChallenge)
            # self.focusGather.setText(self.tr(r"Gather: {}").format(resonator.gather))
            self.focusTacetDiscordNest.setText(", ".join(resonator.tacetDiscordNest))
            self.focusNightmarePurification.setText(", ".join(resonator.nightmarePurification))
            return

        self.focusWeeklyChallenge.clear()
        self.focusTacetSuppression.clear()
        self.focusForgeryChallenge.clear()
        self.focusBossChallenge.clear()
        # self.focusGather.clear()
        self.focusTacetDiscordNest.clear()
        self.focusNightmarePurification.clear()

    def __onFocusResonatorIndexChanged(self, index: int):
        resonator_id = self.focusResonatorComboBox.itemData(index)
        paramConfig.set(paramConfig.focusResonator, resonator_id)
        self.__updateFocusResonatorInfo(resonator_id)

    def __showAboutFlyout(self):
        Flyout.create(
            # icon=InfoBarIcon.INFORMATION,
            title=self.tr('About:'),
            content=self.tr('If you encounter any issues, please report them in our group chat. Before using this feature, we recommend disabling mods and similar modifications to avoid interfering with recognition.'),
            target=self.aboutButton,
            parent=self.window()
        )

    def __onDoubleDrop(self, show_bountiful_crescendo: bool):
        show_labels = self.bountifulCrescendo
        if not show_bountiful_crescendo:
            show_labels = self.chordCleansing
        for label in show_labels:
            label.setVisible(True)