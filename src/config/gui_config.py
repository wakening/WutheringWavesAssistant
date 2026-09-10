import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict

from src.core.boss import BossNameEnum
from src.util import winreg_util

logger = logging.getLogger(__name__)


class ParamConfig(BaseModel):
    """ 有两个同名类，一个是gui目录下前端用的，一个是这个后台用的 """
    bossName: list[str] | None = Field(None, alias="bossName")
    bossLevel: str | None = Field(None, alias="bossLevel")
    autoRestartPeriod: str | None = Field(None, alias="autoRestartPeriod")
    gamePath: str | None = Field(None, alias="gamePath",
                                 description="游戏路径，不做处理默认可能是枚举值Auto，可使用get函数动态获取")
    autoCombatBeta: bool | None = Field(None, alias="autoCombatBeta")

    # SoarToTheBeat
    defaultTemplate: str | None = Field(None, alias="defaultTemplate")
    userTemplate: str | None = Field(None, alias="userTemplate")
    useUserTemplate: bool | None = Field(None, alias="useUserTemplate")


    model_config = ConfigDict(populate_by_name=True)

    def __str__(self):
        return self.model_dump_json(indent=4)

    def get_game_path(self):
        if not self.gamePath or self.gamePath == "Auto":
            game_path = self.get_default_game_path()
        else:
            game_path = self.gamePath
        logger.debug("Get game path: %s", game_path)
        return game_path

    @staticmethod
    def snapshot(path_str: str):
        """ 加载配置为json字符串 """
        try:
            path = Path(path_str)
            if not path.exists() or not path.is_file():
                logger.debug("Path does not exist: %s", path_str)
                return ""
        except Exception:
            return ""
        # logger.debug("Path exist: %s", path_str)
        with open(path_str, "r", encoding="utf-8") as f:
            data = f.read()
        logger.debug("Param config: %s", data)
        return data

    @staticmethod
    def pre_date(data) -> dict:
        pre_data = {}
        if not data:
            return pre_data
        bossRush = data.get("BossRush", {})
        pre_data["bossName"] = bossRush.get("BossName")
        pre_data["bossLevel"] = "Auto"
        pre_data["autoRestartPeriod"] = bossRush.get("AutoRestartPeriod")
        pre_data["autoCombatBeta"] = True

        soarToTheBeat = data.get("SoarToTheBeat", {})
        pre_data["defaultTemplate"] = soarToTheBeat.get("DefaultTemplate")
        pre_data["useUserTemplate"] = soarToTheBeat.get("UseUserTemplate")
        pre_data["userTemplate"] = soarToTheBeat.get("UserTemplate")

        pre_data["gamePath"] = data.get("Game", {}).get("GamePath")
        return pre_data

    @classmethod
    def build(cls, *, path: str | None = None, content: str | None = None):
        if path:
            logger.debug("Param config path: %s", path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pre_data = cls.pre_date(data)
            config = cls.model_validate(pre_data)
        elif content:
            logger.debug("Param config content: %s", content)
            data = json.loads(content)
            pre_data = cls.pre_date(data)
            config = cls.model_validate(pre_data)
        else:
            config = cls(bossName=None, bossLevel=None, autoRestartPeriod=None, gamePath=None, autoCombatBeta=None)
        logger.debug(config)
        return config

    @classmethod
    def get_default_game_path(cls):
        return winreg_util.get_install_path()

    def get_boss_name_list(self):
        boss_names = []
        if not self.bossName:
            boss_names.append(BossNameEnum.Dreamless.value)
            return boss_names
        for boss_name in self.bossName:
            boss_names.append(BossNameEnum[boss_name].value)
        return boss_names

    def get_boss_level_int(self):
        if self.bossLevel and self.bossLevel != "Auto":
            return int(self.bossLevel)
        return 40


if __name__ == '__main__':
    test_content = """{
    "BossRush": {
        "AutoRestartPeriod": "0#10#0",
        "BossLevel": "80",
        "BossName": [
            "NightmareInfernoRider",
            "NightmareMourningAix",
            "NightmareLampylumenMyriad",
            "NightmareThunderingMephis",
            "NightmareTempestMephis",
            "NightmareImpermanenceHeron",
            "NightmareCrownless",
            "NightmareFeilianBeringal"
        ]
    },
    "Game": {
        "GamePath": "D:/Program Files/Wuthering Waves Oversea/Wuthering Waves/Wuthering Waves Game/Wuthering Waves.exe"
    }
}"""
    test_param_config = ParamConfig.build(content=test_content)
    print(test_param_config)

    test_param_config = ParamConfig.model_validate(json.loads(test_content))
    print(test_param_config)

    test_param_config = ParamConfig.model_validate(ParamConfig.pre_date(json.loads(test_content)))
    print(test_param_config)
