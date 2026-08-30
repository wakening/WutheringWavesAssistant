import logging
import random
import re
import time
from typing import Optional

import numpy as np

from src.core.color import ColorRule, Color, ColorMatch
from src.core.combat.combat_core import ResonatorNameEnum, Morph, BaseResonator
from src.core.combat.combat_system import CombatSystem
from src.core.enemy import Enemy, EnemySpecies
from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind, Point
from src.core.i18n import I18nText, Language, I18nTr
from src.core.message import MsgType, MsgTaskStatus, MsgSource
from src.core.movement import Run, Walk, RouteExecutor
from src.core.pages import UIOp, GlobalPage
from src.core.resonator import Resonator
from src.core.resource import Icon
from src.core.task import TaskFSM, TaskStatus, TaskFSMGroup
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow
from src.service.common_workflow import (
    absorb_around_variant_blind, move_and_scan_dialogue,
    match_remaining_attempts, linear_spacing, query_waveplate_guidebook, query_waveplate_claim_rewards,
    object_detection, search_icon_guidebook, bbox_dialogue, AsyncPickup, RoiEx, LinearSpacing, RateLimiter,
)
from src.util import img_util, file_util
from src.util.img_sift_util import SIFTFeatureMatcher
from src.util.img_tile_util import TileGrid

logger = logging.getLogger(__name__)


class TaskLocal:

    def __init__(self):
        self.teamFSM: TaskFSM = TaskFSM(name=I18nText.Team)

        self.rootFSM: TaskFSMGroup = TaskFSMGroup(
            self.teamFSM,
            name="Root"
        )

        # runtime
        self.downed = False

        self.combat_system: CombatSystem = None
        # self.enemy = Enemy.MyriadSnareRustfireChassis
        self.enemy_key = I18nText.EnemyMyriadSnareRustfireChassis


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
    tmpl_img = img_util.read_img(file_util.get_assets_map("Huanglong/Jinzhou/8_0_-1.png"))
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
    if result := ui.search(ctx.tr(I18nText.ResonatorDowned), roi):
        logger.info(f"resonator downed: {len(result)}")
        if ui.esc().sleep(0.5).wait_back_home():
            ui.sleep(0.3)
        return False

    # 匹配编队角色名
    img = ui.img

    # 识别编队
    members_info: list[list] = [
        # 三个元素分别是：name、text、is_exist
        [None, None, None], [None, None, None], [None, None, None]
    ]
    team_members = [ResonatorNameEnum.none.value for _ in range(3)]

    # 编队角色名右侧一点黑色背景上取点
    member_points = [
        AnchorPoint(433, 569, Align.Center | Align.Middle),
        AnchorPoint(810, 569, Align.Center | Align.Middle),
        AnchorPoint(1187, 569, Align.Center | Align.Middle),
    ]
    member_boxes = [
        AnchorBBox(
            AnchorPoint(200, 550, Align.Center | Align.Middle),
            AnchorPoint(510, 590, Align.Center | Align.Middle),
        ),
        AnchorBBox(
            AnchorPoint(576, 550, Align.Center | Align.Middle),
            AnchorPoint(888, 590, Align.Center | Align.Middle),
        ),
        AnchorBBox(
            AnchorPoint(954, 550, Align.Center | Align.Middle),
            AnchorPoint(1280, 590, Align.Center | Align.Middle),
        ),
    ]
    member_points = [ctx.scaler.as_point(p) for p in member_points]
    member_boxes = [ctx.scaler.as_bbox(box) for box in member_boxes]

    color_matches = []
    for p in member_points:
        rule = ColorRule().points(p).colors(Color.bgr(22, 18, 13), 30)
        color_matches.append(ColorMatch(ctx.scaler).rules(rule))

    for i, match in enumerate(color_matches):
        if match.match(img):
            members_info[i][2] = True

    keys = Resonator.i18n_keys()
    lang = ctx.window_service.get_lang()

    for text_box in ui.bbox_result:
        if text_box.x2 < member_boxes[0].x1:
            continue
        if text_box.y2 < member_boxes[0].y1 or text_box.y2 > member_boxes[0].y2:
            continue
        for i, member_bbox in enumerate(member_boxes):
            if not member_bbox.contains_bbox(text_box):
                continue
            if not members_info[i][2]:
                continue
            members_info[i][1] = text_box
            if lang == Language.ZH:
                # 通过名称匹配这个位置的角色名
                enum_obj = ResonatorNameEnum.get_enum_by_ocr_text(text_box.text)
                # 角色名都对不上，默认为主角
                members_info[i][0] = enum_obj.value if enum_obj else ResonatorNameEnum.rover.value
                team_members[i] = members_info[i][0]
            elif lang == Language.EN:
                key = next((k for k in keys if ui.match_key(k, text_box.text)), None)
                if not key:
                    key = I18nText.Rover
                members_info[i][0] = I18nTr(Language.ZH)(key).raw
                team_members[i] = members_info[i][0]

            else:
                raise NotImplementedError()
            # logger.debug(f"team_members[{i}]: {team_members[i]}")

    # logger.debug(f"members_info: {members_info}")
    logger.info(f"team members: {team_members}")

    ui.esc().sleep(1)
    if not any(team_members):  # 兜底，留一个角色，至少能动
        team_members = ["unknown", None, None]
        logger.info(f"reset team members: {team_members}")
    local.teamFSM.complete()
    ctx.shared.team_members = team_members
    # ctx.shared.team_members = ["今汐", "长离", "守岸人"]

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
    roi_ex = RoiEx(ctx)

    if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().search(titles, roi_ex.guidebook_title)):
        logger.warning(f"Page not found: {ctx.tr(I18nText.Guidebook).raw}")
        return None

    # enemy_key = ctx.runtime.cfg.boss.bossName[0]
    enemy_key = local.enemy_key
    enemy_name = ctx.tr(enemy_key)
    enemy = Enemy.enemies().get(enemy_key)
    # logger.debug(f"Enemy: {enemy_name.raw}")
    logger.debug(f"Enemy: {enemy}")

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
        if not ui.sleep(0.1).wait().until(lambda: ui.snapshot().search(_keyword, roi_ex.guidebook_title)):
            return False
        return True

    # 从素材获取菜单进
    if enemy.prefer_quick:
        if not ui.search(materialCollection, roi_ex.guidebook_title) and not _click_icon(
                Icon.materialCollection(), materialCollection):
            return None

        menu_key = enemy.quick_boss_meta.menu
        menu = ctx.tr(menu_key)

        if menu_key not in [I18nText.BossChallenge, I18nText.WeeklyChallenge]:
            raise NotImplementedError(f"Unsupported menu: {menu.raw}")
        logger.info(f"Menu: {menu.raw}")

        if menu_key == I18nText.BossChallenge:
            # 点击讨伐强敌，等待内容
            if not ui.sleep(0.2).wait().until(
                    lambda: ui.snapshot().click_text(menu, roi_ex.guidebook_item, times=2, interval=0.3)
                            and ui.search(ctx.tr(I18nText.FilterToViewRewardsForEachPhase))):
                return None

            # 滑动寻找入口
            for i, p in enumerate(LinearSpacing(ctx).boss_challenge(ui.img)):
                if i > 0:
                    logger.debug(f"Scroll point: {p}")
                    ui.click_point(p, times=2, interval=0.2)
                    ui.sleep(0.2).snapshot()
                if not (enemy_text := ui.search(enemy_name, roi_ex.guidebook_content)):
                    continue
                if not (challenge_list := ui.search(ctx.tr(I18nText.Challenge), roi_ex.guidebook_content)):
                    continue
                challenge_list.sort(key=lambda x: x.y1)
                if enemy_text[0].y1 > challenge_list[-1].y2:
                    continue
                if not (challenge_text := next((i for i in challenge_list if enemy_text[0].y1 < i.y2), None)):
                    return None
                ui.click_bbox(challenge_text, times=2, interval=0.3)

                # 点击提示弹窗
                if not ui.sleep(0.2).wait().until(
                        lambda: ui.snapshot().search(ctx.tr(I18nText.ArrivingAtTheDestination))
                                and ui.click_text(ctx.tr(I18nText.Confirm), times=3, interval=0.3)
                                or ui.search(ctx.tr(I18nText.QuickSetup))
                                and ui.click_text(ctx.tr(I18nText.StartChallenge), times=3, interval=0.3)):
                    return None

                # 等待进入副本
                if not ui.sleep(2).wait_back_home():
                    return None

                return I18nText.BossChallenge

            logger.warning(f"Enemy not found: {enemy_name.raw}")
            return None

        elif menu_key == I18nText.WeeklyChallenge:
            # 点击战歌重奏
            if not ui.sleep(0.2).wait().until(
                    lambda: ui.snapshot().click_text(menu, roi_ex.guidebook_item, times=2, interval=0.3)
                            and ui.search(ctx.tr(I18nText.RemainingWeeklyAttempts))):
                return None

            # 滑动寻找入口
            for i, p in enumerate(LinearSpacing(ctx).boss_challenge(ui.img)):
                if i > 0:
                    logger.debug(f"Scroll point: {p}")
                    ui.click_point(p, times=2, interval=0.2)
                    ui.sleep(0.2).snapshot()
                if not (enemy_text := ui.search(enemy_name, roi_ex.guidebook_content)):
                    continue
                if not (challenge_list := ui.search(ctx.tr(I18nText.Challenge), roi_ex.guidebook_content)):
                    continue
                challenge_list.sort(key=lambda x: x.y1)
                if enemy_text[0].y1 > challenge_list[-1].y2:
                    continue
                if not (challenge_text := next((i for i in challenge_list if enemy_text[0].y1 < i.y2), None)):
                    return None
                ui.click_bbox(challenge_text, times=2, interval=0.3)

                # 点击提示弹窗
                if ui.sleep(0.2).snapshot().search(ctx.tr(I18nText.ArrivingAtTheDestination)):
                    ui.click_text(ctx.tr(I18nText.Confirm), times=2, interval=0.3)
                # 等待进入副本
                if not ui.sleep(2).wait_back_home():
                    return None

                return I18nText.BossChallenge

            logger.warning(f"Enemy not found: {enemy_name.raw}")
            return None

        return None

    # 从敌迹探寻菜单进
    if not _click_icon(Icon.enemyTracing(), enemyTracing):
        return None
    if not ui.search(ctx.tr(I18nText.EnemyTracingSearch)) and not ui.wait().until(
            lambda: ui.snapshot().search(enemyTracing, roi_ex.guidebook_title)
                    and ui.search(ctx.tr(I18nText.EnemyTracingSearch), roi_ex.guidebook_item)):
        return None

    return I18nText.EnemyTracing


@node(NodeName.doMaterialCollection)
def doMaterialCollection(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    return None


@node(NodeName.doBossChallenge)
def doBossChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    return True


@node(NodeName.doWeeklyChallenge)
def doWeeklyChallenge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    return True


@node(NodeName.doEnemyTracing)
def doEnemyTracing(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    ui = UIOp(ctx)
    roi_ex = RoiEx(ctx)

    # 检查是否在敌迹探寻，双击搜索
    if not ui.snapshot().search(ctx.tr(I18nText.EnemyTracing), roi_ex.guidebook_title) or not ui.click_text(
            ctx.tr(I18nText.EnemyTracingSearch), roi_ex.guidebook_item, times=2, interval=0.2):
        return False

    # enemy_key = ctx.runtime.cfg.boss.bossName[0]
    enemy_key = local.enemy_key
    enemy_name = ctx.tr(enemy_key)
    enemy = Enemy.enemies().get(enemy_key)
    # TODO 提示抗性
    logger.debug(f"Enemy: {enemy_name.raw}")

    # 搜索敌人
    ui.sleep(0.1)
    ctx.control_service.input_text(f"^{re.sub(r"[·_-]", ".", enemy_name.raw)}$")
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

    # enemy_key = ctx.runtime.cfg.boss.bossName[0]
    enemy_key = local.enemy_key
    enemy_name = ctx.tr(enemy_key)
    enemy = Enemy.enemies().get(enemy_key)
    # TODO 提示抗性
    logger.info(f"Enemy: {enemy_name.raw}")

    downed = False
    index = 1  # 挑战次数

    # 循环刷取副本，直到需要离开副本
    while ui.is_set():
        if local.combat_system is None:
            local.combat_system = CombatSystem(ctx.control_service, ctx.img_service)
            local.combat_system.set_resonators(ctx.shared.team_members, is_print=False)
            local.combat_system.is_async = True
            local.combat_system.check_boss_hp = True
            local.combat_system.auto_pickup = True

        combat_system = local.combat_system

        # 跑向boss
        if enemy.routes:
            combat_system.exit_special_state(Morph.Prefer)
            RouteExecutor(ctx).execute(enemy.routes)

        no_text_count = 3
        no_text_max = no_text_count
        deadline = time.monotonic() + 10 * 60

        found_complete = False
        heartbeat = RateLimiter(1 / 5)

        if index == 1:
            logger.info(f"R{index} - Combat engaged")

        # 循环战斗，直到击败boss
        while ui.is_set():
            if time.monotonic() > deadline or no_text_count < 0:
                logger.info(f"R{index} - Out of combat")
                break
            if heartbeat() == 0:
                logger.info(f"R{index} - In combat")

            combat_system.start(3.5)
            ui.sleep(1.5).snapshot()

            # 领取奖励 TODO 领取奖励且检查左下角声骸名称判断已拾取
            if ui.search(ctx.tr(I18nText.ClaimRewards)):
                combat_system.pause()
                if ui.search(ctx.tr(I18nText.Confirm)) and ui.search(ctx.tr(I18nText.Cancel)):
                    ui.esc()
                break

            if ui.is_on_homepage():
                # 挑战成功
                if enemy.auto_respawn and ui.search(
                        ctx.tr([I18nText.ForgeryChallengeComplete, I18nText.TacetFieldChallengeComplete])):
                    # logger.info(f"R{index} - Combat ended!")
                    # break
                    # 防止重复识别到
                    if not found_complete:
                        index += 1
                    found_complete = True
                    ui.sleep(1)
                    continue
                found_complete = False

                # 击败
                battle_text = ctx.tr(enemy.battle_text)
                if ui.search(battle_text):
                    no_text_count = no_text_max
                    continue
                no_text_count -= 1
                logger.debug(f"R{index} - Text not found: {battle_text}")

            if page_key := GlobalPage(ctx).action(ui=ui):
                if page_key == GlobalPage.Revive:
                    # 直接挑战的复苏后还在副本里，可以接着打
                    if enemy.prefer_quick:
                        ui.wait_back_home()
                        continue
                    combat_system.pause()
                    return False
                elif page_key == GlobalPage.InternetDisconnecting:
                    combat_system.pause()
                    return False

        # 挑战完成，暂停战斗系统
        combat_system.pause()
        ui.sleep(0.5)
        roi_ex = RoiEx(ctx)

        # 等待回到主页
        back_homepage = False
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            img = ui.grap()
            if ui.is_on_homepage(img=img):
                back_homepage = True
                break
            if GlobalPage(ctx).action(ui=ui.snapshot(img=img)):
                pass
            elif ui.search(ctx.tr(I18nText.ClaimRewards)) and ui.search(
                    ctx.tr(I18nText.Confirm)) and ui.search(ctx.tr(I18nText.Cancel)):
                ui.esc().sleep(0.1)
            ui.sleep(0.3)
        if not back_homepage:
            return False

        # 检查阵亡情况
        if downed:
            logger.info(f"R{index} - Resonator downed")
            local.downed = downed

        # 搜索声骸
        if enemy.auto_respawn:
            pass  # 自动刷新的边打边捡，保证效率
        else:
            # if ui.search(ctx.tr(I18nText.Absorb), roi_ex.dialogue) and not ui.search(
            #         ctx.tr(I18nText.ClaimRewards), roi_ex.dialogue):
            #     ui.pick_up()
            # 退出特殊状态
            combat_system.exit_special_state(Morph.Prefer)
            logger.debug(f"R{index} - Search echo")
            if object_detection(ctx, search_echo=True, timeout=20, boss_name=enemy_name):
                logger.info(f"R{index} - Absorbed")
            else:
                logger.debug(f"R{index} - Not absorbed")

        # 准备进入下一轮
        page = GlobalPage(ctx)
        if not ui.sleep(0.2).esc().sleep(0.3).wait().until(
                lambda: ui.snapshot().search(ctx.tr(I18nText.WeeklyRestart))
                        and ui.search(ctx.tr([I18nText.WeeklyExit, I18nText.Confirm]))
                        or page.isTerminal(ui=ui)):
            return False

        # 副本内esc重新挑战
        if enemy.is_dungeon and not page.isTerminal(ui=ui):
            # 退出副本，复活
            if downed:
                logger.info(f"R{index} - Exit to Nexus")
                ui.click_text(ctx.tr([I18nText.WeeklyExit, I18nText.Confirm]), times=3, interval=0.3)
                ui.sleep(1.5).wait_back_home()
                ui.sleep(0.3)
                return False

            ui.click_text(ctx.tr(I18nText.WeeklyRestart), times=3, interval=0.3)
            index += 1
            logger.info(f"R{index} - {ctx.tr(I18nText.WeeklyRestart).raw}")
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

    def __init_task_local(self):
        """根据配置初始化任务状态"""
        cfg = self.ctx.runtime.cfg.boss
        logger.debug(f"cfg: {cfg}")

        self.local.rootFSM.set_enabled(True)
        self.local.teamFSM.set_enabled(True)

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
            .on(I18nText.BossChallenge).to(NodeName.doBossChallenge)
            .on(I18nText.WeeklyChallenge).to(NodeName.doWeeklyChallenge)
            .on(I18nText.EnemyTracing).to(NodeName.doEnemyTracing)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doEnemyTracing)
            .on(True).to(NodeName.doCombat)
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

        self.engine.source(NodeName.doCombat).always().to(NodeName.globalDispatcher)

        # self.engine.source(NodeName.doBossChallenge).always().to(NodeName.globalDispatcher)
        # self.engine.source(NodeName.doWeeklyChallenge).always().to(NodeName.globalDispatcher)

        self.engine.exception(NodeName.endNode)
