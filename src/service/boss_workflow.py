import logging
import random
import re
import time
from typing import Optional

from src.core.color import ColorRule, Color, ColorMatch
from src.core.combat.combat_core import Morph
from src.core.combat.combat_system import CombatSystem
from src.core.enemy import Enemy, EnemyHpBar, EnemyMeta
from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind, Point
from src.core.i18n import I18nText, I18nTr, Language
from src.core.message import MsgType, MsgTaskStatus, MsgSource
from src.core.movement import Run, Walk, RouteExecutor
from src.core.pages import UIOp, GlobalPage
from src.core.resonator import Resonator, TeamMember
from src.core.resource import Icon, Resource
from src.core.task import TaskFSM, TaskStatus, TaskFSMGroup
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow
from src.service.common_workflow import search_icon_guidebook, RoiEx, RateLimiter, ObjectDetector, Slider, AsyncPickup
from src.util import img_util
from src.util.img_sift_util import SIFTFeatureMatcher

logger = logging.getLogger(__name__)


class TaskLocal:

    def __init__(self):
        self.teamFSM: TaskFSM = TaskFSM(name=I18nText.Team)

        self.rootFSM: TaskFSMGroup = TaskFSMGroup(
            self.teamFSM,
            name="Root"
        )

        # cfg
        self.enemy: EnemyMeta = None

        # runtime
        self.pattern = re.compile(r"[·_-]")
        self.downed = False
        self.members = ["unknown", None, None]
        self.combat_system: CombatSystem = None
        self.combat_count = 1
        self.absorb_count = 0

        # TODO 战斗计数、吸收计数、复苏计数、阵亡计数


class NodeName:
    globalDispatcher = "globalDispatcher"
    rootDispatcher = "rootDispatcher"
    endNode = "endNode"

    # rootDispatcher
    doTeam = "doTeam"
    doGuidebook = "doGuidebook"
    doMail = "doMail"
    doPioneerPodcast = "doPioneerPodcast"

    # doTeam
    doTravelToResonanceNexus = "doTravelToResonanceNexus"

    # doGuidebook
    doActivity = "doActivity"
    doMaterialCollection = "doMaterialCollection"
    doRecurringChallenges = "doRecurringChallenges"
    doPathOfGrowth = "doPathOfGrowth"
    doEnemyTracing = "doEnemyTracing"
    doMilestones = "doMilestones"

    # doMaterialCollection
    doForgeryChallenge = "doForgeryChallenge"
    doSimulationChallenge = "doSimulationChallenge"
    doBossChallenge = "doBossChallenge"
    doTacetSuppression = "doTacetSuppression"
    doWeeklyChallenge = "doWeeklyChallenge"
    doNightmarePurification = "doNightmarePurification"
    doTacetDiscordNest = "doTacetDiscordNest"

    doCombat = "doCombat"


@node(NodeName.endNode)
def endNode(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.rootFSM.is_finished:
        ctx.runtime.taskFSM.complete()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
        ctx.ipc.event_queue.put({
            "task": {"AutoBossProcessTask": "finished"}
        }, block=True)
    else:
        ctx.runtime.taskFSM.fail()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.FAILED)
        ctx.ipc.event_queue.put({
            "task": {"AutoBossProcessTask": "failed"}
        }, block=True)
    time.sleep(0.1)
    return True


@node(NodeName.globalDispatcher)
def globalDispatcher(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """检查是否在有效页面（如：终端），不在则esc尝试离开（副本等）"""
    ui = UIOp(ctx)
    ui.activate().sleep(0.1).snapshot()

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"{ui.bbox_result}")

    page = GlobalPage(ctx)

    # 已在终端页
    if page.isTerminal(ui=ui):
        return I18nText.Terminal

    # 在全局预设中找出离开函数，尝试回到主页
    if page.action(ui=ui):
        ui.sleep(0.5)
        return None

    logger.info("Transferring")

    num = max(1, min(1.4, random.gauss(1.2, 0.08)))
    # 兜底规则，esc
    ui.esc().sleep(num)
    return None


@node(NodeName.rootDispatcher)
def rootDispatcher(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    if local.teamFSM.is_active:
        return I18nText.Team
    if local.downed:
        return I18nText.ResonatorDowned
    return I18nText.Guidebook


@node(NodeName.doTravelToResonanceNexus)
def doTravelToResonanceNexus(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    """去往信标，用于复活队友、脱战等"""
    ui = UIOp(ctx)
    ui.snapshot()

    # 防止失败卡流程，重置状态，少人也能打
    local.downed = False

    # 从终端进入地图
    if GlobalPage(ctx).isTerminal(ui=ui):
        if not ui.click_text(ctx.tr(I18nText.Map), RoiEx(ctx).terminal_content, delay=0.2, times=2, interval=0.3):
            ui.click_point(AnchorPoint(1197, 350, Align.Right | Align.Middle))
            if not ui.sleep(0.3).wait().until(
                    lambda: ui.snapshot().click_text(ctx.tr(I18nText.Map), delay=0.3, times=2, interval=0.3)):
                ui.esc().sleep(1)
                return False
    else:
        # 大世界进入地图
        ctx.control_service.map()

    # 点击切换地图
    if not ui.sleep(0.5).wait(10, 0.4).until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.SwitchMap), delay=0.8)):
        return False

    # 选择瑝珑-今州
    regions_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(600, 0, Align.Right | Align.Top), AnchorPoint(925, 720, Align.Right | Align.Bottom)))
    for i in range(3):
        if i == 2:
            return False
        if not ui.sleep(0.3).wait().until(
                lambda: ui.snapshot().search(
                    ctx.tr([I18nText.Huanglong, I18nText.Mengzhou, I18nText.Jinzhou]), regions_roi)):
            logger.warning(f"Text not found: {ctx.tr(I18nText.Huanglong).raw}")
            return False
        ui.sleep(0.4).snapshot()  # 修复文字未显示完全就识别导致少字，等动画结束，重新识别
        if ui.search(ctx.tr(I18nText.Mengzhou)) or ui.search(ctx.tr(I18nText.Jinzhou)):
            ui.click_text(ctx.tr(I18nText.Mengzhou), regions_roi, delay=0.4, times=2, interval=0.2)
            ui.click_text(ctx.tr(I18nText.Jinzhou), regions_roi, delay=0.1, times=2, interval=0.2)
            break
        elif ui.click_text(ctx.tr(I18nText.Huanglong), regions_roi, delay=0.4):
            ui.sleep(0.35)
            continue
        return False

    # 选择今州城
    regions_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(915, 0, Align.Right | Align.Top), AnchorPoint(1280, 720, Align.Right | Align.Bottom)))
    if not ui.sleep(0.5).wait().until(
            lambda: ui.snapshot().click_text(
                ctx.tr(I18nText.JinzhouCity), regions_roi, delay=0.4, times=2, interval=0.2)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.JinzhouCity).raw}")
        return False

    # 点击今州城传送点
    tmpl_name = "8_0_-1.png"
    tmpl_img = img_util.read_img(Resource.Map.Huanglong.Jinzhou / "8_0_-1.png")
    scene_img = ui.sleep(0.8).grap()
    matcher = SIFTFeatureMatcher()
    feature_data = matcher.build_feature_data(tmpl_name, tmpl_img)
    result = matcher.match(scene_img, feature_data)
    if result is None:
        logger.warning("Feature match failed")
        return False
    # (466, 309)
    point = Point(433, 187)
    scene_point = matcher.feature_to_scene(result, (float(point.x), float(point.y)))
    logger.debug(f"模板点 {point} 映射到场景坐标: ({scene_point[0]:.1f}, {scene_point[1]:.1f})")
    ui.click(int(scene_point[0]), int(scene_point[1]))
    if not ui.sleep(0.5).wait().until(
            lambda: ui.snapshot().click_text(ctx.tr(I18nText.FastTravel), delay=0.3, times=2, interval=0.3)):
        return False

    ui.sleep(2).wait_back_home()
    ui.sleep(1.0)
    return True


@node(NodeName.doTeam)
def doTeam(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool | None:
    """获取编队角色名"""
    if local.teamFSM.is_terminal:
        return True
    if local.teamFSM.status == TaskStatus.PENDING:
        local.teamFSM.start()

    ui = UIOp(ctx)
    ui.activate().sleep(0.1).snapshot()

    # 终端
    if not GlobalPage(ctx).isTerminal(ui=ui):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Terminal).raw}")
        ui.esc().sleep(1)
        return None

    # 点击进入编队
    if not ui.click_text(ctx.tr(I18nText.Team), RoiEx(ctx).terminal_content, pk=PointKind.NEAR, times=2, interval=0.2):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Team).raw}")
        return False

    roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(700, 625, Align.Right | Align.Bottom),
        AnchorPoint(1280, 720, Align.Right | Align.Bottom)
    ))
    if ui.sleep(0.8).wait().until(
            lambda: ui.snapshot().search(ctx.tr(I18nText.QuickSetup), roi) or ui.search(ctx.tr(
                [I18nText.CannotPerformThisActionDuringBattle, I18nText.CannotAdjustTheTeamLineupInTheCurrentState]))):
        if not ui.search(ctx.tr(I18nText.QuickSetup), roi):
            logger.info(f"Team locked")
            return False

    # 检查失去意识
    roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Left | Align.Top),
        AnchorPoint(1280, 450, Align.Right | Align.Middle)
    ))
    if ui.search(ctx.tr(I18nText.ResonatorDowned), roi):
        logger.info(f"resonator downed")
        local.downed = True

    # 识别编队角色
    member_keys = TeamMember.get_members_by_text(ui)
    members = [local.pattern.sub("", ctx.tr(key).raw) if key else key for key in member_keys]
    logger.info(f"Team: {members}")
    # 识别到至少一个角色才更新编队
    if any(members):
        local.member_keys = member_keys
        local.members = members

    local.teamFSM.complete()
    ui.esc().sleep(1)
    return True


@node(NodeName.doGuidebook)
def doGuidebook(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """索拉指南"""
    ui = UIOp(ctx)

    # 终端
    if not GlobalPage(ctx).isTerminal(ui=ui.snapshot()):
        return None
    # 点击进入索拉指南
    if not ui.click_text(ctx.tr(I18nText.Guidebook), RoiEx(ctx).terminal_content,
                         pk=PointKind.NEAR, delay=0.2, times=2, interval=0.2):
        logger.warning(f"Text not found: {ctx.tr(I18nText.Guidebook).raw}")
        return None

    # 进入索拉指南后，默认是 活跃度 或 素材获取页
    activity = ctx.tr(I18nText.Activity)
    materialCollection = ctx.tr(I18nText.MaterialCollection)
    recurringChallenges = ctx.tr(I18nText.RecurringChallenges)
    pathOfGrowth = ctx.tr(I18nText.PathOfGrowth)
    enemyTracing = ctx.tr(I18nText.EnemyTracing)
    milestones = ctx.tr(I18nText.Milestones)

    titles = [activity, materialCollection, recurringChallenges, pathOfGrowth, enemyTracing, milestones]
    roiex = RoiEx(ctx)

    if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().search(titles, roiex.guidebook_title)):
        logger.warning(f"Page not found: {ctx.tr(I18nText.Guidebook).raw}")
        return None

    enemy = local.enemy
    enemy_name = ctx.tr(local.enemy.id)
    logger.debug(f"Enemy: {enemy}, {enemy_name.raw}")

    # 选择刷取入口
    # TODO 容错？直接挑战找不到就去敌迹探寻

    def _click_icon(_icon, _keyword):
        icon_point = None
        for _ in range(2):
            if icon_point := search_icon_guidebook(ctx, icon=_icon):
                break
            ui.sleep(0.3)
        if not icon_point:
            logger.warning(f"{_keyword.raw} icon not found")
            return False
        # 点击侧边栏图标
        ui.click_point(icon_point, times=2, interval=0.3)
        if not ui.sleep(0.1).wait().until(lambda: ui.snapshot().search(_keyword, roiex.guidebook_title)):
            return False
        return True

    # 从素材获取菜单进
    if enemy.prefer_quick:
        if not ui.search(materialCollection, roiex.guidebook_title) and not _click_icon(
                Icon.materialCollection(), materialCollection):
            return None

        return I18nText.MaterialCollection

    # 从敌迹探寻菜单进
    if not _click_icon(Icon.enemyTracing(), enemyTracing):
        return None
    if not ui.search(ctx.tr(I18nText.EnemyTracingSearch), roiex.guidebook_menu) and not ui.wait().until(
            lambda: ui.snapshot().search(enemyTracing, roiex.guidebook_title)
                    and ui.search(ctx.tr(I18nText.EnemyTracingSearch), roiex.guidebook_menu)):
        return None

    return I18nText.EnemyTracing


@node(NodeName.doMaterialCollection)
def doMaterialCollection(ctx: NodeContext, local: TaskLocal, **kwargs) -> str:
    """素材获取 可直接挑战boss"""
    menu_key = local.enemy.quick_boss_meta.menu

    if menu_key not in [I18nText.BossChallenge, I18nText.WeeklyChallenge, I18nText.NightmarePurification]:
        raise NotImplementedError(f"Unsupported menu: {ctx.tr(menu_key).raw}")

    logger.info(f"{ctx.tr(menu_key).raw}: {ctx.tr(local.enemy.id).raw}")
    return menu_key


@node(NodeName.doBossChallenge)
def doBossChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    ui = UIOp(ctx)

    roiex = RoiEx(ctx)
    enemy = local.enemy
    enemy_name = ctx.tr(local.enemy.id)
    menu = ctx.tr(enemy.quick_boss_meta.menu)
    logger.debug(f"Enemy: {enemy_name.raw}")

    # 点击讨伐强敌
    if not ui.sleep(0.2).wait().until(
            lambda: ui.snapshot().click_text(menu, roiex.guidebook_menu, times=2, interval=0.3)
                    and ui.search(ctx.tr(I18nText.FilterToViewRewardsForEachPhase))):
        return False

    # 滑动寻找入口
    slider_points = Slider.points(ui.grap())
    for i, p in enumerate(slider_points):
        if i > 0:
            logger.debug(f"Scroll point: {p}")
            ui.click_point(p, times=2, interval=0.2)
            ui.sleep(0.2).snapshot()
        else:
            ui.snapshot()
        if not (enemy_text := ui.search(enemy_name, roiex.guidebook_content)):
            continue
        if not (challenge_list := ui.search(ctx.tr(I18nText.Challenge), roiex.guidebook_content)):
            continue
        challenge_list.sort(key=lambda x: x.y1)
        if enemy_text[0].y1 > challenge_list[-1].y2:
            continue
        if not (challenge_text := next((cl for cl in challenge_list if enemy_text[0].y1 < cl.y2), None)):
            return False
        # 当前页面最底下，按钮可能只有一半无法点击，再翻一页
        if challenge_text.y2 == challenge_list[-1].y2 and i < len(slider_points) - 1:
            continue
        ui.click_bbox(challenge_text, times=2, interval=0.3)

        # 点击提示弹窗
        if not ui.sleep(0.2).wait().until(
                lambda: ui.snapshot().search(ctx.tr(I18nText.ArrivingAtTheDestination))
                        and ui.click_text(ctx.tr(I18nText.Confirm), delay=0.3, times=2, interval=0.2)
                        or ui.search(ctx.tr(I18nText.QuickSetup))
                        and ui.click_text(ctx.tr(I18nText.StartChallenge), times=3, interval=0.3)):
            return False

        # 等待进入副本
        if not ui.sleep(2).wait_back_home():
            return False

        return True

    logger.warning(f"Enemy not found: {enemy_name.raw}")
    return False


@node(NodeName.doWeeklyChallenge)
def doWeeklyChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    ui = UIOp(ctx)

    roiex = RoiEx(ctx)
    enemy = local.enemy
    enemy_name = ctx.tr(local.enemy.id)
    menu = ctx.tr(enemy.quick_boss_meta.menu)
    logger.debug(f"Enemy: {enemy_name.raw}")

    # 点击战歌重奏
    if not ui.sleep(0.2).wait().until(
            lambda: ui.snapshot().click_text(menu, roiex.guidebook_menu, times=2, interval=0.3)
                    and ui.search(ctx.tr(I18nText.RemainingWeeklyAttempts))):
        return False

    # 滑动寻找入口
    dungeon_name = ctx.tr(enemy.quick_boss_meta.dungeon_name)
    slider_points = Slider.points(ui.grap())
    for i, p in enumerate(slider_points):
        if i > 0:
            logger.debug(f"Scroll point: {p}")
            ui.click_point(p, times=2, interval=0.2)
            ui.sleep(0.2).snapshot()
        else:
            ui.snapshot()
        if not (enemy_text := ui.search(dungeon_name, roiex.guidebook_content)):
            continue
        if not (challenge_list := ui.search(ctx.tr(I18nText.Challenge), roiex.guidebook_content)):
            continue
        challenge_list.sort(key=lambda x: x.y1)
        if enemy_text[0].y1 > challenge_list[-1].y2:
            continue
        if not (challenge_text := next((cl for cl in challenge_list if enemy_text[0].y1 < cl.y2), None)):
            return False
        # 当前页面最底下，按钮可能只有一半无法点击，再翻一页
        if challenge_text.y2 == challenge_list[-1].y2 and i < len(slider_points) - 1:
            continue
        ui.click_bbox(challenge_text, times=2, interval=0.3)

        def _wait_suggested_lv():
            if ui.snapshot().search(ctx.tr(I18nText.WeeklySuggestedLv)) and ui.search(
                    ctx.tr(I18nText.WeeklySoloChallenge)):
                return True
            if ui.search(ctx.tr(I18nText.ArrivingAtTheDestination)):
                ui.click_text(ctx.tr(I18nText.Confirm), delay=0.3, times=2, interval=0.2)
            return False

        # 点击提示弹窗
        if not ui.sleep(0.2).wait(6, 0.3).until(_wait_suggested_lv):
            return False

        # 选择最佳推荐等级
        img = ui.sleep(0.2).grap()
        lv_points: list[Point] = []
        best_lv = None
        for j, lv in enumerate(range(40, 91, 10)):
            p_lv = ctx.scaler.as_point(AnchorPoint(125, 125 + j * (160 - 104), Align.Left | Align.Top))
            if ColorRule().points(p_lv).colors(Color.bgr(88, 85, 77)).match(img, ctx.scaler):
                if len(lv_points) > 0:
                    best_lv = lv_points[-1]
                    logger.info(f"{ctx.tr(I18nText.WeeklySuggestedLv).raw}: {lv - 10}")
                break
            lv_points.append(p_lv)
        if best_lv:
            ui.click_point(best_lv, times=2, interval=0.2)

        # 点击单人挑战
        if not ui.sleep(0.1).click_text(ctx.tr(I18nText.WeeklySoloChallenge)):
            return False
        # 点击开启挑战
        if not ui.sleep(0.2).wait().until(
                lambda: ui.snapshot().search(ctx.tr(I18nText.QuickSetup))
                        and ui.click_text(ctx.tr(I18nText.StartChallenge), times=3, interval=0.3)):
            return False
        # 等待进入副本
        if not ui.sleep(2).wait_back_home():
            return False

        return True

    logger.warning(f"Enemy not found: {enemy_name.raw}")
    return False


@node(NodeName.doNightmarePurification)
def doNightmarePurification(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    ui = UIOp(ctx)

    roiex = RoiEx(ctx)
    enemy = local.enemy
    enemy_name = ctx.tr(local.enemy.id)
    menu = ctx.tr(enemy.quick_boss_meta.menu)
    logger.debug(f"Enemy: {enemy_name.raw}")

    # 点击梦魇祓除
    if not ui.wait().until(
            lambda: ui.click_point(AnchorPoint(458, 636, Align.Top | Align.Left), times=2, interval=0.2)
                    and ui.sleep(0.2).snapshot().click_text(menu, roiex.guidebook_menu, times=2, interval=0.3)
                    and ui.search(ctx.tr(I18nText.SonataSetFilter))):
        return False

    # 滑动寻找入口
    slider_points = Slider.points(ui.grap())
    for i, p in enumerate(slider_points):
        if i > 0:
            logger.debug(f"Scroll point: {p}")
            ui.click_point(p, times=2, interval=0.2)
            ui.sleep(0.2).snapshot()
        else:
            ui.snapshot()
        if not (enemy_text := ui.search(enemy_name, roiex.guidebook_content)):
            continue
        if not (challenge_list := ui.search(ctx.tr(I18nText.Challenge), roiex.guidebook_content)):
            continue
        challenge_list.sort(key=lambda x: x.y1)
        if enemy_text[0].y1 > challenge_list[-1].y2:
            continue
        if not (challenge_text := next((cl for cl in challenge_list if enemy_text[0].y1 < cl.y2), None)):
            return False
        # 当前页面最底下，按钮可能只有一半无法点击，再翻一页
        if challenge_text.y2 == challenge_list[-1].y2 and i < len(slider_points) - 1:
            continue
        ui.click_bbox(challenge_text, times=2, interval=0.3)

        # 点击提示弹窗
        if not ui.sleep(0.2).wait().until(
                lambda: ui.snapshot().search(ctx.tr(I18nText.ArrivingAtTheDestination))
                        and ui.click_text(ctx.tr(I18nText.Confirm), delay=0.3, times=2, interval=0.2)
                        or ui.search(ctx.tr(I18nText.QuickSetup))
                        and ui.click_text(ctx.tr(I18nText.StartChallenge), times=3, interval=0.3)):
            return False

        # 等待进入副本
        if not ui.sleep(2).wait_back_home():
            return False

        return True

    logger.warning(f"Enemy not found: {enemy_name.raw}")
    return False


@node(NodeName.doEnemyTracing)
def doEnemyTracing(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    ui = UIOp(ctx)

    roiex = RoiEx(ctx)
    enemy_name = ctx.tr(local.enemy.id)
    logger.debug(f"Enemy: {enemy_name.raw}")

    # 检查是否在敌迹探寻，双击搜索
    if not ui.snapshot().search(ctx.tr(I18nText.EnemyTracing), roiex.guidebook_title) or not ui.click_text(
            ctx.tr(I18nText.EnemyTracingSearch), roiex.guidebook_menu, times=2, interval=0.2):
        return False

    # 搜索敌人
    ui.sleep(0.1)
    ctx.control_service.input_text(f"^{local.pattern.sub(".", enemy_name.raw)}$")
    ui.sleep(0.2)
    ctx.control_service.enter()

    # 点击敌人
    bbox_first_enemy = AnchorBBox(
        AnchorPoint(145, 134, Align.Left | Align.Top),
        AnchorPoint(430, 196, Align.Left | Align.Top)
    )
    ui.click_bbox(bbox_first_enemy, pk=PointKind.NEAR, delay=0.2, times=2, interval=0.3)

    # 点击探测
    if ui.sleep(0.1).snapshot().search(ctx.tr(I18nText.NoDetectableResult)):
        logger.warning(f"{ctx.tr(I18nText.NoDetectableResult).raw}")
        return False
    if not ui.click_text(ctx.tr(I18nText.Detect), pk=PointKind.NEAR, times=3, interval=0.2):
        logger.warning(f"Text not found: {enemy_name.raw}")
        return False

    # 点击快速旅行
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot().search(ctx.tr(I18nText.DetectionTargetNotFound))
                    or ui.click_text(ctx.tr(I18nText.FastTravel), delay=0.2, times=3, interval=0.3)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.FastTravel).raw}")
        return False
    if ui.search(ctx.tr(I18nText.DetectionTargetNotFound)):
        logger.warning(f"{ctx.tr(I18nText.DetectionTargetNotFound).raw}")
        return False

    ui.wait_back_home(close_window=True)
    ui.sleep(0.5)
    return True


@node(NodeName.doCombat)
def doCombat(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    ui = UIOp(ctx)

    if not ui.is_on_homepage():
        return False

    enemy = local.enemy
    enemy_name = ctx.tr(local.enemy.id)
    logger.debug(f"Enemy: {enemy}, {enemy_name.raw}")
    # TODO 提示抗性

    index = 1  # 挑战次数
    page = GlobalPage(ctx)
    tm = TeamMember(ctx)

    # 设置战斗参数
    if local.combat_system is None:
        local.combat_system = CombatSystem(ctx.control_service, ctx.img_service)
        local.combat_system.set_resonators(local.members, is_print=False)
        local.combat_system.is_async = True
        local.combat_system.check_boss_hp = True
        local.combat_system.auto_pickup = False
    combat_system = local.combat_system
    pickup = AsyncPickup(ctx, delay=0.2, interval=lambda: round(random.uniform(0.3, 0.5), 2), timeout=10)

    # 循环刷取副本，直到需要离开副本
    while ui.is_set():
        # 跑向boss
        if enemy.routes:
            combat_system.exit_special_state(Morph.Prefer)
            ui.sleep(0.2)
            RouteExecutor(ctx).execute(enemy.routes)

        no_text_count = 8 if enemy.auto_respawn else 3
        no_text_max = no_text_count
        deadline = time.monotonic() + 20 * 60

        found_complete = False
        heartbeat = RateLimiter(1 / 5)

        if index == 1:
            logger.info(f"R{index} - Combat engaged")
        # 同步战斗次数
        index = local.combat_count

        # 循环战斗，直到击败boss
        while ui.is_set():
            if time.monotonic() > deadline or no_text_count < 0:
                logger.info(f"R{index} - Out of combat")
                break
            if heartbeat() == 0:
                logger.info(f"R{index} - In combat")
                ui.activate()

            # 开启战斗
            combat_system.start(3.5)

            ui.sleep(1.5).snapshot()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"{ui.bbox_result}")

            is_home = ui.is_on_homepage(ui.img)

            # 开启拾取
            if enemy.auto_respawn:
                pickup.start()
            else:
                if is_home and (hp := EnemyHpBar.detect(ui.img)):
                    logger.debug(f"hp: {hp:.4f}")
                    if hp > 0.3:
                        pickup.start()
                    else:
                        pickup.stop()
                else:
                    logger.debug(f"hp: None")
                    pickup.stop()

            # 检查战斗结束文本：挑战成功、领取奖励
            if ui.search(ctx.tr(
                    [I18nText.ClaimRewards, I18nText.ForgeryChallengeComplete, I18nText.TacetFieldChallengeComplete])):
                # 战斗次数，防止重复识别到
                if enemy.auto_respawn and not found_complete:
                    # 自动刷新的不退出战斗，只能在这里计数，不准
                    index += 1
                    local.combat_count += 1
                found_complete = True

                # 自动刷新的不退出继续打
                if enemy.auto_respawn:
                    ui.sleep(1)
                    continue

                # 结束战斗
                logger.info(f"R{index} - Combat ended")
                pickup.stop()
                combat_system.pause(join=True)
                if ui.search(ctx.tr(I18nText.Confirm)) and ui.search(ctx.tr(I18nText.Cancel)):
                    ui.esc().sleep(0.3)
                break
            found_complete = False

            # 检查战斗中文本：击败敌人、boss名等
            if res_battle_text := ui.search(ctx.tr(enemy.battle_text)):
                logger.debug(f"R{index} - Text: {res_battle_text}")
                no_text_count = no_text_max
                continue
            elif ui.search(ctx.tr(I18nText.PleaseDontForgetToTakeABreak)):
                logger.debug(f"R{index} - {ctx.tr(I18nText.PleaseDontForgetToTakeABreak).raw}")
                continue
            if is_home:
                no_text_count -= 1
            logger.debug(f"R{index} - Text not found: {ctx.tr(enemy.battle_text)}")

            # 自动拾取误触离开副本
            if ui.search(ctx.tr(I18nText.LeaveNow)) and ui.search(
                    ctx.tr(I18nText.Restart)) and ui.search(ctx.tr(I18nText.Confirm)):
                ctx.control_service.attack()
                ui.sleep(0.2)
                continue

            if page_key := page.action(ui=ui):
                if page_key == GlobalPage.Revive:
                    pickup.stop()
                    combat_system.pause(join=True)
                    ui.sleep(0.5)
                    local.downed = False
                    # 直接挑战的复苏后还在副本里，可以接着打
                    if enemy.prefer_quick:
                        ui.wait_back_home()
                        continue
                    return False
                elif page_key == GlobalPage.InternetDisconnecting:
                    pickup.stop()
                    combat_system.pause(join=True)
                    ui.sleep(0.5)
                    return False
                elif page_key == GlobalPage.LeaveInstance:
                    pickup.stop()
                    combat_system.pause(join=True)
                    ui.sleep(0.5)
                    return False

        # 挑战完成，暂停战斗系统
        pickup.stop()
        combat_system.pause(join=True)
        ui.sleep(1)

        # 等待回到主页
        back_homepage = False
        deadline = time.monotonic() + 10
        img = ui.img
        while time.monotonic() < deadline:
            img = ui.grap()
            if ui.is_on_homepage(img=img):
                back_homepage = True
                break
            # 领取奖励
            if ui.search(ctx.tr(I18nText.ClaimRewards)) and ui.search(
                    ctx.tr(I18nText.Confirm)) and ui.search(ctx.tr(I18nText.Cancel)):
                ui.esc().sleep(0.1)
            # 离开副本
            elif ui.search(ctx.tr(I18nText.LeaveNow)) and ui.search(
                    ctx.tr(I18nText.Restart)) and ui.search(ctx.tr(I18nText.Confirm)):
                ui.esc().sleep(0.1)
            # 其他
            elif page.action(ui=ui.snapshot(img=img)):
                pass
            ui.sleep(0.3)
        if not back_homepage:
            return False

        # 检查阵亡情况
        downed = tm.downed(img)
        members_size = len(local.members)
        for i in reversed(range(members_size)):
            if local.members[i]:
                break
            members_size -= 1
        if is_downed := any(downed[:members_size]):
            logger.info(f"R{index} - Resonator downed")
        local.downed = is_downed
        logger.debug(f"downed: {downed}, is_downed: {is_downed}")

        # 搜索声骸
        if enemy.auto_respawn:
            pass  # 自动刷新的边打边捡，保证效率
        else:
            combat_system.exit_special_state(Morph.Prefer)
            # 吸收声骸
            for i in range(2):
                absorb_timeout = 20 if i == 0 else 3
                if ObjectDetector(ctx).absorb_echoes(
                        timeout=absorb_timeout, enemy_name=I18nTr(Language.ZH)(enemy.id).raw):
                    local.absorb_count += 1
                    logger.info(f"R{index} - Absorbed: {local.absorb_count}")
                    if ui.sleep(0.4).snapshot().search(ctx.tr(I18nText.ClaimRewards)) and ui.search(
                            ctx.tr(I18nText.Confirm)) and ui.search(ctx.tr(I18nText.Cancel)):
                        ui.esc().sleep(0.3)
                        continue
                    ui.sleep(0.3)
                    break
                else:
                    logger.debug(f"R{index} - Not absorbed")
                    break

        # 准备进入下一轮
        for _ in range(2):
            claim_time = time.monotonic() + 2
            if not ui.esc().sleep(0.3).wait().until(
                    lambda: ui.snapshot().search(ctx.tr(I18nText.WeeklyRestart))
                            and ui.search(ctx.tr([I18nText.WeeklyExit, I18nText.Confirm]))
                            or time.monotonic() > claim_time and ui.search(ctx.tr(I18nText.ClaimRewards))
                            or page.isTerminal(ui=ui)):
                # 以防万一，检查领取奖励
                if ui.search(ctx.tr(I18nText.ClaimRewards)):
                    # 关闭弹窗
                    if ui.search(ctx.tr(I18nText.Confirm)) and ui.search(ctx.tr(I18nText.Cancel)):
                        ui.esc().sleep(0.3)
                    continue
                return False
            break

        # 不会自动刷新的的在战斗结束后计数
        if not is_downed and not enemy.auto_respawn:
            index += 1
            local.combat_count += 1

        # 副本内esc重新挑战
        if enemy.is_dungeon and not page.isTerminal(ui=ui):
            # 退出副本，复活
            if is_downed:
                logger.info(f"R{index} - Exit to nexus")
                ui.click_text(ctx.tr([I18nText.WeeklyExit, I18nText.Confirm]), times=3, interval=0.3)
                ui.sleep(1.5).wait_back_home()
                ui.sleep(0.3)
                return False

            logger.info(f"R{index} - {ctx.tr(I18nText.WeeklyRestart).raw}: {enemy_name.raw}")
            ui.click_text(ctx.tr(I18nText.WeeklyRestart), pk=PointKind.RANDOM, times=3, interval=0.3)
            ui.sleep(1.5).wait_back_home()
            ui.sleep(0.3)

            continue

        # 大世界
        break

    return False


class BossWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        super().__init__(ctx)

        self.engine = WorkflowEngine()
        self.fsm = TaskFSM(name=self.__class__.__name__)
        self.local = TaskLocal()

        self.__init_task_local()
        self.__init_workflow()

    def execute(self, **kwargs):
        try:
            logger.debug(f"task: {self.__class__.__name__}")
            self.ctx.runtime.taskFSM = self.fsm
            self.fsm.start()
            self.ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
            self.ctx.control_service.activate()
            time.sleep(0.1)
            self.engine.run(self, local=self.local, **kwargs)
        except Exception as e:
            raise e
        finally:
            # logger.info(f"=== Summary ===")
            # logger.info(f"Total: {self.local.combat_count}")
            # if self.local.absorb_count > 0:
            #     logger.info(f"Absorb: {self.local.absorb_count}")
            # logger.info(f"===============")
            pass

    def __init_task_local(self):
        """根据配置初始化任务状态"""
        cfg = self.ctx.runtime.cfg.boss
        logger.debug(f"cfg: {cfg}")

        self.local.rootFSM.set_enabled(True)
        self.local.teamFSM.set_enabled(True)

        logger.info(f"Enemy: {cfg.bossName}")
        self.local.enemy = Enemy.from_key(cfg.bossName[0])

        if not self.local.rootFSM.is_active:
            logger.warning('Task is not active')

    def __init_workflow(self):
        (
            self.engine.source(NodeName.globalDispatcher, is_start=True)
            .on(I18nText.Terminal).to(NodeName.rootDispatcher)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.rootDispatcher)
            .on(I18nText.Team).to(NodeName.doTeam)
            .on(I18nText.ResonatorDowned).to(NodeName.doTravelToResonanceNexus)
            .on(I18nText.Guidebook).to(NodeName.doGuidebook)
            .always().to(NodeName.endNode)
        )

        (
            self.engine.source(NodeName.doTeam)
            .on(False).to(NodeName.doTravelToResonanceNexus)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doTravelToResonanceNexus)
            .on(True).to(NodeName.globalDispatcher)
            .always().to(NodeName.endNode)
        )

        (
            self.engine.source(NodeName.doGuidebook)
            .on(I18nText.MaterialCollection).to(NodeName.doMaterialCollection)
            .on(I18nText.EnemyTracing).to(NodeName.doEnemyTracing)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doMaterialCollection)
            .on(I18nText.BossChallenge).to(NodeName.doBossChallenge)
            .on(I18nText.WeeklyChallenge).to(NodeName.doWeeklyChallenge)
            .on(I18nText.NightmarePurification).to(NodeName.doNightmarePurification)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doBossChallenge)
            .on(True).to(NodeName.doCombat)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doWeeklyChallenge)
            .on(True).to(NodeName.doCombat)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doNightmarePurification)
            .on(True).to(NodeName.doCombat)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doEnemyTracing)
            .on(True).to(NodeName.doCombat)
            .always().to(NodeName.globalDispatcher)
        )

        self.engine.source(NodeName.doCombat).always().to(NodeName.globalDispatcher)

        self.engine.exception(NodeName.endNode)
