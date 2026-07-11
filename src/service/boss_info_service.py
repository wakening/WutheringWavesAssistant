import logging

from src.core.boss import BossNameEnum, RouteStep, Direction, MoveMode, RestartParam
from src.core.interface import BossInfoService

logger = logging.getLogger(__name__)

# 传送boss后的移动方式配置
FAST_TRAVEL_ROUTES: dict[str, list[RouteStep]] = {
    BossNameEnum.Dreamless.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=5)],
    BossNameEnum.FallacyOfNoReturn.value: [
        RouteStep(direction=Direction.RIGHT, mode=MoveMode.WALK, steps=3),
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.0),  # 5.5
    ],
    BossNameEnum.LampylumenMyriad.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=2.6)],
    # 3.6
    BossNameEnum.BellBorneGeochelone.value: [
        RouteStep(direction=Direction.RIGHT, mode=MoveMode.WALK, steps=3),
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=3.0),  # 3.6
    ],
    BossNameEnum.InfernoRider.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=3.5)],  # 4.2
    BossNameEnum.ImpermanenceHeron.value: [
        RouteStep(direction=Direction.RIGHT, mode=MoveMode.WALK, steps=2),
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=3.0),  # 4.0
    ],
    BossNameEnum.MechAbomination.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=6.8)],
    BossNameEnum.MourningAix.value: [
        RouteStep(direction=Direction.LEFT, mode=MoveMode.WALK, steps=2),
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.0),  # 4.8
    ],
    BossNameEnum.ThunderingMephis.value: [
        RouteStep(direction=Direction.LEFT, mode=MoveMode.WALK, steps=2),
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=2.5),  # 3.2
    ],
    BossNameEnum.TempestMephis.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=2.4)],  # 3.0
    BossNameEnum.FeilianBeringal.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=6.0)],
    BossNameEnum.Crownless.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=2.1)],  # 2.7
    BossNameEnum.Jue.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=4)],
    BossNameEnum.SentryConstruct.value: [
        RouteStep(direction=Direction.LEFT, mode=MoveMode.WALK, steps=2),
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=3.2),  # 4.0
    ],
    BossNameEnum.Hecate.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=4)],
    BossNameEnum.Lorelei.value: [
        RouteStep(direction=Direction.LEFT, mode=MoveMode.WALK, steps=2),
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=3.7),  # 4.5
    ],
    BossNameEnum.DragonOfDirge.value: [
        RouteStep(direction=Direction.RIGHT, mode=MoveMode.WALK, steps=3),
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.8),  # 5.6
    ],
    BossNameEnum.NightmareFeilianBeringal.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=1.0)],
    BossNameEnum.NightmareImpermanenceHeron.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=5.3)],
    BossNameEnum.NightmareTempestMephis.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.8)],
    BossNameEnum.NightmareThunderingMephis.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=3.2)],
    BossNameEnum.NightmareCrownless.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=3.0)],
    BossNameEnum.NightmareInfernoRider.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.5)],
    BossNameEnum.NightmareMourningAix.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=3.6)],
    BossNameEnum.NightmareLampylumenMyriad.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=2.6)],
    BossNameEnum.Fleurdelys.value: [],
    BossNameEnum.NightmareKelpie.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=5.2)],
    BossNameEnum.LionessOfGlory.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=1.8)],  # 2.6
    BossNameEnum.NightmareHecate.value: [RouteStep(direction=Direction.LEFT, mode=MoveMode.WALK, steps=4)],
    BossNameEnum.Fenrico.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=0.85)],  # 3.4
    BossNameEnum.LadyOfTheSea.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=7)],
    BossNameEnum.TheFalseSovereign.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=2.5)],
    BossNameEnum.ThrenodianLeviathan.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=3)],
    BossNameEnum.Hyvatia.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.5)],  # 8
    BossNameEnum.ReactorHusk.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.8)],
    BossNameEnum.Sigillum.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=3)],
    BossNameEnum.NamelessExplorer.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=1.4)],  # 3.2
    # BossNameEnum.SeedOfIllusoryOrigin.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=5)],
    BossNameEnum.Denia.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=5)],
    # BossNameEnum.NightmareAdamSmasherLimitedTime.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.WALK, steps=3)],
    BossNameEnum.NightmareAdamSmasher.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=0.5)],
    # BossNameEnum.MyriadSnareRustfireChassisLimitedTime.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=0.5)],
    BossNameEnum.MyriadSnareRustfireChassis.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=4.6)],
    # BossNameEnum.CourtOfShackledSouls.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=0.5)],
    BossNameEnum.ThousandPuppetPavilion.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=0.5)],
}

# RouteStep后的移动方式配置，没有的也留痕注释掉，方便后续排查
RESTART_PARAMS: dict[str, RestartParam] = {
    # BossNameEnum.Dreamless.value: RestartParam(check_text=None, direction=None, routes=None, cycle=20, step=2),
    BossNameEnum.FallacyOfNoReturn.value: RestartParam(
        check_text=None, direction=None, cycle=20, step=2, check_health_bar=True),
    BossNameEnum.LampylumenMyriad.value: RestartParam(check_text=r"击败", direction=None, cycle=14, step=2),
    BossNameEnum.BellBorneGeochelone.value: RestartParam(check_text=r"击败", direction=None, cycle=20, step=2),
    BossNameEnum.InfernoRider.value: RestartParam(check_text=r"击败", direction=None, cycle=20, step=2),
    BossNameEnum.ImpermanenceHeron.value: RestartParam(
        check_text=r"击败", direction=None, cycle=14, step=2, check_health_bar=True),
    # BossNameEnum.MechAbomination.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.MourningAix.value: RestartParam(check_text=r"击败", direction=None, cycle=14, step=2),
    BossNameEnum.ThunderingMephis.value: RestartParam(
        check_text=r"击败", direction=None, cycle=14, step=2, check_health_bar=True),
    BossNameEnum.TempestMephis.value: RestartParam(check_text=r"击败", direction=None, cycle=14, step=2),
    # BossNameEnum.FeilianBeringal.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.Crownless.value: RestartParam(
        check_text=None, direction=None, cycle=14, step=2,
        restart_text=r"^(声弦|Resonance\s*Cord|重新挑战|Restart)$"),
    # BossNameEnum.Jue.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.SentryConstruct.value: RestartParam(
        check_text=r"击败", direction=None, cycle=14, step=2, check_health_bar=True),
    # BossNameEnum.Hecate.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.Lorelei.value: RestartParam(
        check_text=r"击败", direction=None, cycle=14, step=2, check_health_bar=True),
    BossNameEnum.DragonOfDirge.value: RestartParam(
        check_text=None, direction=None, cycle=20, step=2, check_health_bar=True),
    # BossNameEnum.NightmareFeilianBeringal.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.NightmareImpermanenceHeron.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.NightmareTempestMephis.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.NightmareThunderingMephis.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.NightmareCrownless.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.NightmareInfernoRider.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.NightmareMourningAix.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.NightmareLampylumenMyriad.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.Fleurdelys.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    # BossNameEnum.NightmareKelpie.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.LionessOfGlory.value: RestartParam(
        check_text=None, direction=None, cycle=14, step=2, check_health_bar=True),
    # BossNameEnum.NightmareHecate.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.Fenrico.value: RestartParam(check_text=None, direction=None, cycle=14, step=2),
    BossNameEnum.LadyOfTheSea.value: RestartParam(
        check_text=None, direction=None, cycle=8, step=1, restart_text=r"^进入.*最终章.*$"),
    BossNameEnum.TheFalseSovereign.value: RestartParam(
        check_text=None, direction=None, cycle=12, step=2, check_health_bar=True),
    # BossNameEnum.ThrenodianLeviathan.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.Hyvatia.value: RestartParam(
        check_text=r"击败|海维夏$", direction=None, cycle=20, step=2, check_health_bar=True),
    BossNameEnum.ReactorHusk.value: RestartParam(
        check_text=None, direction=None, cycle=20, step=2, check_health_bar=True),
    # BossNameEnum.Sigillum.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.NamelessExplorer.value: RestartParam(
        check_text=None, direction=Direction.FORWARD, cycle=20, step=2, check_health_bar=True),
    # BossNameEnum.SeedOfIllusoryOrigin.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.Denia.value: RestartParam(
        check_text=None, direction=None, cycle=8, step=1, restart_text=r"^进入声之"),
    # BossNameEnum.NightmareAdamSmasherLimitedTime.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.NightmareAdamSmasher.value: RestartParam(
        check_text=None, direction=None, cycle=8, step=1, restart_text=r"进入"),
    # BossNameEnum.MyriadSnareRustfireChassisLimitedTime.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.MyriadSnareRustfireChassis.value: RestartParam(
        check_text=r"击败", direction=None, cycle=25, step=2, check_health_bar=True),
    # BossNameEnum.CourtOfShackledSouls.value: RestartParam(check_text=None, direction=None, cycle=20, step=2),
    BossNameEnum.ThousandPuppetPavilion.value: RestartParam(
            check_text=None, direction=None, cycle=8, step=1, restart_text=r"^进入声之"),
}

# 点击重新挑战后的移动方式配置，适用于个别boss刷新位置离重新挑战点较远的情况，有才写
AFTER_RESTART_ROUTES: dict[str, list[RouteStep]] = {
    BossNameEnum.Fenrico.value: [RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=(3.4 - 1.5))],
    BossNameEnum.NamelessExplorer.value: [
        RouteStep(direction=Direction.FORWARD, mode=MoveMode.RUN, duration=0.7)],
}


class BossInfoServiceImpl(BossInfoService):

    def __init__(self):
        self._boss_name_map_zh_en: dict[str, str] = {member.value: member.name for member in BossNameEnum}

    def get_boss_name_zh_en(self, boss_name_zh: str) -> str:
        return self._boss_name_map_zh_en.get(boss_name_zh)


    def is_nightmare(self, boss_name: str) -> bool:
        """
        是否是梦魇boss
        :param boss_name:
        :return:
        """
        if not boss_name:
            return False
        if boss_name in [
            BossNameEnum.NightmareAdamSmasherLimitedTime.value,
            BossNameEnum.NightmareAdamSmasher.value,
        ]:
            return False
        return boss_name.startswith("梦魇")

    def is_auto_pickup(self, boss_name: str) -> bool:
        """
        是否需要自动拾取，如梦魇boss
        :param boss_name:
        :return:
        """
        if not boss_name:
            return False
        if boss_name in [
            BossNameEnum.Fenrico.value,
            BossNameEnum.LadyOfTheSea.value,
            BossNameEnum.TheFalseSovereign.value,
            BossNameEnum.Hyvatia.value,
            BossNameEnum.ReactorHusk.value,
            BossNameEnum.Sigillum.value,
            BossNameEnum.NamelessExplorer.value,
            BossNameEnum.SeedOfIllusoryOrigin.value,
            BossNameEnum.Denia.value,
            BossNameEnum.NightmareAdamSmasherLimitedTime.value,
            BossNameEnum.NightmareAdamSmasher.value,
            # BossNameEnum.MyriadSnareRustfireChassisLimitedTime.value,
            # BossNameEnum.MyriadSnareRustfireChassis.value,
            BossNameEnum.CourtOfShackledSouls.value,
            BossNameEnum.ThousandPuppetPavilion.value,
        ]:
            return True
        return self.is_nightmare(boss_name)

    def get_fast_travel_routes(self) -> dict[str, list[RouteStep]]:
        """ 获取角色快速旅行后需要执行的路径相关参数 """
        return FAST_TRAVEL_ROUTES

    def get_restart_params(self) -> dict[str, RestartParam]:
        """ 获取重新挑战相关移动参数 """
        return RESTART_PARAMS

    def get_after_restart_routes(self) -> dict[str, list[RouteStep]]:
        """ 获取点击重新挑战后需要再次移动的参数 """
        return AFTER_RESTART_ROUTES

