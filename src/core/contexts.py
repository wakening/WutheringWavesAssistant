import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr

from src.config.app_config import AppConfig
from src.config.config import ConfigV1
from src.config.gui_config import ParamConfig
from src.core.workflow import TaskSpec

logger = logging.getLogger(__name__)


class Status(Enum):
    idle = "空闲"
    fight = "战斗"


class BossTaskContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    roleIndex: int = Field(0, title="角色索引")
    bossIndex: int = Field(0, title="boss索引")
    status: Status = Field(Status.idle, title="状态")
    fightTime: datetime = Field(default_factory=datetime.now, title="战斗开始时间")
    fightCount: int = Field(0, title="战斗次数")
    absorptionCount: int = Field(0, title="吸收次数")
    absorptionSuccess: bool = Field(False, title="吸收成功")
    needAbsorption: bool = Field(False, title="需要吸收")
    lastFightTime: datetime = Field(default_factory=datetime.now, title="最近检测到战斗时间")
    idleTime: datetime = Field(default_factory=datetime.now, title="空闲时间")
    startTime: datetime = Field(default_factory=datetime.now, title="开始时间")
    lastSelectRoleTime: datetime = Field(default_factory=datetime.now, title="最近选择角色时间")
    # currentPageName: str = Field("", title="当前页面名称")
    in_dungeon: bool = Field(False, title="是否在无妄者/角/赫卡忒这种独立副本内")
    # inDreamless: bool = Field(False, title="是否在无妄者副本内")
    # inJue: bool = Field(False, title="是否在角副本内")
    # inHecate: bool = Field(False, title="是否在赫卡忒副本内")
    lastBossName: str = Field("", title="最近BOSS名称")
    healCount: int = Field(0, title="治疗次数")
    needHeal: bool = Field(False, title="需要治疗")
    isCheckedHeal: bool = Field(False, title="是否检查过需要治疗")
    waitBoss: bool = Field(True, title="等待Boss时间")
    DungeonWeeklyBossLevel: int = Field(0, title="储存自动判断出的最低可获奖励副本BOSS的等级")
    resetRole: bool = Field(False, title="重置选择角色")
    adaptsType: int = Field(None, title="适配类型")
    # adaptsResolution: str = Field(None, title="适配分辨率")

    # challengeSuccess: bool = Field(False, title="是否挑战成功")
    # lastChallengeSuccessTime: datetime = Field(default_factory=datetime.now, title="上次挑战成功的时间")
    challengeFenricoCount: int = Field(0, title="挑战芬莱克次数")
    gui_win_id: int | None = Field(None, title="gui的pid")

    echoIsLockQuantity: int = Field(0, title="检测到连续锁定的声骸数量")
    echoNumber: int = Field(0, title="当前进行的锁定声骸个数")
    inSpecEchoQuantity: int = Field(0, title="检测到的符合配置的声骸数量")
    synthesisGoldQuantity: int = Field(0, title="合成声骸数量")
    synthesisTimes: int = Field(0, title="声骸合成次数")
    inSpecSynthesisEchoQuantity: int = Field(0, title="合成的符合配置的声骸数量")
    needOpenDataMerge: bool = Field(True, title="是否要打开数据融合")
    dataMergeFinish: bool = Field(False, title="数据融合是否完成")
    bagIsOpen: bool = Field(False, title="背包是否打开")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.lastFightTime = datetime.now() + timedelta(seconds=config.MaxIdleTime / 2)
        self.lastFightTime = datetime.now() + timedelta(seconds=5)


class EchoContext:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Context(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    config: ConfigV1 = Field(default_factory=ConfigV1, title="所有配置文件")
    boss_task_ctx: BossTaskContext = Field(default_factory=BossTaskContext, title="刷boss声骸上下文")
    spec: TaskSpec = None
    _container: Any = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.boss_task_ctx.lastFightTime = datetime.now() + timedelta(seconds=self.config.app.MaxIdleTime / 2)

    def __str__(self):
        return self.model_dump_json(indent=4)

    @property
    def app_config(self) -> AppConfig:
        return self.config.app

    @property
    def param_config(self) -> ParamConfig:
        return self.config.param

    @param_config.setter
    def param_config(self, value: ParamConfig):
        self.config.param = value


# class TaskCtx(BaseModel):
#     model_config = {"arbitrary_types_allowed": True}
#
# class CombatContext(TaskCtx):
#
#     # boss
#     bossIndex: int = Field(0)
#     bossName: str | None = Field(None)
#     lastBossName: str | None = Field(None)
#     inInstance: bool = Field(False)
#
#     # role
#     roleIndex: str | None = Field(None)
#
#     # Metrics
#     reviveCount: int = Field(0)
#     combatCount: int = Field(0)
#     echoCount: int = Field(0)
#     rewardCount: int = Field(0)
#
#     def toggle_boss(self):
#         pass
#
#
#
# if __name__ == '__main__':
#     print(Context())

# CombatTracker
# CombatStats
# CombatSession
# CombatMetrics
# CombatContext
# CombatSnapshot