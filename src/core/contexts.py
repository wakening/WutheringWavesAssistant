import logging
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field, PrivateAttr

from src.config.config import Config

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

    echoIsLockQuantity: int = Field(0, title="检测到连续锁定的声骸数量")
    echoNumber: int = Field(0, title="当前进行的锁定声骸个数")
    inSpecEchoQuantity: int = Field(0, title="检测到的符合配置的声骸数量")
    synthesisGoldQuantity: int = Field(0, title="合成声骸数量")
    synthesisTimes: int = Field(0, title="声骸合成次数")
    inSpecSynthesisEchoQuantity: int = Field(0, title="合成的符合配置的声骸数量")
    needOpenDataMerge: bool = Field(True, title="是否要打开数据融合")
    dataMergeFinish: bool = Field(False, title="数据融合是否完成")
    bagIsOpen: bool = Field(False, title="背包是否打开")


class EchoContext:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Context(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    config: Config = Field(default_factory=Config, title="所有配置文件")
    boss_task_ctx: BossTaskContext = Field(default_factory=BossTaskContext, title="刷boss声骸上下文")
    _container = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.boss_task_ctx.lastFightTime = datetime.now() + timedelta(seconds=self.config.app.MaxIdleTime / 2)

    def __str__(self):
        return self.model_dump_json(indent=4)


if __name__ == '__main__':
    print(Context())
