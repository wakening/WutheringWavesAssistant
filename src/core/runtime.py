import logging
from enum import Enum
from functools import cached_property
from pathlib import Path

from src.config.config import Config, BossRushConfig, DailyConfig, GameConfig, SoarToTheBeatConfig
from src.core.boss import BossNameEnum
from src.core.i18n import I18nText, Language
from src.util import winreg_util

logger = logging.getLogger(__name__)


# =========================================================
# 运行态配置，由全局配置解析转化而来，仅内部使用
# 全局配置字段类型多为 字符串 | None
# 运行态配置字段有明确且可直接使用的类型，如bool、int、list类型
# =========================================================


class BossRushRuntimeConfig:

    def __init__(self, cfg: BossRushConfig):
        self._cfg: BossRushConfig = cfg

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

    @cached_property
    def autoCombat(self) -> bool:
        if self._cfg.autoCombatBetaV2 is None:
            return True
        return self._cfg.autoCombatBetaV2

    @cached_property
    def restartInterval(self) -> int:
        """ 获取定时重启时间 秒，为空则是关闭定时 """
        if not self._cfg.autoRestartPeriod or self._cfg.autoRestartPeriod == "Close":
            return -1
        try:
            # 定时重启开启时间，格式: 时#分#秒 或 Close
            period = self._cfg.autoRestartPeriod.strip().split("#")
            restart_interval = 3600 * int(period[0]) + 60 * int(period[1]) + int(period[2])
            if restart_interval > 10:
                logger.info(f"Scheduled game restart enabled, interval: {restart_interval}")
                return restart_interval
            logger.warning(f"Restart interval too short: {restart_interval}, auto-disabling")
        except Exception:
            pass
        return -1

    @cached_property
    def bossLevel(self) -> int:
        if not self._cfg.bossLevel:
            return -1
        level = None
        try:
            level = int(self._cfg.bossLevel)
        except Exception:
            pass
        if not level or level not in [40, 50, 60, 70, 80, 90]:
            logger.warning(f"Invalid boss level: {level}")
            return -1
        return level

    @cached_property
    def bossName(self) -> list[str]:
        if not self._cfg.bossName:
            return [I18nText.EnemyDreamless]
        try:
            idx = self._cfg.bossName.index("SeedOfLllusoryOrigin")
            self._cfg.bossName[idx] = I18nText.SeedOfIllusoryOrigin
        except Exception:
            pass
        enemies = BossNameEnum.enemies()
        if not set(enemies).issubset(set(self._cfg.bossName)):
            raise ValueError(f"Invalid boss name in list: '{self._cfg.bossName}'")
        return list(dict.fromkeys(self._cfg.bossName))


class DailyRuntimeConfig:

    def __init__(self, cfg: DailyConfig):
        self._cfg: DailyConfig = cfg
        self.weeklyChallenge: bool = bool(cfg.weeklyChallenge)
        self.weeklyChallengeOpen: bool = bool(cfg.weeklyChallengeOpen)
        self.tacetSuppression: bool = bool(cfg.tacetSuppression)
        self.tacetSuppressionOpen: bool = bool(cfg.tacetSuppressionOpen)
        self.forgeryChallenge: bool = bool(cfg.forgeryChallenge)
        self.forgeryChallengeOpen: bool = bool(cfg.forgeryChallengeOpen)
        self.simulationChallenge: bool = bool(cfg.simulationChallenge)
        self.simulationChallengeOpen: bool = bool(cfg.simulationChallengeOpen)
        self.bossChallenge: bool = bool(cfg.bossChallenge)
        self.bossChallengeOpen: bool = bool(cfg.bossChallengeOpen)
        self.nightmarePurification: bool = bool(cfg.nightmarePurification)
        self.nightmarePurificationOpen: bool = bool(cfg.nightmarePurificationOpen)
        self.tacetDiscordNest: bool = bool(cfg.tacetDiscordNest)
        self.tacetDiscordNestOpen: bool = bool(cfg.tacetDiscordNestOpen)
        self.activity: bool = bool(cfg.activity)
        self.activityOpen: bool = bool(cfg.activityOpen)
        self.mail: bool = bool(cfg.mail)
        self.mailOpen: bool = bool(cfg.mailOpen)
        self.pioneerPodcast: bool = bool(cfg.pioneerPodcast)
        self.pioneerPodcastOpen: bool = bool(cfg.pioneerPodcastOpen)

        self.__init_weeklyChallenge()
        self.__init_tacetSuppression()
        self.__init_forgeryChallenge()
        self.__init_simulationChallenge()
        self.__init_bossChallenge()
        self.__init_nightmarePurification()
        self.__init_tacetDiscordNest()

    def __init_weeklyChallenge(self):
        self.seedOfIllusoryOrigin: bool = self._cfg.weeklyChallenge == I18nText.SeedOfIllusoryOrigin
        self.gateOfTheLostStar: bool = self._cfg.weeklyChallenge == I18nText.GateOfTheLostStar
        self.cinderniteApocalypse: bool = self._cfg.weeklyChallenge == I18nText.CinderniteApocalypse
        self.theWheelOfBrokenFate: bool = self._cfg.weeklyChallenge == I18nText.TheWheelOfBrokenFate
        self.beyondTheCrimsonCurtain: bool = self._cfg.weeklyChallenge == I18nText.BeyondTheCrimsonCurtain
        self.theFatedConfrontation: bool = self._cfg.weeklyChallenge == I18nText.TheFatedConfrontation
        self.statueOfTheCrownless: bool = self._cfg.weeklyChallenge == I18nText.StatueOfTheCrownless
        self.chaoticJuncture: bool = self._cfg.weeklyChallenge == I18nText.ChaoticJuncture
        self.bellOfArchaicChants: bool = self._cfg.weeklyChallenge == I18nText.BellOfArchaicChants

    def __init_tacetSuppression(self):
        self.westernFangPeaksTacetField: bool = self._cfg.tacetSuppression == I18nText.WesternFangPeaksTacetField
        self.easternXuanPeaksTacetField: bool = self._cfg.tacetSuppression == I18nText.EasternXuanPeaksTacetField
        self.tacetFieldSolisiaLanding: bool = self._cfg.tacetSuppression == I18nText.TacetFieldSolisiaLanding
        self.tacetFieldFrostlandsTransitPort: bool = self._cfg.tacetSuppression == I18nText.TacetFieldFrostlandsTransitPort
        self.tacetFieldMountGjallar: bool = self._cfg.tacetSuppression == I18nText.TacetFieldMountGjallar
        self.tacetFieldMawburrowDesert: bool = self._cfg.tacetSuppression == I18nText.TacetFieldMawburrowDesert
        self.tacetFieldStagnantRun: bool = self._cfg.tacetSuppression == I18nText.TacetFieldStagnantRun

    def __init_forgeryChallenge(self):
        self.fallenSanctum: bool = self._cfg.forgeryChallenge == I18nText.FallenSanctum
        self.lessonInSunset: bool = self._cfg.forgeryChallenge == I18nText.LessonInSunset
        self.strickenSanctum: bool = self._cfg.forgeryChallenge == I18nText.StrickenSanctum
        self.lessonInVoid: bool = self._cfg.forgeryChallenge == I18nText.LessonInVoid
        self.lessonInEmbers: bool = self._cfg.forgeryChallenge == I18nText.LessonInEmbers
        self.gardenOfSalvation: bool = self._cfg.forgeryChallenge == I18nText.GardenOfSalvation
        self.abyssOfInitiation: bool = self._cfg.forgeryChallenge == I18nText.AbyssOfInitiation
        self.gardenOfAdoration: bool = self._cfg.forgeryChallenge == I18nText.GardenOfAdoration
        self.abyssOfSacrifice: bool = self._cfg.forgeryChallenge == I18nText.AbyssOfSacrifice
        self.abyssOfConfession: bool = self._cfg.forgeryChallenge == I18nText.AbyssOfConfession
        self.flamingRemnants: bool = self._cfg.forgeryChallenge == I18nText.FlamingRemnants
        self.mistyForest: bool = self._cfg.forgeryChallenge == I18nText.MistyForest
        self.erodedRuins: bool = self._cfg.forgeryChallenge == I18nText.ErodedRuins
        self.moonlitGroves: bool = self._cfg.forgeryChallenge == I18nText.MoonlitGroves
        self.marigoldWoods: bool = self._cfg.forgeryChallenge == I18nText.MarigoldWoods

    def __init_simulationChallenge(self):
        pass

    def __init_bossChallenge(self):
        pass

    def __init_nightmarePurification(self):
        pass

    def __init_tacetDiscordNest(self):
        _all = "All"
        self.southernYuanHillsTacetDiscordNest: bool = self._cfg.tacetDiscordNest in [
            _all, I18nText.SouthernYuanHillsTacetDiscordNest]
        self.starblindCrashsiteTacetDiscordNest: bool = self._cfg.tacetDiscordNest in [
            _all, I18nText.StarblindCrashsiteTacetDiscordNest]
        self.rebirthUplandsTacetDiscordNest: bool = self._cfg.tacetDiscordNest in [
            _all, I18nText.RebirthUplandsTacetDiscordNest]
        self.stagnantRunTacetDiscordNest: bool = self._cfg.tacetDiscordNest in [
            _all, I18nText.StagnantRunTacetDiscordNest]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


class Device(str, Enum):
    Auto = "Auto"
    CUDA = "CUDA"
    CPU = "CPU"

    def is_gpu(self):
        return self in [Device.Auto, Device.CUDA]

    def is_cpu(self):
        return not self.is_gpu()


class GameRuntimeConfig:

    def __init__(self, cfg: GameConfig):
        self._cfg: GameConfig = cfg

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

    @cached_property
    def gameLanguage(self) -> Language:
        lang = Language.ZH
        if self._cfg.gameLanguage:
            try:
                lang = Language(self._cfg.gameLanguage)
            except Exception:
                logger.warning(f"Invalid game language: '{self._cfg.gameLanguage}', using default: {lang}")
                return lang
        logger.info(f"Using game language: '{lang}'")
        return lang

    @cached_property
    def gamePath(self) -> Path | None:
        gamePath = self._cfg.gamePath
        if gamePath and gamePath != "Auto":
            try:
                path = Path(gamePath)
                if path.is_file():
                    logger.info(f"Using game path: '{path}'")
                    return path
            except Exception:
                pass
            logger.warning(f"Invalid game path: '{gamePath}'")

        gamePath = winreg_util.get_install_path()
        if gamePath:
            try:
                path = Path(gamePath)
                if path.is_file():
                    logger.info(f"Using game path: '{path}'")
                    return path
            except Exception:
                pass
        logger.warning(f"Invalid game path: '{gamePath}'")
        return None

    @cached_property
    def device(self) -> Device:
        device = self._cfg.device
        if not device:
            return Device.Auto
        try:
            device = Device(device)
        except Exception:
            logger.warning(f"Invalid device: '{self._cfg.device}', using default: {Device.Auto}")
            return Device.Auto
        logger.info(f"Device: '{device.value}'")
        return device


class SoarToTheBeatRuntimeConfig:

    def __init__(self, cfg: SoarToTheBeatConfig):
        self._cfg: SoarToTheBeatConfig = cfg
        self.defaultTemplate: str | None = cfg.defaultTemplate
        self.useUserTemplate: bool | None = cfg.useUserTemplate
        self.userTemplate: str | None = cfg.userTemplate

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


class RuntimeConfig:

    def __init__(self, cfg):
        self._cfg: Config = self.format_config(cfg)
        self.bossRush: BossRushRuntimeConfig = BossRushRuntimeConfig(self._cfg.bossRush)
        self.daily: DailyRuntimeConfig = DailyRuntimeConfig(self._cfg.daily)
        self.game: GameRuntimeConfig = GameRuntimeConfig(self._cfg.game)
        self.soarToTheBeat: SoarToTheBeatRuntimeConfig = SoarToTheBeatRuntimeConfig(self._cfg.soarToTheBeat)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

    @staticmethod
    def format_config(cfg: Config | dict | str | None) -> Config:
        if not cfg:
            # gui提交的任务都有，pytest等提交的可能没有
            logger.warning(f"Using default config because cfg is: '{cfg}'")
            cfg = Config.load_user_config()
        elif isinstance(cfg, dict):
            cfg = Config.from_dict(cfg)
        elif isinstance(cfg, str):
            cfg = Config.from_json(cfg)
        return cfg
