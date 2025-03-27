import logging
import os
import traceback
import winreg
from typing import Optional, Dict, List

from omegaconf import OmegaConf
from pydantic import BaseModel, Field

from src.util import file_util

logger = logging.getLogger(__name__)

APP_CONFIG_PATH = str(file_util.get_project_root().joinpath("config.yaml"))


class AppConfig(BaseModel):
    # 脚本基础配置
    AppPath: Optional[str] = Field(None, title="游戏路径")
    # ModelName: Optional[str] = Field("yolo", title="模型的名称,默认是yolo.onnx")
    OcrInterval: float = Field(0.5, title="OCR间隔时间", ge=0)
    GameMonitorTime: int = Field(5, title="游戏窗口检测间隔时间")
    # project_root: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # LogFilePath: Optional[str] = Field(None, title="日志文件路径")

    # 游戏崩溃捕获及处理
    RestartWutheringWaves: bool = Field(
        False, title="定时重启游戏以避免游戏卡10%、75%等特殊进度"
    )
    RestartWutheringWavesTime: int = Field(7200, title="游戏自动重启间隔时间")
    RebootCount: int = Field(0, title="截取窗口失败次数")
    DetectionUE4: bool = Field(True, title="是否检测UE4崩溃")

    # 控制台信息
    EchoDebugMode: bool = Field(True, title="声骸锁定功能DEBUG显示输出的开关")
    EchoSynthesisDebugMode: bool = Field(
        True, title="声骸合成锁定功能DEBUG显示输出的开关"
    )

    # 自动战斗及声骸锁定配置
    MaxFightTime: int = Field(120, title="最大战斗时间")
    MaxIdleTime: int = Field(10, title="最大空闲时间", ge=5)
    MaxSearchEchoesTime: int = Field(18, title="最大搜索声骸时间")
    SelectRoleInterval: int = Field(2, title="选择角色间隔时间", ge=2)
    DungeonWeeklyBossLevel: int = Field(40, title="周本(副本)boss等级")
    BossWaitTime_Dreamless: float = Field(2.7, title="进入-无妄者-周本等待时间")
    BossWaitTime_Jue: float = Field(2, title="进入-角-周本等待时间")
    BossWaitTime_fallacy: float = Field(5, title="进入-无归的谬误-等待时间")
    BossWaitTime_sentry_construct: float = Field(2.5, title="进入-异构武装-等待时间")
    SearchEchoes: bool = Field(False, title="是否搜索声骸")
    # SearchDreamlessEchoes: bool = Field(True, title="是否搜索无妄者")
    CharacterHeal: bool = Field(True, title="是否判断角色是否阵亡")
    WaitUltAnimation: bool = Field(False, title="是否等待大招时间")
    EchoLock: bool = Field(False, title="是否启用锁定声骸功能")
    EchoLockConfig: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)
    EchoMaxContinuousLockQuantity: int = Field(
        5, title="最大连续检测到已锁定声骸的数量"
    )

    # 战斗策略
    TargetBoss: list[str] = Field([], title="目标关键字")
    FightTactics: list[str] = Field(
        [
            "e,q,r,a,0.1,a,0.1,a,0.1,a,0.1,a,0.1",
            "e,q,r,a~0.5,0.1,a,0.1,a,0.1,a,0.1,a,0.1",
            "e~0.5,q,r,a,0.1,a,0.1,a,0.1,a,0.1,a,0.1",
        ],
        title="战斗策略 三个角色的释放技能顺序, 逗号分隔, e,q,r为技能, a为普攻(默认连点0.3秒), 数字为间隔时间,a~0.5为普攻按下0.5秒,a(0.5)为连续普攻0.5秒",
    )
    FightTacticsUlt: list[str] = Field(
        [
            "a(1.6),e,a(1.6),e,a(1.6)",
            "a(1.6),e,a(1.6),e,a(1.6)",
            "a(1.2),e",
        ],
        title="大招释放成功时的技能释放顺序",
    )
    FightOrder: list[int] = Field([1, 2, 3],
                                  title="战斗顺序，123为角色在编队和战斗策略中的位置，调整可使维里奈在编队3号位也可以先连招")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.AppPath:
            self.AppPath = get_wuthering_waves_path()

    def __str__(self):
        return self.model_dump_json(indent=4)

    @staticmethod
    def build(config_path: str | None = None) -> "AppConfig":
        if not config_path:
            config_path = APP_CONFIG_PATH
        data = OmegaConf.load(config_path)
        app_config = AppConfig.model_validate(data)
        logger.debug(app_config)
        return app_config


def get_wuthering_waves_path():
    key = None
    # 打开注册表项
    # key_path = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\KRInstall Wuthering Waves"

    key_paths = [
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\KRInstall Wuthering Waves",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\KRInstall Wuthering Waves Overseas",
    ]

    for key_path in key_paths:
        key = open_registry_key(key_path)

        if key:
            try:
                # 读取安装路径
                install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                if install_path:
                    # 构造完整的程序路径
                    program_path = os.path.join(
                        install_path, "Wuthering Waves Game", "Wuthering Waves.exe"
                    )
                    # print(f"从注册表中加载到游戏目录：{program_path}")
                    return program_path
            except Exception as e:
                logger.error("获取游戏安装路径错误: %s", traceback.format_exc())
            finally:
                if "key" in locals():
                    key.Close()

    return None


# 获取鸣潮游戏路径
def open_registry_key(key_path):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        return key
    except FileNotFoundError:
        logger.error(f"未找到注册表路径'{key_path}'")
    except Exception as e:
        logger.error(f"访问注册表错误: {traceback.format_exc()}")
    return None
