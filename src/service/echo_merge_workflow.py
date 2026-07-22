import inspect
import logging
import time
from typing import Optional

from src.core.geometry import AnchorBBox, Align, AnchorPoint
from src.core.i18n import I18nText
from src.core.message import MsgType, MsgTaskStatus
from src.core.pages import I18nPage, I18nPageEchoMerge, OcrQuery
from src.core.task import TaskFSM
from src.core.workflow import node, WorkflowEngine, NodeContext, AbstractWorkflow

logger = logging.getLogger(__name__)


@node()
def end_node(ctx: NodeContext, **kwargs) -> bool:
    logger.debug(inspect.currentframe().f_code.co_name)
    ctx.ipc.event_queue.put({
        "task": {"EchoMergeProcessTask": "finished"}
    }, block=True)
    time.sleep(0.2)
    return True


@node()
def globalDispatcher(ctx: NodeContext, **kwargs) -> Optional[str]:
    logger.debug(inspect.currentframe().f_code.co_name)
    time.sleep(1)

    oq = OcrQuery(ctx).grab().query()
    if not oq.has_results():
        ctx.control_service.esc()
        time.sleep(1)
        logger.debug(f"Ocr nothing")
        return None

    # 已在终端页
    is_match = ctx.page_service.is_match(oq.results, I18nPage.Terminal.PAGE)
    if is_match:
        logger.debug("已在终端")
        return I18nPage.Terminal.PAGE

    # 未知页面，全局扫描，尝试回到主页
    global_result = ctx.page_service.global_page_action(oq.results)
    if global_result:
        logger.debug("找到全局页面")
        time.sleep(1)
        return None

    # 兜底规则，esc
    ctx.control_service.esc()
    logger.debug("未找到任何页面")
    time.sleep(1)
    return None


@node()
def navigateToDataMerge(ctx: NodeContext, **kwargs) -> bool:
    logger.debug(inspect.currentframe().f_code.co_name)

    ctx.control_service.activate()
    time.sleep(0.1)

    oq = OcrQuery(ctx).grab().query()
    if not oq.has_results():
        ctx.control_service.esc()
        time.sleep(1)
        return False

    # 终端
    match_result = ctx.page_service.is_match(oq.results, I18nPage.Terminal.PAGE)
    if not match_result:
        logger.warning(f"Page not found: {I18nPage.Terminal.PAGE}")
        return False

    # 点击进入数据坞
    data_bank = ctx.tr(I18nText.DataBank)
    data_bank_bbox = ctx.scaler.as_bbox(
        AnchorBBox(AnchorPoint(500, 0, Align.Top | Align.Left), AnchorPoint(1280, 720, Align.Right | Align.Bottom)))
    search_result = oq.search(data_bank, data_bank_bbox)
    if not search_result:
        logger.warning(f"Text not found: {data_bank}")
        return False
    bbox = search_result[0]
    ctx.control_service.click(bbox.near)
    time.sleep(1)

    # 等待葫芦等级页面出现
    oq = OcrQuery(ctx)
    match_result = oq.poll(
        lambda: ctx.echo_merge_service.is_match(oq.grab().query().results, I18nPageEchoMerge.DataBank.PAGE),
        timeout=5.0, interval=0.3
    )
    if not match_result:
        logger.warning(f"Page not found: {I18nPageEchoMerge.DataBank.PAGE}")
        return False

    # 点击数据合成侧边栏坐标
    data_merge_point = ctx.scaler.as_point(AnchorPoint(50, 400, Align.Top | Align.Left)).as_tuple()
    time.sleep(0.4)
    ctx.control_service.click(data_merge_point)
    time.sleep(0.3)
    ctx.control_service.click(data_merge_point)
    time.sleep(1)

    # 等待数据合成页面出现
    oq = OcrQuery(ctx)
    match_result = oq.poll(
        lambda: ctx.echo_merge_service.is_match(oq.grab().query().results, I18nPageEchoMerge.DataMerge.PAGE),
        timeout=5.0, interval=0.3
    )
    if not match_result:
        logger.warning(f"Page not found: {I18nPageEchoMerge.DataMerge.PAGE}")
        return False
    # 查找定向融合 TODO 进入定向融合
    targeted_merge = ctx.tr(I18nText.TargetedMerge)
    search_result = oq.search(targeted_merge)
    if not search_result or len(search_result) > 2:
        logger.warning(f"Insufficient text count: {targeted_merge}, expected: 1 or 2")
        return False
    if len(search_result) == 2:
        # 点击标准融合
        bbox = match_result.get(I18nPageEchoMerge.DataMerge.StandardMerge)
        ctx.control_service.click(bbox.near)
        time.sleep(0.2)
        ctx.control_service.click(bbox.center)
        time.sleep(1.0)
    if len(search_result) == 1:
        search_result = oq.search(ctx.tr(I18nText.StandardMerge))
    # 点击进入声骸选择页
    search_result.sort(key=lambda p: p.y2, reverse=True)
    ctx.control_service.click(search_result[0].near)
    time.sleep(0.5)

    need_notice_check = True

    # 开始循环融合
    idx = 0
    while idx < 1000:
        # 等待选择页面出现
        oq = OcrQuery(ctx)
        match_result = oq.poll(
            lambda: ctx.echo_merge_service.is_match(oq.grab().query().results,
                                                    I18nPageEchoMerge.StandardMerge_SelectAll.PAGE),
            timeout=3.0, interval=0.3
        )
        if not match_result:
            logger.warning(f"Page not found: {I18nPageEchoMerge.StandardMerge_SelectAll.PAGE}")
            return False

        # 点击全选 合成
        time.sleep(0.2)
        bbox = match_result.get(I18nPageEchoMerge.StandardMerge_SelectAll.SelectAll)
        ctx.control_service.click(bbox.center)
        time.sleep(0.2)
        bbox = match_result.get(I18nPageEchoMerge.StandardMerge_SelectAll.StandardMerge)
        ctx.control_service.click(bbox.near)
        time.sleep(0.4)

        oq = OcrQuery(ctx).grab().query()
        # 检查弹窗
        if need_notice_check:
            match_result = ctx.echo_merge_service.is_match(oq.results, I18nPageEchoMerge.Notice_IncludesHighRarity.PAGE)
            if match_result:
                bbox = match_result.get(I18nPageEchoMerge.Notice_IncludesHighRarity.DoNotShowAgain)
                time.sleep(0.3)
                ctx.control_service.click(bbox.center)
                time.sleep(0.3)
                bbox = match_result.get(I18nPageEchoMerge.Notice_IncludesHighRarity.Confirm)
                ctx.control_service.click(bbox.center)
                time.sleep(0.5)
            need_notice_check = False

        is_new_echo = None
        is_finished = False
        end_time = time.monotonic() + 5.0
        # 循环等待合成结果
        while True:
            oq = OcrQuery(ctx).grab().query()
            # 检查合成是否完成
            is_new_echo = ctx.echo_merge_service.is_match(oq.results, I18nPageEchoMerge.NewEcho.PAGE)
            if is_new_echo:
                break
            # 检查是否有声骸不足提示，退出
            is_match = ctx.echo_merge_service.is_match(oq.results, I18nPageEchoMerge.StandardMerge_SelectAll.PAGE)
            if is_match:
                search_result = oq.search(ctx.tr(I18nText.PleaseSelectAtLeast5Echoes))
                if search_result:
                    is_finished = True
                    break
            if time.monotonic() >= end_time:
                break
            time.sleep(0.3)

        if is_finished:
            logger.debug(f"声骸融合结束")
            ctx.control_service.esc()
            time.sleep(0.8)
            ctx.control_service.esc()
            time.sleep(1)
            return True
        elif not is_new_echo:
            logger.warning(f"Page not found: {I18nPageEchoMerge.NewEcho.PAGE}")
            return False

        # 合成结果页，esc返回选择声骸页，动画时间不定，可能吞键，循环检查
        for i in range(5):
            time.sleep(0.3)
            ctx.control_service.esc()
            time.sleep(0.3)
            oq = OcrQuery(ctx).grab().query()
            is_match = ctx.echo_merge_service.is_match(oq.results, I18nPageEchoMerge.NewEcho.PAGE)
            if is_match:
                continue
            break

        idx += 1

    return False


class EchoMergeWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        super().__init__(ctx)

        self.engine = WorkflowEngine()
        self.fsm = TaskFSM(name="EchoMergeWorkflow")

        self.__init_workflow()

    def __init_workflow(self):
        (
            self.engine.source("globalDispatcher", is_start=True)
            .when(lambda ctx: ctx.shared.last_result == I18nPage.Terminal.PAGE).to("navigateToDataMerge")
            .always().to("globalDispatcher")
        )

        self.engine.source("navigateToDataMerge").always().to("end_node")

    def execute(self, **kwargs):
        try:
            logger.debug(f"task: {self.__class__.__name__}")
            self.ctx.runtime.taskFSM = self.fsm
            self.fsm.start()
            self.ctx.runtime.send(MsgType.TASK_STATUS, status=MsgTaskStatus.SUCCESS)
            self.ctx.control_service.activate()
            time.sleep(0.1)
            self.engine.run(self, **kwargs)
            self.fsm.complete()
        except Exception as e:
            self.fsm.fail()
            raise e
