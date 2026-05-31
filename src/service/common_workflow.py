import logging
import re
import time
from typing import Optional

from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, BBox, TextBox
from src.core.i18n import I18nText
from src.core.movement import Run, Walk, RouteExecutor
from src.core.pages import UIOp
from src.core.workflow import NodeContext

logger = logging.getLogger(__name__)


def bbox_terminal_content(ctx: NodeContext) -> BBox:
    """终端页右侧功能项所在区域，防止左侧昵称、签名等影响匹配"""
    return ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(540, 0, Align.Left | Align.Top),
        AnchorPoint(1280, 720, Align.Right | Align.Bottom)
    ))


def bbox_dialogue(ctx: NodeContext) -> BBox:
    """对话框所在区域"""
    return ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(788, 280, Align.Center | Align.Middle),
        AnchorPoint(1100, 560, Align.Center | Align.Middle)
    ))


def bbox_guidebook_item(ctx: NodeContext) -> BBox:
    """索拉指南左侧选项区"""
    return ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Left | Align.Top),
        AnchorPoint(454, 720, Align.Left | Align.Bottom),
    ))


def bbox_guidebook_content(ctx: NodeContext) -> BBox:
    """索拉指南右侧内容区，不包含上面的体力值和下面的uid"""
    return ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(454, 75, Align.Left | Align.Top),
        AnchorPoint(1280, 660, Align.Right | Align.Bottom),
    ))


def bbox_hp_bar(ctx: NodeContext) -> BBox:
    """血条"""
    return ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(180, 0, Align.Left | Align.Top),
        AnchorPoint(1280, 612, Align.Right | Align.Bottom),
    ))


def absorb_around_variant(ctx: NodeContext):
    """环绕吸收变体"""
    roi = bbox_dialogue(ctx)
    ui = UIOp(ctx)

    if ui.snapshot(roi=roi).search(ctx.tr(I18nText.Absorb)):
        return absorb_and_claim_rewards(ctx)

    route = [
        Run.forward(0.22), Run.forward(0.23), Run.left(0.22), Run.backward(0.27), Run.backward(0.27),
        Run.right(0.22), Run.forward(0.27), Run.right(0.22), Run.forward(0.23), Run.backward(0.53)
    ]

    for i, step in enumerate(route):
        key = step.direction.get_key()
        # 点按停顿
        if i > 0:
            ctx.control_service.fight_tap(key, 0.05)
            ctx.control_service.fight_tap(key, 0.05)
        ctx.control_service.forward_run(step.duration, key)
        # 等待惯性停止
        time.sleep(0.75)
        if ui.snapshot(roi=roi).search(ctx.tr(I18nText.Absorb)):
            return absorb_and_claim_rewards(ctx)

    return False


def absorb_and_claim_rewards(ctx: NodeContext) -> bool:
    """
    吸收和领取奖励重合
    :param ctx:
    :return:
    """
    ctx.control_service.activate()

    roi = bbox_dialogue(ctx)
    ui = UIOp(ctx)

    tried_empty_once = False
    max_ocr = 3
    count = 0

    while count < max_ocr:
        absorb = ui.snapshot().search(ctx.tr(I18nText.Absorb), roi)

        # 没有吸收，再试一次
        if not absorb:
            if tried_empty_once:
                break
            tried_empty_once = True
            continue

        claim_rewards = ui.search(ctx.tr(I18nText.ClaimRewards))
        # 部分boss可以重新挑战
        challenge_again = ui.search(ctx.tr(I18nText.ChallengeAgain))

        # 有吸收和领取奖励，吸收在下则滚动到下方
        if claim_rewards:
            logger.debug(f"absorb: {absorb}, claim_rewards: {claim_rewards}")

            points = [absorb, claim_rewards]
            if challenge_again:
                points.append(challenge_again)

            # 按 y 排序，找到 absorb 的位置
            sorted_points = sorted(points, key=lambda x: x.y1)
            absorb_index = next(
                (i for i, p in enumerate(sorted_points) if p[0].y1 == absorb[0].y1),
                0
            )
            for _ in range(absorb_index):
                logger.info("向下滚动")
                ctx.control_service.scroll_mouse(-1)
                time.sleep(0.5)

        count += 1
        ctx.control_service.pick_up()
        time.sleep(2)

        if ui.snapshot().search(ctx.tr([I18nText.Confirm, I18nText.CollectSupplies])):
            logger.info("点击到领取奖励，关闭页面")
            ctx.control_service.esc()
            time.sleep(2)

    if count == 0:
        return False
    logger.info("吸收声骸")

    return True


# def claim_rewards_around(ctx: NodeContext):
#     """环绕领取奖励，如无音区"""
#     roi = bbox_dialogue(ctx)
#     ui = UIOp(ctx)
#
#     if ui.snapshot(roi).search(ctx.tr(I18nText.ClaimRewards)):
#         logger.info("发现领取奖励")
#         return True
#
#     route = [
#         Run.forward(0.22), Run.forward(0.23), Run.left(0.22), Run.backward(0.27), Run.backward(0.27),
#         Run.right(0.22), Run.forward(0.27), Run.right(0.22), Run.forward(0.23), Run.backward(0.53)
#     ]
#
#     for i, step in enumerate(route):
#         key = step.direction.get_key()
#         # 点按停顿
#         if i > 0:
#             ctx.control_service.fight_tap(key, 0.05)
#             ctx.control_service.fight_tap(key, 0.05)
#         ctx.control_service.forward_run(step.duration, key)
#         # 等待惯性停止
#         time.sleep(0.75)
#         if ui.snapshot(roi=roi).search(ctx.tr(I18nText.ClaimRewards)):
#             logger.info("发现领取奖励")
#             return True
#
#     return False


def move_and_scan_dialogue(ctx: NodeContext, regex_str: str | list[str], loop: int, steps: int = 2):
    """移动并查找文本"""
    roi = bbox_dialogue(ctx)
    ui = UIOp(ctx)
    executor = RouteExecutor(ctx)
    route = [Walk.forward(steps)]

    for i in range(loop):
        if ui.snapshot(roi=roi).search(regex_str):
            return True
        executor.execute(route)
        ui.sleep(0.2)
        continue
    return False


def query_waveplate(ctx: NodeContext):
    try:
        ui = UIOp(ctx)
        max_waveplate = 240
        # 结晶单质
        waveplate_crystal_regex = r"^\d+$"
        waveplate_crystal_roi = ctx.scaler.as_bbox(AnchorBBox(
            AnchorPoint(730, 0, Align.Right | Align.Top), AnchorPoint(870, 80, Align.Right | Align.Top)))

        # 结晶波片
        total_waveplate_regex = r"^\d+/\d+$"
        total_waveplate_pattern = re.compile(r"^(\d+)/(\d+)$", flags=re.I)
        total_waveplate_roi = ctx.scaler.as_bbox(AnchorBBox(
            AnchorPoint(865, 0, Align.Right | Align.Top), AnchorPoint(1058, 80, Align.Right | Align.Top)))

        # merge_roi = waveplate_crystal_roi.merge(total_waveplate_roi)
        # ui.snapshot(roi=merge_roi, resize=False)
        ui.snapshot(resize=False)

        result = ui.search(waveplate_crystal_regex, waveplate_crystal_roi)
        if result:
            logger.debug(f"waveplate crystal: {result[0].text}")
            waveplate_crystal = int(result[0].text)
        else:
            # 0无法识别
            logger.debug(f"ocr result: {ui.bbox_result}")
            logger.debug("waveplate crystal number not found")
            waveplate_crystal = 0

        result = ui.search(total_waveplate_regex, total_waveplate_roi)
        if not result:
            logger.warning(f"total waveplate number not found")
            return None, None
        logger.debug(f"total waveplate: {result[0].text}")

        match = total_waveplate_pattern.search(result[0].text)
        logger.debug(f"match: {match.group(0)}")
        cur_waveplate = int(match.group(1))
        total_waveplate = int(match.group(2))
        if total_waveplate != max_waveplate:
            return None, None
        logger.info(f"waveplate: {waveplate_crystal}, {cur_waveplate}/{total_waveplate}")
        return cur_waveplate, waveplate_crystal
    except (KeyboardInterrupt, StopError) as e:
        raise e
    except Exception:
        pass
    return None, None


def object_detection(
        ctx: NodeContext,
        search_echo: bool = False,
        search_reward: bool = False,
        timeout: float = 20.0
):
    if not search_echo and not search_reward:
        raise ValueError("Must choose one: search_echo or search_reward")

    ui = UIOp(ctx)
    ui.activate().sleep(0.1).camera_reset().sleep(0.5)

    deadline = time.monotonic() + timeout

    last_box = None
    max_tolerance = 1
    tolerance = max_tolerance
    window_bbox = ctx.window_service.window_bbox()
    dialogue_roi = bbox_dialogue(ctx)
    camera_reset_count = 0

    while time.monotonic() < deadline:
        # 领取奖励
        if ui.snapshot(roi=dialogue_roi).search(ctx.tr(I18nText.ClaimRewards)):
            ui.pick_up().sleep(0.5)
            return True

        absorb = ui.search(ctx.tr(I18nText.Absorb))
        claim_rewards = ui.search(ctx.tr(I18nText.ClaimRewards))
        logger.debug(f"absorb: {absorb}, claim_rewards: {claim_rewards}")

        # 有吸收和领取奖励
        if absorb and claim_rewards:
            # 吸收在下则滚动到下方
            if absorb[0].y1 < claim_rewards[0].y1:
                logger.info("向下滚动")
                ctx.control_service.scroll_mouse(-1)
                time.sleep(0.5)
            ui.pick_up().sleep(2)
        elif absorb:
            ui.pick_up().sleep(2)
        elif claim_rewards:
            pass

        if search_echo:
            det = ctx.od_service.search_echo()
        elif search_reward:
            det = ctx.od_service.search_reward()
        else:
            raise NotImplementedError()

        if det:
            last_box = det
            tolerance = min(max_tolerance, tolerance + 1)
        elif last_box is not None and tolerance > 0:
            det = last_box
            tolerance -= 1

        if det is None:
            camera_reset_count += 1
            if camera_reset_count % 8 == 0:
                # 可能掉在正前方被人物挡住，前进一下再看
                for _ in range(5):
                    ctx.control_service.up(0.08)
                    ui.sleep(0.08)
                for _ in range(3):
                    ctx.control_service.left(0.08)
                ui.sleep(0.1)
                continue
            # ctx.control_service.left(0.1)
            ctx.control_service.key_down("w")
            ctx.control_service.key_down("a")
            ui.sleep(0.1)
            ctx.control_service.key_up("w")
            ctx.control_service.key_up("a")
            ui.sleep(0.2).camera_reset().sleep(0.8)
            continue

        # 前往目标
        echo_x2 = det.x1 + det.width()
        half_window_width = window_bbox.width() // 2

        if det.x1 * 0.75 > half_window_width:  # 目标中在角色右侧
            logger.info("发现目标 向右移动")
            ctx.control_service.right(0.1)
            ui.sleep(0.05)
        elif echo_x2 * 1.1 < half_window_width:  # 目标中在角色左侧
            logger.info("发现目标 向左移动")
            ctx.control_service.left(0.1)
            ui.sleep(0.05)
        else:
            logger.info("发现目标 向前移动")
            # self._control_service.up(0.1)
            # ui.sleep(0.01)
            for _ in range(5):
                ctx.control_service.up(0.1)
                # ctx.control_service.pick_up(0.001)
                if ui.snapshot(roi=dialogue_roi).search(ctx.tr(I18nText.ClaimRewards)):
                    continue
                ui.sleep(0.05)
            ui.sleep(0.5)
    return False


def match_remaining_attempts(result: list[TextBox] | None) -> tuple[Optional[int], Optional[int]]:
    """从文本内提取剩余次数"""
    if not result:
        return None, None
    try:
        # 本周剩余可收取次数: 3/3
        logger.info(f"{result[0].text}")
        match = re.search(r"([0-9o])/(\d)", result[0].text, flags=re.I)
        if not match:
            return None, None
        logger.debug(f"match: {match.group(0)}")
        remain = 0 if match.group(1) in ["0", "O", "o"] else int(match.group(1))
        max_remain = int(match.group(2))
        return remain, max_remain
    except (KeyboardInterrupt, StopError) as e:
        raise e
    except Exception as e:
        logger.exception(e)
        return None, None


def linear_spacing(start: int, end: int, num_points: int, offset=None):
    """
    线性插值（支持整体偏移）
    :param start: 起始位置（第一个点的坐标）
    :param end: 结束位置（最后一个点的坐标）
    :param num_points: 点的总数（>= 2）
    :param offset: 整体偏移量（可选）
               - None: 返回主点位置
               - 数值: 返回 [p + offset for p in 主点位置]
    :return: 所有点的位置坐标
    """
    if num_points < 2:
        raise ValueError("num_points 必须 >= 2")

    # 计算等分位置
    segments = num_points - 1
    positions = []

    for i in range(num_points):
        t = i / segments  # 0 到 1 之间的比例
        pos = start + (end - start) * t
        positions.append(int(pos))

    # 应用偏移
    if offset is not None:
        positions = [p + offset for p in positions]

    return positions
