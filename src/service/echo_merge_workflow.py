import logging
import random
import time
from typing import Optional

from src.core.geometry import AnchorBBox, Align, AnchorPoint, PointKind
from src.core.i18n import I18nText
from src.core.message import MsgType, MsgTaskStatus
from src.core.pages import UIOp, GlobalPage
from src.core.task import TaskFSM, TaskFSMGroup, TaskStatus
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow
from src.service.common_workflow import bbox_terminal_content

logger = logging.getLogger(__name__)


class TaskLocal:

    def __init__(self):
        self.embedding: bool = False

        self.standardMergeFSM: TaskFSM = TaskFSM(name=I18nText.StandardMerge)

        self.dataBankFSM: TaskFSMGroup = TaskFSMGroup(
            self.standardMergeFSM,
            name=I18nText.DataBank
        )

        self.rootFSM: TaskFSMGroup = TaskFSMGroup(
            self.dataBankFSM,
            name="Root"
        )

        # runtime
        self._failed_count = 3

    def fail(self) -> bool:
        self._failed_count -= 1
        return self._failed_count <= 0


class NodeName:
    globalDispatcher = "globalDispatcher"
    rootDispatcher = "rootDispatcher"
    endNode = "endNode"

    # rootDispatcher
    doDataBank = "doDataBank"

    # doDataBank
    doDataMerge = "doDataMerge"
    doStandardMerge = "doStandardMerge"


@node(NodeName.endNode)
def endNode(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    if local.rootFSM.is_finished:
        ctx.runtime.taskFSM.complete()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
    else:
        ctx.runtime.taskFSM.fail()
        ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.FAILED)
    ctx.ipc.event_queue.put({
        "task": {"EchoMergeProcessTask": "finished"}
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
        logger.debug(f"Found page: {page.Terminal}")
        return I18nText.Terminal

    if (ui.search(ctx.tr(I18nText.DataMerge))
            and ui.search(ctx.tr(I18nText.TargetedMerge))
            and ui.search(ctx.tr(I18nText.StandardMerge))):
        return I18nText.DataMerge

    # 在全局预设中找出离开函数，尝试回到主页
    if page_key := page.action(ui=ui):
        logger.debug(f"Found page: {page_key}")
        ui.sleep(0.5)
        return None

    logger.info("Transferring")

    num = max(1, min(1.4, random.gauss(1.2, 0.08)))
    # 兜底规则，esc
    ui.esc().sleep(num)
    return None


@node(NodeName.rootDispatcher)
def rootDispatcher(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    if local.dataBankFSM.is_active:
        return I18nText.DataBank

    if local.rootFSM.is_active:
        logger.warning("Unexpected root state")
    return None


@node(NodeName.doDataBank)
def doDataBank(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """数据坞"""
    if local.dataBankFSM.is_terminal:
        return None

    ui = UIOp(ctx)
    ui.activate().sleep(0.1).snapshot()

    # 从终端点击进入数据坞
    if GlobalPage(ctx).isTerminal(ui=ui):
        if not ui.click_text(ctx.tr(I18nText.DataBank), bbox_terminal_content(ctx),
                             pk=PointKind.NEAR, delay=0.2, times=2, interval=0.2):
            logger.warning(f"Text not found: {ctx.tr(I18nText.DataBank).raw}")
            ui.esc().sleep(1)
            return None
    elif ui.search(ctx.tr(I18nText.DataMerge)) and ui.search(ctx.tr(
            I18nText.TargetedMerge)) and ui.search(ctx.tr(I18nText.StandardMerge)):
        return I18nText.DataMerge
    else:
        return None

    # 等待进入数据坞
    if not ui.sleep(0.8).wait().until(
            lambda: ui.snapshot()
                    and ui.search(ctx.tr(I18nText.DataBankInfo))
                    and ui.search(ctx.tr(I18nText.DataBank))):
        logger.warning(f"Text not found: {ctx.tr(I18nText.DataBank).raw}")
        ui.esc().sleep(1)
        return None

    # 点击侧边栏图标
    ui.sleep(0.4).click_point(AnchorPoint(50, 400, Align.Top | Align.Left), times=2, interval=0.3)

    # 等待进入数据融合
    if not ui.sleep(0.5).wait().until(
            lambda: ui.snapshot()
                    and ui.search(ctx.tr(I18nText.DataMerge))
                    and ui.search(ctx.tr(I18nText.TargetedMerge))
                    and ui.search(ctx.tr(I18nText.StandardMerge))):
        logger.warning(f"Text not found: {ctx.tr(I18nText.DataMerge).raw}")
        ui.esc().sleep(1)
        return None

    return I18nText.DataMerge


@node(NodeName.doDataMerge)
def doDataMerge(ctx: NodeContext, local: TaskLocal, **kwargs) -> Optional[str]:
    """数据融合"""
    if local.dataBankFSM.is_terminal:
        return None

    ui = UIOp(ctx)
    ui.snapshot()

    roi_tab = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Left | Align.Middle),
        AnchorPoint(1280, 720 // 2, Align.Right | Align.Middle)
    ))
    roi_bottom = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 720 // 2, Align.Left | Align.Middle),
        AnchorPoint(1280, 720, Align.Right | Align.Middle)
    ))
    # 等待进入数据融合
    if not (ui.search(ctx.tr(I18nText.TargetedMerge), roi_tab)
            and ui.search(ctx.tr(I18nText.StandardMerge), roi_tab)
            and ui.search(ctx.tr([I18nText.TargetedMerge, I18nText.StandardMerge]), roi_bottom)):
        logger.warning(f"Text not found: {ctx.tr(I18nText.StandardMerge).raw}")
        ui.esc().sleep(1)
        return None

    # 点击标准融合
    ui.click_text(ctx.tr(I18nText.StandardMerge), roi_tab, delay=0.3, times=2, interval=0.2)
    ui.sleep(0.4).click_text(ctx.tr([I18nText.TargetedMerge, I18nText.StandardMerge]), roi_bottom)

    # 等待进入标准融合
    if not ui.sleep(0.3).wait().until(
            lambda: ui.snapshot()
                    and ui.search(ctx.tr(I18nText.DataMergeSelectAll))
                    and ui.search(ctx.tr(I18nText.StandardMerge))):
        ui.esc().sleep(1)
        return None

    return I18nText.StandardMerge


@node(NodeName.doStandardMerge)
def doStandardMerge(ctx: NodeContext, local: TaskLocal, **kwargs) -> bool:
    """标准融合"""
    if local.standardMergeFSM.is_terminal:
        return True
    if local.standardMergeFSM.status == TaskStatus.PENDING:
        logger.info(f"{ctx.tr(I18nText.StandardMerge).raw}")
        local.standardMergeFSM.start()

    ui = UIOp(ctx)
    ui.activate().sleep(0.1).snapshot()

    select_all = ctx.tr(I18nText.DataMergeSelectAll)
    standard_merge = ctx.tr(I18nText.StandardMerge)

    # 确认在标准融合
    if not ui.search(select_all) and not ui.search(standard_merge):
        logger.warning(f"Text not found: {standard_merge.raw}")
        ui.esc().sleep(1)
        return False

    def _fail_return():
        ui.esc().sleep(0.5)
        if local.fail():
            local.standardMergeFSM.fail()
            return True
        return False

    def _wait_new_echo():
        ui.snapshot()

        if ui.search(ctx.tr(I18nText.DataMergeNewEcho)):
            return True

        # 检查声骸数量不足提示
        if ui.search(ctx.tr(I18nText.PleaseSelectAtLeast5Echoes)):
            return True

        # 检查高品质提示弹窗
        if ui.click_text(ctx.tr(I18nText.DoNotShowAgain), delay=0.3) and ui.click_text(
                ctx.tr(I18nText.Confirm), delay=0.3):
            ui.sleep(0.3)

        return False

    last_time = None

    def _close_new_echo():
        ui.snapshot()

        nonlocal last_time
        if last_time is None:
            last_time = time.monotonic()

        if ui.search(ctx.tr(I18nText.DataMergeSelectAll)) and ui.search(ctx.tr(I18nText.StandardMerge)):
            return True

        # 每隔一段时间检查一次，防止因卡顿等，导致esc被吞，还留在获得声骸页
        if time.monotonic() - last_time < 0.25:
            return False
        if ui.search(ctx.tr(I18nText.DataMergeNewEcho)):
            ui.esc()
        last_time = time.monotonic()

        return False

    # 开始循环融合
    idx = 1
    while idx < 100:
        # 点击全选 合成
        if not ui.search(select_all) and not ui.search(standard_merge):
            return _fail_return()
        logger.info(f"Merge: {idx}")
        ui.click_text(select_all, delay=0.3)
        ui.click_text(standard_merge, delay=0.2)

        # 等待合成结果
        if not ui.sleep(0.4).wait(8, 0.3).until(_wait_new_echo):
            return _fail_return()

        # 声骸不足
        if ui.search(ctx.tr(I18nText.PleaseSelectAtLeast5Echoes)):
            local.standardMergeFSM.complete()
            ui.esc()
            return True

        # 等待回到选择页
        ui.sleep(0.3).esc().sleep(0.3)
        if not ui.wait(8, 0.3).until(_close_new_echo):
            return _fail_return()

        idx += 1

    return _fail_return()


class EchoMergeWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        super().__init__(ctx)

        self.engine = WorkflowEngine()
        self.fsm = TaskFSM(name="EchoMergeWorkflow")
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
            self.fsm.fail()
            raise e

    def __init_task_local(self):
        """根据配置初始化任务状态"""

        self.local.rootFSM.set_enabled(True)
        self.local.dataBankFSM.set_enabled(True)
        self.local.standardMergeFSM.set_enabled(True)

        if not self.local.rootFSM.is_active:
            logger.warning('Task is not active')

    def __init_workflow(self):
        (
            self.engine.source(NodeName.globalDispatcher, is_start=True)
            .on(I18nText.Terminal).to(NodeName.rootDispatcher)
            .on(I18nText.DataMerge).to(NodeName.doDataMerge)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.rootDispatcher)
            .on(I18nText.DataBank).to(NodeName.doDataBank)
            .always().to(NodeName.endNode)
        )

        (
            self.engine.source(NodeName.doDataBank)
            .on(I18nText.DataMerge).to(NodeName.doDataMerge)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doDataMerge)
            .on(I18nText.StandardMerge).to(NodeName.doStandardMerge)
            .always().to(NodeName.globalDispatcher)
        )

        (
            self.engine.source(NodeName.doStandardMerge)
            .on(True).to(NodeName.endNode)
            .always().to(NodeName.globalDispatcher)
        )

        self.engine.exception(NodeName.endNode)
