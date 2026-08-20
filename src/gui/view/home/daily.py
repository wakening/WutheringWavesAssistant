import logging

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
                            PushButton, ToolButton, MessageBox, ToggleToolButton)

from src.gui.common.config import paramConfig, BossNameEnum
from src.gui.common.globals import globalParam, globalSignal
from src.gui.common.style_sheet import StyleSheet
from src.gui.common.task import TaskId, BaseTask, ValidationResult

logger = logging.getLogger(__name__)


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

        self.contentTitleLabel = QLabel(self.tr("任务设置"), self.container)
        self.gridLayout = QGridLayout()
        self.__initGridLayout()

        self.contentBottomLayout = QHBoxLayout()
        self.resetButton = PushButton(self.tr("重置"), self.container)
        self.aboutButton = PushButton(self.tr('关于'), self.container)

        self.__initWidget()

        self.currentTask = self.task

    def __initData(self):
        from src.core.i18n import I18nText, I18nTr, Language

        # try:
        #     self.curLang = Language(paramConfig.get(paramConfig.gameLanguage))
        # except Exception:
        #     self.curLang = Language.ZH
        self.curLang = Language.ZH

        self.i18ntr = I18nTr(self.curLang)

        # 周本副本名，保存用，后端用，倒叙，最新在前
        self.weeklyChallenge = [
            I18nText.CourtOfShackledSouls,
            I18nText.SeedOfIllusoryOrigin,
            I18nText.GateOfTheLostStar,
            I18nText.CinderniteApocalypse,
            I18nText.TheWheelOfBrokenFate,
            I18nText.BeyondTheCrimsonCurtain,
            I18nText.TheFatedConfrontation,
            I18nText.StatueOfTheCrownless,
            I18nText.ChaoticJuncture,
            I18nText.BellOfArchaicChants,
        ]
        # 周本boss名，展示用，仅前端用
        self.weeklyBoss = [
            I18nText.WeeklyBossThousandPuppetPavilion,
            I18nText.WeeklyBossDenia,
            I18nText.WeeklyBossSigillum,
            I18nText.WeeklyBossThrenodianLeviathan,
            I18nText.WeeklyBossFleurdelys,
            I18nText.WeeklyBossHecate,
            I18nText.WeeklyBossJue,
            I18nText.WeeklyBossCrownless,
            I18nText.WeeklyBossScarAberrantNightmare,
            I18nText.WeeklyBossBellBorneGeochelone,
        ]
        # 武器、角色升级素材
        self.weapon = [
            I18nText.Sword,
            I18nText.Rectifier,
            I18nText.Broadblade,
            I18nText.Gauntlets,
            I18nText.Pistols,
        ]
        self.forgeryChallenge = [
            I18nText.WingfallChasm,
            I18nText.SilentChasm,
            I18nText.SplitChasm,
            I18nText.ErodedChasm,
            I18nText.AshenChasm,
            I18nText.FallenSanctum,
            I18nText.LessonInSunset,
            I18nText.StrickenSanctum,
            I18nText.LessonInVoid,
            I18nText.LessonInEmbers,
            I18nText.GardenOfSalvation,
            I18nText.AbyssOfInitiation,
            I18nText.GardenOfAdoration,
            I18nText.AbyssOfSacrifice,
            I18nText.AbyssOfConfession,
            I18nText.FlamingRemnants,
            I18nText.MistyForest,
            I18nText.ErodedRuins,
            I18nText.MoonlitGroves,
            I18nText.MarigoldWoods,
        ]
        self.bossChallenge = [
            I18nText.EnemyMyriadSnareRustfireChassis,
            I18nText.EnemyNightmareAdamSmasher,
            I18nText.EnemyNamelessExplorer,
            I18nText.EnemyHyvatia,
            I18nText.EnemyReactorHusk,
            I18nText.EnemyLadyOfTheSea,
            I18nText.EnemyTheFalseSovereign,
            I18nText.EnemyFenrico,
            I18nText.EnemyLionessOfGlory,
            I18nText.EnemyDragonOfDirge,
            I18nText.EnemyLorelei,
            I18nText.EnemySentryConstruct,
            I18nText.EnemyCrownless,
            I18nText.EnemyThunderingMephis,
            I18nText.EnemyTempestMephis,
            I18nText.EnemyInfernoRider,
            I18nText.EnemyFeilianBeringal,
            I18nText.EnemyMourningAix,
            I18nText.EnemyImpermanenceHeron,
            I18nText.EnemyLampylumenMyriad,
            I18nText.EnemyMechAbomination,
            I18nText.EnemyFallacyOfNoReturn,
        ]
        self.tacetSuppression = [
            I18nText.WesternFangPeaksTacetField,
            I18nText.EasternXuanPeaksTacetField,
            I18nText.TacetFieldSolisiaLanding,
            I18nText.TacetFieldFrostlandsTransitPort,
            I18nText.TacetFieldMountGjallar,
            I18nText.TacetFieldMawburrowDesert,
            I18nText.TacetFieldStagnantRun,
        ]
        self.tacetSuppressionTips = [
            [I18nText.WishesOfQuietSnowfall, I18nText.ReelOfSplicedMemories],
            [I18nText.TrailblazingStar, I18nText.SoundOfTrueName],
            [I18nText.TrailblazingStar, I18nText.ChromaticFoam],
            [I18nText.RiteOfGildedRevelation, I18nText.PactOfNeonlightLeap],
            [I18nText.RiteOfGildedRevelation, I18nText.HaloOfStarryRadiance],
        ]
        self.nightmarePurification = [
        ]
        self.tacetDiscordNest = [
            I18nText.SouthernYuanHillsTacetDiscordNest,
            I18nText.StarblindCrashsiteTacetDiscordNest,
            I18nText.RebirthUplandsTacetDiscordNest,
            I18nText.StagnantRunTacetDiscordNest,
        ]
        self.guidebookRegion = [
            I18nText.GuidebookMengzhou,
            I18nText.GuidebookLahaiRoi,
            I18nText.GuidebookRinascita,
            I18nText.GuidebookJinzhou,
        ]
        self.guidebookRegionMap = {
            I18nText.WingfallChasm: I18nText.GuidebookMengzhou,
            I18nText.SilentChasm: I18nText.GuidebookMengzhou,
            I18nText.SplitChasm: I18nText.GuidebookMengzhou,
            I18nText.ErodedChasm: I18nText.GuidebookMengzhou,
            I18nText.AshenChasm: I18nText.GuidebookMengzhou,
            I18nText.FallenSanctum: I18nText.GuidebookLahaiRoi,
            I18nText.LessonInSunset: I18nText.GuidebookLahaiRoi,
            I18nText.StrickenSanctum: I18nText.GuidebookLahaiRoi,
            I18nText.LessonInVoid: I18nText.GuidebookLahaiRoi,
            I18nText.LessonInEmbers: I18nText.GuidebookLahaiRoi,
            I18nText.GardenOfSalvation: I18nText.GuidebookRinascita,
            I18nText.AbyssOfInitiation: I18nText.GuidebookRinascita,
            I18nText.GardenOfAdoration: I18nText.GuidebookRinascita,
            I18nText.AbyssOfSacrifice: I18nText.GuidebookRinascita,
            I18nText.AbyssOfConfession: I18nText.GuidebookRinascita,
            I18nText.FlamingRemnants: I18nText.GuidebookJinzhou,
            I18nText.MistyForest: I18nText.GuidebookJinzhou,
            I18nText.ErodedRuins: I18nText.GuidebookJinzhou,
            I18nText.MoonlitGroves: I18nText.GuidebookJinzhou,
            I18nText.MarigoldWoods: I18nText.GuidebookJinzhou,

            I18nText.WesternFangPeaksTacetField: I18nText.GuidebookMengzhou,
            I18nText.EasternXuanPeaksTacetField: I18nText.GuidebookMengzhou,
            I18nText.TacetFieldSolisiaLanding: I18nText.GuidebookLahaiRoi,
            I18nText.TacetFieldFrostlandsTransitPort: I18nText.GuidebookLahaiRoi,
            I18nText.TacetFieldMountGjallar: I18nText.GuidebookLahaiRoi,
            I18nText.TacetFieldMawburrowDesert: I18nText.GuidebookLahaiRoi,
            I18nText.TacetFieldStagnantRun: I18nText.GuidebookLahaiRoi,

            I18nText.SouthernYuanHillsTacetDiscordNest: I18nText.GuidebookMengzhou,
            I18nText.StarblindCrashsiteTacetDiscordNest: I18nText.GuidebookLahaiRoi,
            I18nText.RebirthUplandsTacetDiscordNest: I18nText.GuidebookLahaiRoi,
            I18nText.StagnantRunTacetDiscordNest: I18nText.GuidebookLahaiRoi,

        }


    def __initGridLayout(self):
        # self.weeklyChallengeCheckBox.setStyleSheet("QCheckBox { border: 2px solid red; }")
        self.weeklyChallengeCheckBox = CheckBox(self.tr("周本:"), self.container)
        self.weeklyChallengeComboBox = ComboBox(self.container)
        self.weeklyChallengeComboBox.addItem(self.tr("不选择"), userData=None)
        # self.weeklyChallengeComboBox.addItem(self.tr("自动 - 最新BOSS"), userData="Auto")
        for i in range(len(self.weeklyChallenge)):
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.weeklyChallenge[i]).raw, boss=self.i18ntr(self.weeklyBoss[i]).raw)
            self.weeklyChallengeComboBox.addItem(text, userData=self.weeklyChallenge[i])
            if i > 3:
                self.weeklyChallengeComboBox.setItemEnabled(self.weeklyChallengeComboBox.count() - 1, False)
        self.weeklyChallengeComboBox.setCurrentIndex(0)
        # self.weeklyChallengeSettingButton = ToggleToolButton(FIF.SETTING, self)

        self.tacetSuppressionCheckBox = CheckBox(self.tr("声骸材料:"), self.container)
        self.tacetSuppressionComboBox = ComboBox(self.container)
        self.tacetSuppressionComboBox.addItem(self.tr("不选择"), userData=None)
        for i in range(len(self.tacetSuppression)):
            text = self.tr("{challenge} - {region}").format(
                challenge=self.i18ntr(self.tacetSuppression[i]).raw,
                region=self.i18ntr(self.guidebookRegionMap.get(self.tacetSuppression[i])).raw,
            )
            self.tacetSuppressionComboBox.addItem(text, userData=self.tacetSuppression[i])
            if i > 3:
                self.tacetSuppressionComboBox.setItemEnabled(self.tacetSuppressionComboBox.count() - 1, False)
        # self.tacetSuppressionSettingButton = ToggleToolButton(FIF.SETTING, self)

        self.forgeryChallengeCheckBox = CheckBox(self.tr("武器及技能材料:"), self.container)
        self.forgeryChallengeComboBox = ComboBox(self.container)
        self.forgeryChallengeComboBox.addItem(self.tr("不选择"), userData=None)
        for i in range(len(self.forgeryChallenge)):
            text = self.tr("{challenge} - {weapon} - {region}").format(
                challenge=self.i18ntr(self.forgeryChallenge[i]).raw,
                weapon=self.i18ntr(self.weapon[i % len(self.weapon)]).raw,
                region=self.i18ntr(self.guidebookRegionMap.get(self.forgeryChallenge[i])).raw,
            )
            self.forgeryChallengeComboBox.addItem(text, userData=self.forgeryChallenge[i])
            if i > len(self.weapon) * 3 - 1:
                self.forgeryChallengeComboBox.setItemEnabled(self.forgeryChallengeComboBox.count() - 1, False)
        # self.forgeryChallengeSettingButton = ToggleToolButton(FIF.SETTING, self)

        self.bossChallengeCheckBox = CheckBox(self.tr("共鸣者突破材料:"), self.container)
        self.bossChallengeComboBox = ComboBox(self.container)
        self.bossChallengeComboBox.addItem(self.tr("不选择"), userData=None)
        for i in range(len(self.bossChallenge)):
            self.bossChallengeComboBox.addItem(self.i18ntr(self.bossChallenge[i]).raw, userData=self.bossChallenge[i])
            if i > -1:
                self.bossChallengeComboBox.setItemEnabled(self.bossChallengeComboBox.count() - 1, False)
        # self.bossChallengeSettingButton = ToggleToolButton(FIF.SETTING, self)

        self.nightmarePurificationCheckBox = CheckBox(self.tr("梦魇聚落:"), self.container)
        self.nightmarePurificationComboBox = ComboBox(self.container)
        self.nightmarePurificationComboBox.addItem(self.tr("不选择"), userData=None)
        self.nightmarePurificationComboBox.addItem(self.tr("全选"), userData="All")
        self.nightmarePurificationComboBox.setItemEnabled(self.nightmarePurificationComboBox.count() - 1, False)
        for i in range(len(self.nightmarePurification)):
            self.nightmarePurificationComboBox.addItem(
                self.i18ntr(self.nightmarePurification[i]).raw,
                userData=self.nightmarePurification[i])
        # self.nightmarePurificationSettingButton = ToggleToolButton(FIF.SETTING, self)

        self.tacetDiscordNestCheckBox = CheckBox(self.tr("残象聚落:"), self.container)
        self.tacetDiscordNestComboBox = ComboBox(self.container)
        self.tacetDiscordNestComboBox.addItem(self.tr("不选择"), userData=None)
        self.tacetDiscordNestComboBox.addItem(self.tr("全选"), userData="All")
        for i in range(len(self.tacetDiscordNest)):
            text = self.tr("{challenge} - {region}").format(
                challenge=self.i18ntr(self.tacetDiscordNest[i]).raw,
                region=self.i18ntr(self.guidebookRegionMap.get(self.tacetDiscordNest[i])).raw,
            )
            self.tacetDiscordNestComboBox.addItem(text, userData=self.tacetDiscordNest[i])
        # self.tacetDiscordNestSettingButton = ToggleToolButton(FIF.SETTING, self)

        self.activityCheckBox = CheckBox(self.tr("活跃行迹:"), self.container)
        self.activityComboBox = ComboBox(self.container)
        # self.activityComboBox.addItem(self.tr("不选择"), userData=None)
        self.activityComboBox.addItem(self.tr("自动"), userData="Auto")
        # self.activitySettingButton = ToggleToolButton(FIF.SETTING, self)

        self.mailCheckBox = CheckBox(self.tr("邮件:"), self.container)
        self.mailComboBox = ComboBox(self.container)
        #         self.mailComboBox.addItem(self.tr("不选择"), userData=None)
        self.mailComboBox.addItem(self.tr("自动"), userData="Auto")
        # self.mailSettingButton = ToggleToolButton(FIF.SETTING, self)

        self.pioneerPodcastCheckBox = CheckBox(self.tr("先约电台:"), self.container)
        self.pioneerPodcastComboBox = ComboBox(self.container)
        #         self.pioneerPodcastComboBox.addItem(self.tr("不选择"), userData=None)
        self.pioneerPodcastComboBox.addItem(self.tr("自动"), userData="Auto")
        # self.pioneerPodcastSettingButton = ToggleToolButton(FIF.SETTING, self)

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

    def __refreshGridLayout(self, index):
        from src.core.i18n import I18nText, I18nTr, Language

        try:
            self.curLang = self.lang[index]
        except Exception:
            self.curLang = Language.ZH

        self.i18ntr = I18nTr(self.curLang)

        for idx in range(self.weeklyChallengeComboBox.count()):
            try:
                i = self.weeklyChallenge.index(self.weeklyChallengeComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.weeklyChallenge[i]).raw, boss=self.i18ntr(self.weeklyBoss[i]).raw)
            self.weeklyChallengeComboBox.setItemText(idx, text)

        for idx in range(self.tacetSuppressionComboBox.count()):
            try:
                i = self.tacetSuppression.index(self.tacetSuppressionComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.tacetSuppression[i]).raw, boss=self.i18ntr(self.tacetSuppression[i]).raw)
            self.tacetSuppressionComboBox.setItemText(idx, text)
            # _tipsList = self.tacetSuppressionTips[i]
            # _tips = ""
            # for x in range(len(_tipsList)):
            #     _tips += self.i18ntr(_tipsList[x])
            #     if x < len(_tipsList) - 1:
            #         _tips += "\n"
            # self.tacetSuppressionComboBox.setToolTip(_tips)

        for idx in range(self.forgeryChallengeComboBox.count()):
            try:
                i = self.forgeryChallenge.index(self.forgeryChallengeComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.forgeryChallenge[i]).raw, boss=self.i18ntr(self.forgeryChallenge[i]).raw)
            self.forgeryChallengeComboBox.setItemText(idx, text)

        for idx in range(self.bossChallengeComboBox.count()):
            try:
                i = self.bossChallenge.index(self.bossChallengeComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.bossChallenge[i]).raw, boss=self.i18ntr(self.bossChallenge[i]).raw)
            self.bossChallengeComboBox.setItemText(idx, text)

        for idx in range(self.nightmarePurificationComboBox.count()):
            try:
                i = self.nightmarePurification.index(self.nightmarePurificationComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.nightmarePurification[i]).raw,
                boss=self.i18ntr(self.nightmarePurification[i]).raw)
            self.nightmarePurificationComboBox.setItemText(idx, text)

        for idx in range(self.tacetDiscordNestComboBox.count()):
            try:
                i = self.tacetDiscordNest.index(self.tacetDiscordNestComboBox.itemData(idx))
            except Exception:
                i = -1
            if i == -1:
                continue
            text = self.tr("{challenge} - {boss}").format(
                challenge=self.i18ntr(self.tacetDiscordNest[i]).raw, boss=self.i18ntr(self.tacetDiscordNest[i]).raw)
            self.tacetDiscordNestComboBox.setItemText(idx, text)

    def __initWidget(self):
        # self.resize(1000, 800)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()
        self.__loadConfig()

    def __initLayout(self):
        self.contentBottomLayout.addWidget(self.resetButton)
        self.contentBottomLayout.addWidget(self.aboutButton)
        self.contentBottomLayout.addStretch()
        self.contentBottomLayout.setSpacing(15)
        self.contentBottomLayout.setContentsMargins(110, 0, 0, 0)

        # grid
        row = 0
        self.gridLayout.addWidget(self.weeklyChallengeCheckBox, row, 0)
        self.gridLayout.addWidget(self.weeklyChallengeComboBox, row, 1)
        # self.gridLayout.addWidget(self.weeklyChallengeSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.tacetSuppressionCheckBox, row, 0)
        self.gridLayout.addWidget(self.tacetSuppressionComboBox, row, 1)
        # self.gridLayout.addWidget(self.tacetSuppressionSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.forgeryChallengeCheckBox, row, 0)
        self.gridLayout.addWidget(self.forgeryChallengeComboBox, row, 1)
        # self.gridLayout.addWidget(self.forgeryChallengeSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.bossChallengeCheckBox, row, 0)
        self.gridLayout.addWidget(self.bossChallengeComboBox, row, 1)
        # self.gridLayout.addWidget(self.bossChallengeSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.tacetDiscordNestCheckBox, row, 0)
        self.gridLayout.addWidget(self.tacetDiscordNestComboBox, row, 1)
        # self.gridLayout.addWidget(self.tacetDiscordNestSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.nightmarePurificationCheckBox, row, 0)
        self.gridLayout.addWidget(self.nightmarePurificationComboBox, row, 1)
        # self.gridLayout.addWidget(self.nightmarePurificationSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.activityCheckBox, row, 0)
        self.gridLayout.addWidget(self.activityComboBox, row, 1)
        # self.gridLayout.addWidget(self.activitySettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.mailCheckBox, row, 0)
        self.gridLayout.addWidget(self.mailComboBox, row, 1)
        # self.gridLayout.addWidget(self.mailSettingButton, row, 2)

        row += 1
        self.gridLayout.addWidget(self.pioneerPodcastCheckBox, row, 0)
        self.gridLayout.addWidget(self.pioneerPodcastComboBox, row, 1)
        # self.gridLayout.addWidget(self.pioneerPodcastSettingButton, row, 2)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setHorizontalSpacing(10)
        # self.gridLayout.setVerticalSpacing(8)
        self.gridLayout.setAlignment(Qt.AlignVCenter)

        # column stretch
        self.gridLayout.setColumnStretch(0, 0)
        self.gridLayout.setColumnStretch(1, 0)
        # self.gridLayout.setColumnStretch(2, 1)
        # self.gridLayout.setColumnStretch(3, 0)  # button
        # self.gridLayout.setColumnStretch(4, 2)  # description（最大吃空间）

        self.mainLayout.addWidget(self.contentTitleLabel)
        self.mainLayout.addLayout(self.gridLayout)
        self.mainLayout.addLayout(self.contentBottomLayout)
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(36, 10, 36, 10)
        # self.mainLayout.setAlignment(Qt.AlignTop)

    def __connectSignalToSlot(self):
        self.weeklyChallengeCheckBox.toggled.connect(
            lambda checked: paramConfig.set(paramConfig.weeklyChallengeOpen, checked))
        for idx, cb in enumerate(self.buttonGroup):
            cb.toggled.connect(lambda checked, c=cb, i=idx: self.onCheckboxGroupChanged(c, i, checked))
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
        self.nightmarePurificationComboBox.currentIndexChanged.connect(
            lambda _: paramConfig.set(paramConfig.nightmarePurification,
                                      self.nightmarePurificationComboBox.currentData()))
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
        self.nightmarePurificationComboBox.setCurrentIndex(
            self.nightmarePurificationComboBox.findData(paramConfig.get(paramConfig.nightmarePurification)))
        self.tacetDiscordNestComboBox.setCurrentIndex(
            self.tacetDiscordNestComboBox.findData(paramConfig.get(paramConfig.tacetDiscordNest)))
        self.activityComboBox.setCurrentIndex(
            self.activityComboBox.findData(paramConfig.get(paramConfig.activity)))
        self.mailComboBox.setCurrentIndex(
            self.mailComboBox.findData(paramConfig.get(paramConfig.mail)))
        self.pioneerPodcastComboBox.setCurrentIndex(
            self.pioneerPodcastComboBox.findData(paramConfig.get(paramConfig.pioneerPodcast)))

    def __onResetButtonClicked(self):
        self.weeklyChallengeComboBox.setCurrentIndex(0)
        self.weeklyChallengeCheckBox.setChecked(False)

        self.tacetSuppressionComboBox.setCurrentIndex(0)
        self.tacetSuppressionCheckBox.setChecked(False)

        self.forgeryChallengeComboBox.setCurrentIndex(0)
        self.forgeryChallengeCheckBox.setChecked(False)

        self.bossChallengeComboBox.setCurrentIndex(0)
        self.bossChallengeCheckBox.setChecked(False)

        self.nightmarePurificationComboBox.setCurrentIndex(0)
        self.nightmarePurificationCheckBox.setChecked(False)

        self.tacetDiscordNestComboBox.setCurrentIndex(0)
        self.tacetDiscordNestCheckBox.setChecked(False)

        self.activityComboBox.setCurrentIndex(0)
        self.activityCheckBox.setChecked(False)

        self.mailComboBox.setCurrentIndex(0)
        self.mailCheckBox.setChecked(False)

        self.pioneerPodcastComboBox.setCurrentIndex(0)
        self.pioneerPodcastCheckBox.setChecked(False)

    def onCheckboxGroupChanged(self, cb, idx, checked):
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

    def __showAboutFlyout(self):
        Flyout.create(
            # icon=InfoBarIcon.INFORMATION,
            title='关于:',
            content=self.tr(
                '测试中，仅开放部分关卡。有问题及时群里反馈，最好录屏，或者截图游戏窗口和脚本日志，遮住uid。'
                '\n使用前建议关闭微星小飞机、英伟达统计数据、Mod等，避免遮挡游戏ui影响识别'
            ),
            target=self.aboutButton,
            parent=self.window()
        )
