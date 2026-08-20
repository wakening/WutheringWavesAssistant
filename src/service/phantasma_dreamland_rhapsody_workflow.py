import logging
import math
import random
import re
import time
from typing import Optional

from src.core.color import Color
from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind, BBox
from src.core.i18n import I18nText
from src.core.message import MsgType, MsgTaskStatus
from src.core.pages import UIOp, GlobalPage
from src.core.task import TaskFSM, TaskStatus, TaskFSMGroup
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow
from src.service.common_workflow import (
    bbox_terminal_content, bbox_guidebook_title
)

logger = logging.getLogger(__name__)


# 幻梦游园·狂想


class TaskLocal:

    def __init__(self):
        self.embedding: bool = False

        self.phantasmaDreamlandRhapsodyFSM: TaskFSM = TaskFSM(name="PhantasmaDreamlandRhapsody")

        # ------- Guidebook -------
        self.activityFSM: TaskFSMGroup = TaskFSMGroup(
            self.phantasmaDreamlandRhapsodyFSM,
            name=I18nText.Activity
        )

        # ------- Root -------
        self.guidebookFSM: TaskFSMGroup = TaskFSMGroup(
            self.activityFSM,
            name=I18nText.Guidebook
        )

        self.rootFSM: TaskFSMGroup = TaskFSMGroup(
            self.guidebookFSM,
            name="Root"
        )


class NodeName:
    globalDispatcher = "globalDispatcher"
    rootDispatcher = "rootDispatcher"
    endNode = "endNode"

    # rootDispatcher
    doGuidebook = "doGuidebook"

    # PhantasmaDreamlandRhapsody
    doStart = "doStart"
    doPlay = "doPlay"


@node(NodeName.endNode)
def endNode(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.embedding:
        return True

    if local.rootFSM.is_finished:
        ctx.runtime.taskFSM.complete()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
        # ctx.ipc.event_queue.put({
        #     "task": {"DailyTask": "finished"}
        # }, block=True)
    else:
        ctx.runtime.taskFSM.fail()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.FAILED)
        # ctx.ipc.event_queue.put({
        #     "task": {"DailyTask": "failed"}
        # }, block=True)
    time.sleep(0.1)
    return True


@node(NodeName.globalDispatcher)
def globalDispatcher(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """检查是否在有效页面（如：终端），不在则esc尝试离开（副本等）"""
    ui = UIOp(ctx)
    ui.activate().sleep(0.1).snapshot()

    # 幻梦游园·狂想主页
    if ui.search(ctx.tr(I18nText.PhantasmaDreamlandRhapsody)) and ui.search(ctx.tr(I18nText.PdrDreamGallery)):
        return I18nText.PhantasmaDreamlandRhapsody

    # 进入下一天
    if ui.search(ctx.tr(I18nText.PdrProceedToNextDay)) and ui.search(ctx.tr(
            I18nText.PdrDreamlandOfTheWeek)) and ui.search(ctx.tr(I18nText.PdrDreamlandDetail)):
        return I18nText.PdrProceedToNextDay

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
    if local.guidebookFSM.is_active:
        return I18nText.Guidebook

    if local.rootFSM.is_active:
        logger.warning("Unexpected root state")
    return None


@node(NodeName.doGuidebook)
def doGuidebook(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """索拉指南"""
    if local.guidebookFSM.is_terminal:
        return None

    ui = UIOp(ctx)
    ui.snapshot()

    # 终端
    if GlobalPage(ctx).isTerminal(ui=ui):
        # 点击进入索拉指南
        if not ui.click_text(ctx.tr(I18nText.Guidebook),
                             bbox_terminal_content(ctx), pk=PointKind.NEAR, delay=0.2, times=2, interval=0.2):
            logger.warning(f"Text not found: {ctx.tr(I18nText.Guidebook).raw}")
            return None
    else:
        ctx.control_service.guidebook()

    # 进入索拉指南后，默认是 活跃度 或 素材获取页
    titles = ctx.tr([
        I18nText.Activity,
        I18nText.MaterialCollection,
        I18nText.RecurringChallenges,
        I18nText.PathOfGrowth,
        I18nText.EnemyTracing,
        I18nText.Milestones,
    ])
    title_roi = bbox_guidebook_title(ctx)

    if not ui.sleep(0.5).wait().until(lambda: ui.snapshot().search(titles, title_roi)):
        logger.warning(f"Page not found: {ctx.tr(I18nText.Guidebook).raw}")
        return None

    # 点击周度游历
    weekly_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Top | Align.Left),
        AnchorPoint(610, 130, Align.Top | Align.Left)
    ))
    if not ui.sleep(0.3).click_text(ctx.tr(I18nText.ActivityWeekly), weekly_roi, times=2, interval=0.3):
        # 点击侧边栏
        ui.click_point(AnchorPoint(50, 128, Align.Top | Align.Left), times=2, interval=0.3)

        if not ui.sleep(0.5).wait().until(
                lambda: ui.snapshot().click_text(
                    ctx.tr(I18nText.ActivityWeekly), weekly_roi, delay=0.3, times=2, interval=0.3)):
            logger.warning(f"Text not found: {ctx.tr(I18nText.ActivityWeekly).raw}")
            return None

    # 点击幻梦游园·狂想
    if not ui.wait().until(lambda: ui.snapshot().click_text(
            ctx.tr(I18nText.PhantasmaDreamlandRhapsody), delay=0.2, times=2, interval=0.2)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.PhantasmaDreamlandRhapsody).raw}")
        return None

    # 等待游戏主页
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot()
                    and ui.search(ctx.tr(I18nText.PdrDreamGallery))
                    and ui.search(ctx.tr(I18nText.PdrWeeklyActivityPts))):
        logger.warning(f"Text not found: {ctx.tr(I18nText.PdrDreamGallery).raw}")
        return None

    ui.sleep(0.5)
    return I18nText.PhantasmaDreamlandRhapsody


def __getWeeklyActivityPts(ctx: NodeContext, ui: UIOp, roi: Optional[BBox | AnchorBBox] = None):
    max_pts = 6000
    # 已达到上限
    if ui.search(ctx.tr(I18nText.PdrLimitReached), roi):
        logger.info(f"Weekly Activity Pts: {ctx.tr(I18nText.PdrLimitReached).raw}")
        return max_pts
        # return 0  # test
    regex = rf"([0-9oO]*)/{max_pts}$"
    result = ui.search(regex, roi)
    if not result:
        logger.warning(f"Weekly Activity Pts not found")
        return 0
    match = re.compile(regex, flags=re.I).search(result[0].text)
    logger.debug(f"match: {match.group(0)}")
    cur_pts = int(re.compile(r"[oO]").sub("0", match.group(1)))
    logger.info(f"Weekly Activity Pts: {cur_pts}/{max_pts}")
    return cur_pts


@node(NodeName.doStart)
def doStart(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[bool]:
    """开始游戏"""
    if local.phantasmaDreamlandRhapsodyFSM.is_terminal:
        return False
    if local.phantasmaDreamlandRhapsodyFSM.status == TaskStatus.PENDING:
        logger.info(f"{ctx.tr(I18nText.PhantasmaDreamlandRhapsody).raw}")
        local.phantasmaDreamlandRhapsodyFSM.start()

    ui = UIOp(ctx)
    ui.snapshot()

    # 检查游戏主页
    if not ui.search(ctx.tr(I18nText.PdrDreamGallery)) or not ui.search(ctx.tr(I18nText.PdrWeeklyActivityPts)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.PdrDreamGallery).raw}")
        return None

    # 本周游历值
    pts_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Left | Align.Top),
        AnchorPoint(235, 200, Align.Left | Align.Top)
    ))
    cur_pts = __getWeeklyActivityPts(ctx, ui, roi=pts_roi)
    if cur_pts >= 6000:
        local.phantasmaDreamlandRhapsodyFSM.complete()
        return False

    start_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(980, 590, Align.Right | Align.Bottom),
        AnchorPoint(1280, 720, Align.Right | Align.Bottom)
    ))
    # 已存档，点击继续游戏
    if ui.click_text(ctx.tr(I18nText.PdrContinue), start_roi, delay=0.3):
        logger.info(f"{ctx.tr(I18nText.PdrContinue).raw}")
        # 点击新游戏
        if not ui.sleep(0.3).wait().until(
                lambda: ui.snapshot().click_text(ctx.tr(I18nText.PdrNewGame), delay=0.3, times=2, interval=0.2)):
            return None
    elif res_start := ui.search(ctx.tr(I18nText.PdrStart), start_roi):
        logger.info(f"{ctx.tr(I18nText.PdrStart).raw}")
        # 新游戏，选择祝福
        if ui.search(ctx.tr(I18nText.BlessingReset)):
            ui.click_point(AnchorPoint(610, 575, Align.Center | Align.Bottom), delay=0.3)
            if ui.sleep(0.4).wait().until(
                    lambda: ui.snapshot()
                            and ui.search(ctx.tr(I18nText.PhantasmaBlessing))
                            and ui.search(ctx.tr(I18nText.Confirm))):
                if ui.click_text(ctx.tr(I18nText.BlessingAddOn), delay=0.3, times=2, interval=0.2):
                    ui.click_text(ctx.tr(I18nText.Confirm), delay=0.3)
                else:
                    ui.sleep(0.3).esc()
                ui.sleep(0.3)
        # 点击开始
        ui.click_bbox(res_start, times=2, interval=0.2)
    else:
        return None

    # 乐园阶段目标
    if not ui.sleep(0.5).wait().until(
            lambda: ui.snapshot()
                    and ui.click_text(ctx.tr(I18nText.PdrNewGame), delay=0.3) is not None  # 此处仅为以防万一，兼容继续游戏弹窗
                    and ui.search(ctx.tr(I18nText.PdrCurrentPhase))
                    and ui.click_text(ctx.tr(I18nText.Confirm), delay=0.3)):
        return None

    ui.sleep(0.5)
    return True


def __calcRarityRank(pixels: list) -> int:
    """欧几里得距离匹配，找出颜色品质最高的点，返回下标，仅支持BGR"""
    if not pixels:
        return 0

    # 品质
    rarity = [
        Color.bgr(226, 217, 218),  # Grey
        Color.bgr(253, 227, 192),  # Blue
        Color.bgr(252, 190, 239),  # Purple
        Color.bgr(132, 234, 255),  # Orange
    ]

    best_rank = -1
    best_index = 0

    for i, pixel in enumerate(pixels):
        b, g, r = pixel

        # 计算该点与4个基准色的欧几里得距离，选最近者
        min_dist = float('inf')
        rank = 0
        for idx, base in enumerate(rarity):
            dist = math.sqrt(
                (b - base.c1) ** 2 +
                (g - base.c2) ** 2 +
                (r - base.c3) ** 2
            )
            if dist < min_dist:
                min_dist = dist
                rank = idx

        # 更新最高等级
        if rank > best_rank:
            best_rank = rank
            best_index = i

    return best_index


def __getHighestQualityPoint(ctx: NodeContext, img) -> tuple[int, int]:
    """获取最高品质声骸所在点"""
    points = [
        AnchorPoint(230, 140, Align.Center | Align.Middle),
        AnchorPoint(531, 140, Align.Center | Align.Middle),
        AnchorPoint(834, 140, Align.Center | Align.Middle),
    ]
    pixels = []
    for ap in points:
        p = ctx.scaler.as_point(ap)
        pixels.append(img[p.y, p.x])
    index = __calcRarityRank(pixels)
    logger.debug(f"rarity index: {index}")
    rois = [
        AnchorBBox(
            AnchorPoint(249, 137, Align.Center | Align.Middle),
            AnchorPoint(435, 215, Align.Center | Align.Middle),
        ),
        AnchorBBox(
            AnchorPoint(249 + 302, 137, Align.Center | Align.Middle),
            AnchorPoint(435 + 302, 215, Align.Center | Align.Middle),
        ),
        AnchorBBox(
            AnchorPoint(249 + 302 * 2, 137, Align.Center | Align.Middle),
            AnchorPoint(435 + 302 * 2, 215, Align.Center | Align.Middle),
        ),
    ]
    roi_point = ctx.scaler.as_bbox(rois[index]).random
    logger.debug(f"roi point: {roi_point}")
    return roi_point


@node(NodeName.doPlay)
def doPlay(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.phantasmaDreamlandRhapsodyFSM.is_terminal:
        return False
    if local.phantasmaDreamlandRhapsodyFSM.status == TaskStatus.PENDING:
        logger.info(f"{ctx.tr(I18nText.PhantasmaDreamlandRhapsody).raw}")
        local.phantasmaDreamlandRhapsodyFSM.start()

    index = 0
    max_miss = 5
    miss_count = max_miss
    interval = 0.4
    next_activate_time = time.monotonic() - 1

    ui = UIOp(ctx)

    while ctx.runtime.stop_event.is_set():
        logger.debug(f"index: {index}")
        index += 1

        if time.monotonic() > next_activate_time:
            ui.activate()
            next_activate_time = time.monotonic() + 1
        ui.snapshot()

        # 乐园阶段目标
        if ui.search(ctx.tr(I18nText.PdrCurrentPhase)) and ui.click_text(ctx.tr(I18nText.Confirm), delay=0.3):
            ui.sleep(interval)
            miss_count = max_miss
            continue

        # 阶段收益结算
        if ui.search(ctx.tr(I18nText.PdrPhaseResult)) and ui.click_text(
                ctx.tr([I18nText.PdrNextPhase, I18nText.Confirm]), delay=0.3):
            ui.sleep(interval)
            miss_count = max_miss
            continue

        # 乐园商店
        if ui.search(ctx.tr(I18nText.PdrDreamlandShop)):
            ui.esc().sleep(0.5)
            miss_count = max_miss
            continue

        # 奇缘异遇
        if ui.search(ctx.tr(I18nText.PdrStrangeEncounters)) and ui.search(ctx.tr(
                I18nText.PdrImNotInterestedInThis)) and ui.search(ctx.tr(I18nText.Confirm)):
            ui.click_text(ctx.tr(I18nText.PdrImNotInterestedInThis), delay=0.3, times=2, interval=0.2)
            ui.click_text(ctx.tr(I18nText.Confirm))
            ui.sleep(interval)
            miss_count = max_miss
            continue

        # 三选一
        if ui.search(ctx.tr(I18nText.PdrRefresh)) and ui.search(
                ctx.tr(I18nText.PdrSkip)) and ui.search(ctx.tr(I18nText.Confirm)):
            point_echo = __getHighestQualityPoint(ctx, ui.grap())
            ui.click_point(point_echo, delay=0.2, times=2, interval=0.2)
            ui.click_text(ctx.tr(I18nText.Confirm))
            ui.click_text(ctx.tr(I18nText.PdrSkip), delay=0.03)
            ui.sleep(interval)
            miss_count = max_miss
            continue

        # 使用祝福
        if ui.click_text(ctx.tr(I18nText.PdrUseBlessing), delay=0.3):
            ui.sleep(interval)
            miss_count = max_miss
            continue

        # 进入下一天
        next_day = ui.search(ctx.tr(I18nText.PdrProceedToNextDay))
        if next_day and ui.search(
                ctx.tr(I18nText.PdrDreamlandOfTheWeek)) and ui.search(ctx.tr(I18nText.PdrDreamlandDetail)):
            # 切换速度
            speed_roi = ctx.scaler.as_bbox(AnchorBBox(
                AnchorPoint(783, 0, Align.Right | Align.Top),
                AnchorPoint(924, 88, Align.Right | Align.Top)
            ))
            if not ui.search(ctx.tr(I18nText.PdrMax), speed_roi):
                ui.click_point(AnchorPoint(850, 41, Align.Right | Align.Top), delay=0.3)
                ui.sleep(0.05)
            # 新阶段第一天使用祝福
            if ui.search(ctx.tr(I18nText.PdrRemainingDays5)):
                ui.click_point(AnchorPoint(230, 565, Align.Left | Align.Bottom), delay=0.3)
                if ui.sleep(0.4).wait(0.8, 0.3).until(lambda: ui.snapshot().search(ctx.tr(I18nText.PdrUseBlessing))):
                    if ui.search(ctx.tr(I18nText.BlessingAddOn)):
                        ui.click_text(ctx.tr(I18nText.PdrUseBlessing), delay=0.3, times=2, interval=0.2)
                        # 三选一
                        if ui.sleep(0.3).wait().until(
                                lambda: ui.snapshot()
                                        and ui.search(ctx.tr(I18nText.PdrRefresh))
                                        and ui.search(ctx.tr(I18nText.PdrSkip))
                                        and ui.search(ctx.tr(I18nText.Confirm))):
                            point_echo = __getHighestQualityPoint(ctx, ui.grap())
                            ui.click_point(point_echo, delay=0.2, times=2, interval=0.2)
                            ui.click_text(ctx.tr(I18nText.Confirm))
                            ui.click_text(ctx.tr(I18nText.PdrSkip), delay=0.05)
                    elif ui.search(ctx.tr(I18nText.BlessingTransience)):
                        ui.click_text(ctx.tr(I18nText.PdrUseBlessing), delay=0.3, times=2, interval=0.2)
                    # elif ui.search(ctx.tr(I18nText.BlessingReset)):
                    #     ui.esc()
                    elif ui.search(ctx.tr(I18nText.BlessingTeleport)):
                        ui.click_text(ctx.tr(I18nText.PdrUseBlessing), delay=0.3, times=2, interval=0.2)
                    else:
                        ui.esc()

            ui.click_bbox(next_day, pk=PointKind.RANDOM, delay=0.3, times=3, interval=0.3)
            ui.sleep(3.2)
            miss_count = max_miss
            continue

        # esc误触暂停，点击继续
        if ui.search(ctx.tr(I18nText.PdrFinalize)) and ui.search(
                ctx.tr(I18nText.PdrRestart)) and ui.click_text(ctx.tr(I18nText.PdrResume), delay=0.3):
            ui.sleep(interval)
            miss_count = max_miss
            continue

        max_pts = 6000
        # 挑战成功，返回主页
        if ui.search(ctx.tr(I18nText.PdrChallengeComplete)) and ui.search(ctx.tr(I18nText.PdrReturn)):
            logger.info(f"{ctx.tr(I18nText.PdrChallengeComplete).raw}")
            cur_pts = __getWeeklyActivityPts(ctx, ui)
            if cur_pts >= max_pts:
                local.phantasmaDreamlandRhapsodyFSM.complete()
                ui.click_text(ctx.tr(I18nText.PdrReturn), delay=0.3)
                ui.sleep(0.2)
                return False
            ui.click_text(ctx.tr(I18nText.PdrReturn), delay=0.3)
            ui.sleep(0.4)
            break

        # 挑战失败，返回主页
        if ui.search(ctx.tr(I18nText.PdrChallengeFailed)) and ui.search(ctx.tr(I18nText.PdrReturn)):
            logger.info(f"{ctx.tr(I18nText.PdrChallengeFailed).raw}")
            cur_pts = __getWeeklyActivityPts(ctx, ui)
            if cur_pts >= max_pts:
                local.phantasmaDreamlandRhapsodyFSM.complete()
                ui.click_text(ctx.tr(I18nText.PdrReturn), delay=0.3)
                ui.sleep(0.2)
                return False
            ui.click_text(ctx.tr(I18nText.PdrReturn), delay=0.3)
            ui.sleep(0.4)
            break

        # 游戏主页
        if ui.search(ctx.tr(I18nText.PdrDreamGallery)):
            ui.sleep(1.0)
            break

        # 计数
        logger.debug(f"miss_count: {miss_count}")
        miss_count -= 1
        if miss_count == 0:
            break
        ui.sleep(interval)

    return True


class PhantasmaDreamlandRhapsodyWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        """幻梦游园·狂想"""
        super().__init__(ctx)

        self.engine = WorkflowEngine()
        self.fsm = TaskFSM(name="PhantasmaDreamlandRhapsodyWorkflow")
        self.local = TaskLocal()

        self.__init_task_local()
        self.__init_workflow()

    def execute(self, **kwargs):
        try:
            logger.debug(f"task: {self.__class__.__name__}")
            self.ctx.runtime.taskFSM = self.fsm
            self.fsm.start()
            if not self.embedding:
                self.ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
            self.ctx.control_service.activate()
            time.sleep(0.1)
            self.engine.run(self, local=self.local, **kwargs)
        except Exception as e:
            raise e

    def __init_task_local(self):
        """根据配置初始化任务状态"""
        self.local.phantasmaDreamlandRhapsodyFSM.set_enabled(True)

    def __init_workflow(self):
        (
            self.engine.source(NodeName.globalDispatcher, is_start=True)
            .on(I18nText.Terminal).to(NodeName.rootDispatcher)
            .on(I18nText.PhantasmaDreamlandRhapsody).to(NodeName.doStart)
            .on(I18nText.PdrProceedToNextDay).to(NodeName.doPlay)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.rootDispatcher)
            .on(I18nText.Guidebook).to(NodeName.doGuidebook)
            .always().to(NodeName.endNode)
        )

        (
            self.engine.source(NodeName.doGuidebook)
            .on(I18nText.PhantasmaDreamlandRhapsody).to(NodeName.doStart)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doStart)
            .on(True).to(NodeName.doPlay)
            .on(False).to(NodeName.endNode)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doPlay)
            .on(False).to(NodeName.endNode)
            .always().to(NodeName.globalDispatcher)
        )

        self.engine.exception(NodeName.endNode)
