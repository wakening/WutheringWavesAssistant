import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property
from numbers import Number
from typing import Optional, Callable

import numpy as np

from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, BBox, TextBox, Scaler, Point
from src.core.i18n import I18nText
from src.core.movement import Run, Walk, RouteExecutor
from src.core.pages import UIOp
from src.core.workflow import NodeContext
from src.util import img_template_util

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


def bbox_guidebook_title(ctx: NodeContext) -> BBox:
    """索拉指南左上角小标题"""
    return ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 0, Align.Top | Align.Left),
        AnchorPoint(300, 100, Align.Top | Align.Left),
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


class RoiEx:
    """提供一些常用的roi，带缓存，方便在lambda中复用"""

    def __init__(self, ctx):
        self.ctx = ctx
        self.scaler = Scaler(self.ctx.window_service.get_client_wh())

    @cached_property
    def terminal_content(self) -> BBox:
        """终端页右侧功能项所在区域，防止左侧昵称、签名等影响匹配"""
        return self.scaler.as_bbox(AnchorBBox(
            AnchorPoint(540, 0, Align.Left | Align.Top),
            AnchorPoint(1280, 720, Align.Right | Align.Bottom)
        ))

    @cached_property
    def dialogue(self) -> BBox:
        """对话框所在区域"""
        return self.scaler.as_bbox(AnchorBBox(
            AnchorPoint(788, 280, Align.Center | Align.Middle),
            AnchorPoint(1100, 560, Align.Center | Align.Middle)
        ))

    @cached_property
    def guidebook_title(self) -> BBox:
        """索拉指南左上角小标题"""
        return self.scaler.as_bbox(AnchorBBox(
            AnchorPoint(0, 0, Align.Top | Align.Left),
            AnchorPoint(300, 100, Align.Top | Align.Left),
        ))

    @cached_property
    def guidebook_menu(self) -> BBox:
        """索拉指南左侧选项区"""
        return self.scaler.as_bbox(AnchorBBox(
            AnchorPoint(0, 0, Align.Left | Align.Top),
            AnchorPoint(454, 720, Align.Left | Align.Bottom),
        ))

    @cached_property
    def guidebook_content(self) -> BBox:
        """索拉指南右侧内容区，不包含上面的体力值和下面的uid"""
        return self.scaler.as_bbox(AnchorBBox(
            AnchorPoint(454, 75, Align.Left | Align.Top),
            AnchorPoint(1280, 660, Align.Right | Align.Bottom),
        ))

    @cached_property
    def hp_bar(self) -> BBox:
        """血条"""
        return self.scaler.as_bbox(AnchorBBox(
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


class AsyncPickup:
    """异步拾取，为防滥用，设置为全局共享"""

    _EXECUTOR = ThreadPoolExecutor(max_workers=1)

    def __init__(self, ctx, *, delay: float = 0.0, event=None,
                 interval: float | Callable[[], float] = 0.05, timeout: float = 60.0):
        self.ctx = ctx
        self.delay = max(0, min(delay, 60))
        self.event = event
        if self.event is None:
            self.event = threading.Event()
        self.interval = interval
        self.timeout = timeout  # 防止忘了关，没续上就自动停
        self._lock = threading.Lock()
        self._deadline = None

    def _pickup(self):
        if self.timeout > 0:
            self._refresh_deadline()
        with self._lock:
            self._sleep(self.delay)
            while self.event.is_set():
                if self.timeout > 0 and self._deadline is not None and time.monotonic() >= self._deadline:
                    break
                self.ctx.control_service.pick_up()
                # logger.info(f"async pickup")
                if isinstance(self.interval, Number):
                    self._sleep(self.interval)
                else:
                    self._sleep(self.interval())

    def _sleep(self, seconds: float):
        if seconds <= 0:
            return
        t = 0.05
        while seconds > t:
            if not self.event.is_set():
                return
            time.sleep(t)
            seconds -= t
        if not self.event.is_set():
            return
        if seconds > 0:
            time.sleep(seconds)
        return

    def _refresh_deadline(self):
        self._deadline = time.monotonic() + self.timeout

    def start(self):
        self.event.set()
        self._refresh_deadline()
        if not self._lock.acquire(blocking=False):
            return
        try:
            self._EXECUTOR.submit(self._pickup)
        finally:
            self._lock.release()

    def stop(self):
        self.event.clear()
        with self._lock:
            logger.debug(f"Stop async pickup")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()


def absorb_around_variant_blind(ctx: NodeContext):
    """
    路线为：环绕吸收变体
    识别：只有执行前会识别一次，防止刚好就在脚下，及时结束。后续不识别吸收盲捡
    :param ctx:
    :return:
    """
    roi = bbox_dialogue(ctx)
    ui = UIOp(ctx)

    if ui.snapshot(roi=roi).search(ctx.tr(I18nText.Absorb)):
        return absorb_and_claim_rewards(ctx)

    route = [
        Run.forward(0.32), Run.forward(0.33), Run.left(0.32), Run.backward(0.37), Run.backward(0.37),
        Run.right(0.32), Run.forward(0.37), Run.right(0.32), Run.forward(0.33), Run.backward(0.63)
    ]

    executor = RouteExecutor(ctx)

    with AsyncPickup(ctx):
        for i, step in enumerate(route):
            key = step.direction.get_key()
            # 点按停顿
            if i > 0:
                ctx.control_service.fight_tap(key, 0.05)
                ctx.control_service.fight_tap(key, 0.05)

            executor.execute([step])
            time.sleep(0.1)

    return True


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


def query_waveplate_guidebook(ctx: NodeContext):
    """找出体力值，在索拉指南页面的体力区域"""
    # 结晶单质
    waveplate_crystal_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(656, 0, Align.Right | Align.Top), AnchorPoint(798, 80, Align.Right | Align.Top)))

    # 结晶波片
    total_waveplate_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(798, 0, Align.Right | Align.Top), AnchorPoint(984, 80, Align.Right | Align.Top)))

    return _query_waveplate(ctx, waveplate_crystal_roi, total_waveplate_roi)


def query_waveplate_claim_rewards(ctx: NodeContext):
    """找出体力值，副本内，点F领取奖励后弹出的页面里的体力区域"""
    # 结晶单质
    waveplate_crystal_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(723, 0, Align.Right | Align.Top), AnchorPoint(865, 80, Align.Right | Align.Top)))

    # 结晶波片
    total_waveplate_roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(865, 0, Align.Right | Align.Top), AnchorPoint(1048, 80, Align.Right | Align.Top)))

    return _query_waveplate(ctx, waveplate_crystal_roi, total_waveplate_roi)


def _query_waveplate(ctx: NodeContext, waveplate_crystal_roi, total_waveplate_roi):
    try:
        ui = UIOp(ctx)
        max_waveplate = 240
        # 结晶单质
        # waveplate_crystal_regex = r"^\d+$"
        waveplate_crystal_regex = r"^[0-9oO]+$"
        # waveplate_crystal_roi = ctx.scaler.as_bbox(AnchorBBox(
        #     AnchorPoint(730, 0, Align.Right | Align.Top), AnchorPoint(870, 80, Align.Right | Align.Top)))

        # 结晶波片
        # total_waveplate_regex = r"^\d+/\d+$"
        total_waveplate_regex = r"^[0-9oO]+/[0-9oO]+$"
        # total_waveplate_pattern = re.compile(r"^(\d+)/(\d+)$", flags=re.I)
        total_waveplate_pattern = re.compile(r"^([0-9oO]+)/([0-9oO]+)$", flags=re.I)
        # total_waveplate_roi = ctx.scaler.as_bbox(AnchorBBox(
        #     AnchorPoint(865, 0, Align.Right | Align.Top), AnchorPoint(1058, 80, Align.Right | Align.Top)))

        # merge_roi = waveplate_crystal_roi.merge(total_waveplate_roi)
        # ui.snapshot(roi=merge_roi)
        # ui.snapshot(resize=False)
        ui.snapshot()

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

        zero_pattern = re.compile(r"[oO]")
        match = total_waveplate_pattern.search(result[0].text)
        logger.debug(f"match: {match.group(0)}")
        cur_waveplate = int(zero_pattern.sub("0", match.group(1)))
        total_waveplate = int(zero_pattern.sub("0", match.group(2)))
        if total_waveplate != max_waveplate:
            return None, None
        logger.info(f"waveplate: {waveplate_crystal}, {cur_waveplate}/{total_waveplate}")
        return cur_waveplate, waveplate_crystal
    except (KeyboardInterrupt, StopError) as e:
        raise e
    except Exception:
        pass
    return None, None


class ObjectDetector:
    """目标检测"""

    # ---------- 内部辅助类 ----------
    class _TargetTracker:
        """目标位置跟踪器，带有简单容错机制"""

        def __init__(self, max_tolerance: int = 1):
            self.last_box = None
            self.tolerance = max_tolerance
            self.max_tolerance = max_tolerance

        def update(self, detected_box):
            """
            输入本次检测到的目标框（可能为 None）。
            返回应该使用的目标框（detected 或缓存的 last_box）。
            """
            if detected_box:
                self.last_box = detected_box
                self.tolerance = min(self.max_tolerance, self.tolerance + 1)
                return detected_box
            elif self.last_box is not None and self.tolerance > 0:
                self.tolerance -= 1
                return self.last_box
            else:
                self.last_box = None
                return None

    class _WanderHelper:
        """无目标时的探索移动策略"""

        def __init__(self, control, ui):
            self.control = control
            self.ui = ui
            self.step_counter = 0
            self.camera_reset_count = 0

        def reset_step(self):
            self.step_counter = 0

        def wander_and_reset(self):
            """执行一次探索移动，并重置视角，每8次触发特殊绕行"""
            self.step_counter += 1

            # 可能被遮挡，走开一段距离重新识别
            if self.step_counter > 1 and self.step_counter % 5 == 0:
                logger.debug("Special anti-block move: forward + left")
                # for _ in range(5):
                #     self.control.up(0.08)
                #     self.ui.sleep(0.08)
                # for _ in range(3):
                #     self.control.left(0.08)
                try:
                    self.control.key_down("w")
                    self.control.key_down("a")
                    self.ui.sleep(0.8)
                finally:
                    self.control.key_up("w")
                    self.control.key_up("a")
                self.ui.camera_reset().sleep(0.6)
                return

            # 转动视角
            logger.debug("Wandering with WA + camera reset")
            self.control.left(0.1)
            self.ui.sleep(0.2).camera_reset().sleep(0.8)
            self.camera_reset_count += 1
            return

        # def wander_and_reset2(self):
        #     """执行一次探索移动，并重置视角，每8次触发特殊绕行"""
        #     self.step_counter += 1
        #
        #     # 可能被遮挡，走开一段距离重新识别
        #     if self.step_counter % self.batch_size == 0:
        #         if self.step_counter >= self.batch_size * 2:
        #             return
        #         logger.debug("Special anti-block move: forward + left")
        #         for _ in range(5):
        #             self.control.up(0.08)
        #             self.ui.sleep(0.08)
        #         for _ in range(3):
        #             self.control.left(0.08)
        #         self.ui.sleep(0.1)
        #         return
        #
        #     # 转动视角
        #     logger.debug("Wandering with WA + camera reset")
        #     if self.step_counter % self.batch_size == 0:
        #         self.control.key_down("w")
        #         self.control.key_down("a")
        #         self.ui.sleep(0.1)
        #         self.control.key_up("w")
        #         self.control.key_up("a")
        #     else:
        #         self.control.key_down("a")
        #         self.ui.sleep(0.1)
        #         self.control.key_up("a")
        #     self.ui.sleep(0.2).camera_reset().sleep(0.8)

    def __init__(self, ctx: NodeContext):
        self.ctx = ctx

    def absorb_echoes(self, timeout: float = 20.0, enemy_name: Optional[str] = None):
        """
        持续搜索并移动到回声目标，直到出现“吸收”交互项并拾取。
        返回是否成功吸收。
        """
        logger.debug("Absorb echoes")

        ctx = self.ctx
        ui = UIOp(ctx)
        control = ctx.control_service
        od = ctx.od_service
        roi_dialogue = RoiEx(ctx).dialogue
        window_half_width = ctx.window_service.window_bbox().width() // 2

        ui.activate().camera_reset().sleep(0.5)

        tracker = self._TargetTracker(max_tolerance=1)
        wander = self._WanderHelper(control, ui)

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._try_pickup(ui, roi_dialogue):
                return True
            # 转两圈都没有就结束
            if wander.camera_reset_count >= 8:
                break

            detected = od.search_echo_2(boss_name=enemy_name)
            target_box = tracker.update(detected)

            if target_box is None:
                wander.wander_and_reset()
            else:
                wander.reset_step()
                self._move_towards(target_box, control, ui, window_half_width)

        logger.debug("Absorb echoes timeout")
        return False

    # ---------- 辅助方法 ----------
    def _try_pickup(self, ui: "UIOp", roi) -> bool:
        """检测并执行拾取操作，返回是否成功拾取"""
        ui.snapshot(roi=roi)
        absorb = ui.search(self.ctx.tr(I18nText.Absorb))
        if not absorb:
            return False

        # 若“领取奖励”在“吸收”下方，需要滚动
        claim = ui.search(self.ctx.tr(I18nText.ClaimRewards))
        if claim and absorb[0].y1 > claim[0].y1:
            logger.debug("Scroll down to reveal absorb button")
            self.ctx.control_service.scroll_mouse(-1)
            ui.sleep(0.5)

        ui.pick_up().sleep(0.5)
        logger.debug("Successfully absorbed!")
        return True

    def _move_towards(self, target, control, ui, half_width: int):
        """根据目标框在屏幕上的位置，决定转向或前进"""
        center_x = target.x1 + target.width() / 2
        offset = center_x - half_width
        dead_zone = half_width * 0.2  # 屏幕宽度的 20% 作为死区

        if offset < -dead_zone:
            logger.debug("← Target on left, turning left")
            control.left(0.08)
        elif offset > dead_zone:
            logger.debug("→ Target on right, turning right")
            control.right(0.08)
        else:
            logger.debug("↑ Target centered, moving forward")
            control.up(0.1)  # 一次前进，避免过度移动

        ui.sleep(0.05)  # 每次移动后短暂停顿，让画面稳定

    def claim_rewards(self, timeout: float = 20.0):
        logger.debug("Claim rewards")
        ctx = self.ctx


def object_detection(
        ctx: NodeContext,
        search_echo: bool = False,
        search_reward: bool = False,
        timeout: float = 20.0,
        boss_name: Optional[str] = None,
):
    if search_echo:
        logger.debug(f"search_echo: {search_echo}")
    elif search_reward:
        logger.debug(f"search_reward: {search_reward}")
    else:
        raise ValueError("Must choose one: echo or reward")

    ui = UIOp(ctx)
    ui.activate().sleep(0.1).camera_reset().sleep(0.5)

    deadline = time.monotonic() + timeout

    last_box = None
    max_tolerance = 1
    tolerance = max_tolerance
    window_bbox = ctx.window_service.window_bbox()
    roiex = RoiEx(ctx)
    camera_reset_count = 0

    while time.monotonic() < deadline:
        ui.snapshot(roi=roiex.dialogue)
        absorb = ui.search(ctx.tr(I18nText.Absorb))
        claim_rewards = ui.search(ctx.tr(I18nText.ClaimRewards))
        logger.debug(f"absorb: {absorb}, claim_rewards: {claim_rewards}")

        if search_echo:
            if absorb:
                # 有领取奖励，吸收在下则滚动到下方
                if claim_rewards and absorb[0].y1 > claim_rewards[0].y1:
                    logger.info("Scroll down")
                    ctx.control_service.scroll_mouse(-1)
                    time.sleep(0.5)
                ui.pick_up().sleep(0.5)
                return True
            elif absorb:
                ui.pick_up().sleep(1)
        else:
            # 领取奖励
            if claim_rewards:
                ui.pick_up().sleep(0.5)
                return True
            elif absorb:
                ui.pick_up().sleep(1)

        if search_echo:
            det = ctx.od_service.search_echo_2(boss_name=boss_name)
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
                if ui.snapshot(roi=roiex.dialogue).search(ctx.tr(I18nText.ClaimRewards)):
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


def search_icon_guidebook(ctx: NodeContext, *, icon: np.ndarray) -> tuple[int, int] | None:
    roi = ctx.scaler.as_bbox(AnchorBBox(
        AnchorPoint(0, 85, Align.Left | Align.Top),
        AnchorPoint(99, 720, Align.Left | Align.Top),
    )).as_tuple()
    img = ctx.img_service.screenshot()
    bbox = img_template_util.find_icon_in_roi_accelerated(
        img,
        icon,
        roi=roi,
        scale_min=0.4,
        scale_max=2.0,
        scale_step=0.03,
    )
    logger.debug(f"bbox: {bbox}")
    if bbox is None or bbox.score < 0.7:
        return None
    return bbox.near


class RateLimiter:
    """
    速率控制器
    目标：限制调用频率，防止CPU过高
    """

    def __init__(self, rate: float):
        # rate表示每秒执行次数
        if rate <= 0:
            raise ValueError("rate must be > 0")

        self.interval = 1.0 / rate
        self.next_time = None

    def __call__(self) -> float:
        now = time.monotonic()

        if self.next_time is None:
            self.next_time = now + self.interval
            return 0.0

        wait = self.next_time - now

        if wait <= 0:
            self.next_time += self.interval
            if self.next_time < now:
                self.next_time = now + self.interval
            return 0.0

        return round(wait, 6)


class Slider:
    """滑块"""

    # @staticmethod
    # def __find_bar_bottom(point: Point, img: np.ndarray):
    #     """滑块底部的点"""
    #     column = img[point.y:, point.x]
    #     # bgr 219 221 203
    #     is_white = np.all(column > 185, axis=1)
    #     indices = np.flatnonzero(~is_white)
    #     y = point.y + indices[0] if indices.size else img.shape[0] - 1
    #     return Point(point.x, y)

    @staticmethod
    def __find_slider(point: Point, img: np.ndarray):
        """查找滑块"""
        column = img[point.y:, point.x]
        is_white = np.all(column > 185, axis=1)
        # 找白色起点
        start_indices = np.flatnonzero(is_white)
        if not start_indices.size:
            return None, None
        start = start_indices[0]
        # 从白色起点开始，找第一个非白色点
        end_indices = np.flatnonzero(~is_white[start:])
        if end_indices.size:
            end = start + end_indices[0] - 1
        else:
            end = img.shape[0] - 1
        return (
            Point(point.x, point.y + start),
            Point(point.x, point.y + end),
        )

    @classmethod
    def __points(cls, img: np.ndarray, top: Point, bottom: Point, rate: float) -> list[Point]:
        """
        生成滑块移动轨迹点
        :param img:
        :param top: 滑轨起点，y大概就行
        :param bottom: 滑轨终点
        :param rate: 移动比例
        :return:
        """
        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        slider_top = scaler.as_point(AnchorPoint(top.x, top.y, Align.Top | Align.Right))
        track_bottom = scaler.as_point(AnchorPoint(bottom.x, bottom.y, Align.Bottom | Align.Right))

        # 找出滑块位置，修正滑块顶端位置
        new_slider_top, slider_bottom = cls.__find_slider(slider_top, img)
        if not new_slider_top or not slider_bottom:
            logger.warning(f"Slider not found")
            return []

        step = (slider_bottom.y - new_slider_top.y) * rate
        points = [slider_bottom]
        while True:
            p = Point(points[-1].x, int(points[-1].y + step))
            if p.y >= track_bottom.y:
                break
            points.append(p)
        points.append(track_bottom)

        logger.debug(f"slider points: {points}")
        return points

    @classmethod
    def points(cls, img: np.ndarray) -> list[Point]:
        """索拉指南素材获取页，通用右侧滑块移动轨迹点"""
        return cls.__points(img, Point(1245, 100), Point(1245, 633), 0.4)
