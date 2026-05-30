from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from src.config.app_config import AppConfig
from src.config.echo_config import EchoModel
from src.config.gui_config import ParamConfig
from src.config.keyboard_mapping_config import KeyboardMappingConfig
from src.util import file_util


class ConfigV1(BaseModel):
    """ 所有的配置 """
    model_config = {"arbitrary_types_allowed": True}
    app: AppConfig = Field(default_factory=AppConfig.build, title="应用配置，旧版，仅旧版自动战斗在用")
    echo: EchoModel = Field(default_factory=EchoModel.build, title="声骸词条配置",
                            description="配置声骸合成和锁定需要的词条")
    keyboard_mapping: KeyboardMappingConfig = Field(default_factory=KeyboardMappingConfig, title="游戏内按键映射")
    param: ParamConfig = Field(default_factory=ParamConfig.build, title="新版参数配置")


def alias_generator(name: str) -> str:
    """
    gameLanguage -> GameLanguage
    bossRush -> BossRush
    """
    return name[0].upper() + name[1:]


class ConfigBase(BaseModel):
    model_config = ConfigDict(
        extra="ignore",  # 忽略未知字段
        populate_by_name=True,  # 支持字段名和别名
        alias_generator=alias_generator,
        frozen=True,
    )

    _path: Path | None = None  # 配置文件路径，不导出到 JSON

    @property
    def path(self) -> Path | None:
        return self._path

    # ---------- 加载 ----------

    @classmethod
    def from_dict(cls, data: dict):
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, json_str: str):
        return cls.model_validate_json(json_str)

    @classmethod
    def load(cls, path: str | Path):
        path = Path(path)
        conf = cls.from_json(path.read_text(encoding="utf-8"))
        conf._path = path
        return conf

    # ---------- 导出 ----------

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True)

    def to_json(self) -> str:
        return self.model_dump_json(
            by_alias=True,
            indent=4,
        )

    def save(self, path: str | Path):
        Path(path).write_text(
            self.to_json(),
            encoding="utf-8",
        )


class BossRushConfig(ConfigBase):
    autoCombatBetaV2: bool | None = None
    autoRestartPeriod: str | None = None
    bossLevel: str | None = None
    bossName: list[str] | None = None


class DailyConfig(ConfigBase):
    weeklyChallenge: str | None = None
    weeklyChallengeOpen: bool | None = None
    tacetSuppression: str | None = None
    tacetSuppressionOpen: bool | None = None
    forgeryChallenge: str | None = None
    forgeryChallengeOpen: bool | None = None
    simulationChallenge: str | None = None
    simulationChallengeOpen: bool | None = None
    bossChallenge: str | None = None
    bossChallengeOpen: bool | None = None
    nightmarePurification: str | None = None
    nightmarePurificationOpen: bool | None = None
    tacetDiscordNest: str | None = None
    tacetDiscordNestOpen: bool | None = None
    activity: str | None = None
    activityOpen: bool | None = None
    mail: str | None = None
    mailOpen: bool | None = None
    pioneerPodcast: str | None = None
    pioneerPodcastOpen: bool | None = None


class GameConfig(ConfigBase):
    gameLanguage: str | None = None
    gamePath: str | None = None


class SoarToTheBeatConfig(ConfigBase):
    defaultTemplate: str | None = None
    useUserTemplate: bool | None = None
    userTemplate: str | None = None


class Config(ConfigBase):
    bossRush: BossRushConfig = Field(default_factory=BossRushConfig)
    daily: DailyConfig = Field(default_factory=DailyConfig)
    game: GameConfig = Field(default_factory=GameConfig)
    soarToTheBeat: SoarToTheBeatConfig = Field(default_factory=SoarToTheBeatConfig)

    @classmethod
    def load_user_config(cls) -> 'Config':
        path = file_util.get_temp_config("param-config.json")
        return cls.load(path)
