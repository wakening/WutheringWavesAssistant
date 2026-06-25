# coding:utf-8
import json
import logging
import sys
from copy import deepcopy
from datetime import datetime
from enum import Enum, EnumMeta
from pathlib import Path
from typing import List

from PySide6.QtCore import QLocale, QObject, Signal
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, EnumSerializer,
                            exceptionHandler, ConfigValidator)
from src import __version__
from src.gui.common.boss import BossNameEnum
from src.gui.common.globals import globalSignal

logger = logging.getLogger(__name__)


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    """ Config of application """

    # # folders
    # musicFolders = ConfigItem(
    #     "Folders", "LocalMusic", [], FolderListValidator())
    # downloadFolder = ConfigItem(
    #     "Folders", "Download", "app/download", FolderValidator())

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    windowSize = OptionsConfigItem(
        "MainWindow", "WindowSize", "Default", OptionsValidator(["720x720", "Default"]), restart=False)
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # # Material
    # blurRadius  = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))

    # software update
    # checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", False, BoolValidator())
    checkUpdateAtStartUpV2 = ConfigItem("Update", "CheckUpdateAtStartUpV2", True, BoolValidator())


YEAR = datetime.now().year
AUTHOR = "wakening"
VERSION = __version__
HELP_URL = "https://github.com/wakening/WutheringWavesAssistant?tab=readme-ov-file#-%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97"
REPO_URL = "https://github.com/wakening/WutheringWavesAssistant"
EXAMPLE_URL = "https://github.com/wakening"
FEEDBACK_URL = "https://github.com/wakening/WutheringWavesAssistant/issues"
RELEASE_URL = "https://github.com/wakening/WutheringWavesAssistant/releases/latest"
ZH_SUPPORT_URL = "https://afdian.com/a/wakening"
EN_SUPPORT_URL = "https://afdian.com/a/wakening"
CHANGELOG_URL = "https://github.com/wakening/WutheringWavesAssistant/CHANGELOG.md" # TODO terminal

VERSION_URLS = [
    "https://ghfast.top/https://raw.githubusercontent.com/wakening/WutheringWavesAssistant/main/src/__init__.py",
    "https://cdn.jsdelivr.net/gh/wakening/WutheringWavesAssistant@main/src/__init__.py",
    "https://raw.githubusercontent.com/wakening/WutheringWavesAssistant/main/src/__init__.py",
]


cfg = Config()
cfg.themeMode.value = Theme.AUTO
# qconfig.load('temp/config/config.json', cfg)
_qconfigPath = str(Path(__file__).parent.parent.parent.parent.joinpath('temp/config/config.json'))
qconfig.load(_qconfigPath, cfg)


class BossNameListValidator(ConfigValidator):
    """ Enum list validator """

    def __init__(self, enumMeta: EnumMeta): # EnumMeta是枚举类的元类，指枚举类本身（不是成员），Enum则是指枚举类的成员
        self._enumMeta = enumMeta
        self.names = list(enumMeta.__members__.keys())

    def validate(self, value):
        return value.name in self.names

    def correct(self, values: list):
        enumList = []
        for v in values:
            if isinstance(v, str) and v in self.names:
                enumList.append(self._enumMeta[v])
            elif isinstance(v, self._enumMeta):
                enumList.append(v)
        return enumList

class BossNameListSerializer(ConfigSerializer):
    """ enumeration class serializer """

    def __init__(self, enumClass):
        self.enumClass = enumClass

    def serialize(self, values: list[Enum]):
        enumList = [value.name for value in values]
        # logger.debug(enumList)
        return enumList

    def deserialize(self, values: list[str]):
        enumList = [self.enumClass[value] for value in values]
        # logger.debug(enumList)
        return enumList

class GameFolderValidator(ConfigValidator):

    def validate(self, value):
        if value == "Auto":
            return True
        return Path(value).exists()

    def correct(self, value):
        if value == "Auto":
            return value
        path = Path(value)
        return str(path.absolute()).replace("\\", "/").replace("\\\\", "/")

class ParamConfig(QConfig):
    """ Config of parameters """

    # Boss
    bossName = ConfigItem(
        "BossRush", "BossName", [BossNameEnum.Dreamless], BossNameListValidator(BossNameEnum), BossNameListSerializer(BossNameEnum))
    # Weekly Challenge
    bossLevel = OptionsConfigItem(
        "BossRush", "BossLevel", "Auto", OptionsValidator(["40", "50", "60", "70", "80", "90", "Auto"]))

    autoCombat = ConfigItem("BossRush", "AutoCombatBetaV2", True, BoolValidator())

    autoRestartPeriod = ConfigItem("BossRush", "AutoRestartPeriod", 'Close')

    # macroReplaySoarToTheBeat
    soarToTheBeat_DefaultTemplate = ConfigItem("SoarToTheBeat", "DefaultTemplate", None)
    soarToTheBeat_UserTemplate = ConfigItem("SoarToTheBeat", "UserTemplate", None)
    soarToTheBeat_UseUserTemplate = ConfigItem("SoarToTheBeat", "UseUserTemplate", False, BoolValidator())

    # Daily
    weeklyChallenge = ConfigItem("Daily", "WeeklyChallenge", None)
    weeklyChallengeOpen = ConfigItem("Daily", "WeeklyChallengeOpen", False, BoolValidator())
    tacetSuppression = ConfigItem("Daily", "TacetSuppression", None)
    tacetSuppressionOpen = ConfigItem("Daily", "TacetSuppressionOpen", False, BoolValidator())
    forgeryChallenge = ConfigItem("Daily", "ForgeryChallenge", None)
    forgeryChallengeOpen = ConfigItem("Daily", "ForgeryChallengeOpen", False, BoolValidator())
    bossChallenge = ConfigItem("Daily", "BossChallenge", None)
    bossChallengeOpen = ConfigItem("Daily", "BossChallengeOpen", False, BoolValidator())
    nightmarePurification = ConfigItem("Daily", "NightmarePurification", None)
    nightmarePurificationOpen = ConfigItem("Daily", "NightmarePurificationOpen", False, BoolValidator())
    tacetDiscordNest = ConfigItem("Daily", "TacetDiscordNest", None)
    tacetDiscordNestOpen = ConfigItem("Daily", "TacetDiscordNestOpen", False, BoolValidator())
    activity = ConfigItem("Daily", "Activity", "Auto")
    activityOpen = ConfigItem("Daily", "ActivityOpen", False, BoolValidator())
    mail = ConfigItem("Daily", "Mail", "Auto")
    mailOpen = ConfigItem("Daily", "MailOpen", False, BoolValidator())
    pioneerPodcast = ConfigItem("Daily", "PioneerPodcast", "Auto")
    pioneerPodcastOpen = ConfigItem("Daily", "PioneerPodcastOpen", False, BoolValidator())

    # Game
    gameLanguage = ConfigItem("Game", "GameLanguage", None)
    gamePath = ConfigItem("Game", "GamePath", "Auto", GameFolderValidator())
    device = ConfigItem("Game", "Device", None, OptionsValidator([None, "GPU", "CPU"]))


    def save(self):
        """ Save config, excluding certain fields """
        # 获取字典并排除某些字段
        config_dict = self._cfg.toDict()

        # 排除字段
        fields_to_exclude = ['QFluentWidgets']
        filtered_dict = {key: value for key, value in config_dict.items() if key not in fields_to_exclude}

        # 保存过滤后的字典
        self._cfg.file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._cfg.file, "w", encoding="utf-8") as f:
            json.dump(filtered_dict, f, ensure_ascii=False, indent=4)


def getParamFilePath():
    return str(Path(__file__).parent.parent.parent.parent.joinpath('temp/config/param-config.json'))


paramConfig = ParamConfig()
paramConfigPath = getParamFilePath()
paramConfig.load(paramConfigPath)
logger.debug(str(paramConfig.toDict()))
globalSignal.paramConfigPathSignal.emit(paramConfigPath)
