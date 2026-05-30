import logging
import threading
import time

import numpy as np
from pynput import keyboard

from src.core.contexts import Context
from src.core.i18n import Language
from src.core.interface import ControlService, OCRService, ImgService, WindowService, ODService, BossInfoService
from src.core.pages import Page, Position, TextMatch, ConditionalAction, ImageMatch
from src.core.regions import DynamicPosition, TextPosition
from src.service.page_event_service import PageEventAbstractService
from src.util.wrap_util import timeit

logger = logging.getLogger(__name__)


class DynamicFpsLimit:

    def __init__(self):
        self.key_press_time = None

    def sleep(self, execute_use_seconds: float, fps_lock: float | None = None):
        """
        动态fps
        :param execute_use_seconds:
        :param fps_lock: 固定fps，即不使用动态fps
        :return:
        """
        if fps_lock is None:
            now = time.perf_counter_ns()
            if self.key_press_time is None:
                fps = 1
            else:
                idle_seconds = (now - self.key_press_time) / 1e9
                if idle_seconds < 3:
                    # logger.warning("3秒")
                    fps = 1 / 3  # 按键3秒内有动过，可能不在剧情对话中，检测频率为3秒一次
                elif idle_seconds < 5:
                    fps = 1 / 2  # 2秒一次
                else:  # idle_seconds >= 5
                    fps = 1  # 超过5秒按键没有动过，可能进入剧情，检测频率为1秒一次
        else:
            fps = fps_lock
        seconds = 1 / fps
        # logger.info(f"seconds: {seconds:.2f}")
        sleep_seconds = seconds - execute_use_seconds # 减去流程耗时
        if sleep_seconds > 0.0001:
            logger.debug("sleep: %s", sleep_seconds)
            time.sleep(sleep_seconds)

    def refresh(self):
        self.key_press_time = time.perf_counter_ns()


class AutoStoryServiceImpl(PageEventAbstractService):
    """自动过剧情"""

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService,
                 boss_info_service: BossInfoService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__(context, window_service, img_service, ocr_service, control_service, od_service, boss_info_service)
        self._img_service.set_capture_mode(ImgService.CaptureEnum.FG)

        self._story_pages: list[Page] = []
        self._build_story_pages()
        self._story_conditional_actions: list[ConditionalAction] = []

        # skip_page
        env_skip_is_open = context.spec.skip_is_open
        self.skip_is_open = env_skip_is_open is True # 跳过剧情 还是 沉浸式
        self.skip_btn_is_clicked = False # 是否点击了跳过按钮，用于开启不再提示和剧情梗概的识别
        self.skip_btn_is_clicked_start_time = time.time()
        self.skip_btn_is_clicked_timeout = 3 # 不再提示和剧情梗概识别的最大时间，避免万一clicked状态未变导致每次都识别占用资源

        # auto_play_page
        self._is_auto_play_enabled: bool = False

        # mouse move param
        self._mouse_idle_time = 2.5
        self._mouse_last_check_time = None
        self._listener_thread = None

        # fps limit
        self._dynamic_fps_limit = DynamicFpsLimit()

    def execute(self, **kwargs):
        if not self._window_service.is_foreground_window():
            time.sleep(0.5)
            if self._mouse_last_check_time is not None:
                self._mouse_last_check_time = time.perf_counter()
            self._control_service.activate()
            return

        start_time = time.perf_counter_ns()
        self._execute()
        use_time = time.perf_counter_ns() - start_time
        if use_time > 0.0:
            logger.debug(f"fps: {(1e9 / use_time)}")
        use_seconds = use_time / 1e9

        if self.skip_is_open:
            # 默认一秒一次，点击了跳过则每秒两次
            fps_lock= 8 if self.skip_btn_is_clicked else 1
        else:
            fps_lock = None
        self._dynamic_fps_limit.sleep(use_seconds, fps_lock=fps_lock)
        use_time = time.perf_counter_ns() - start_time
        if use_time > 0.0:
            logger.debug(f"final fps: {(1e9 / use_time)}")

        return

    @timeit(ignore=3)
    def _execute(self, **kwargs):
        # prepare
        src_img = self._img_service.screenshot()
        img = self._img_service.resize(src_img)
        ocr_results: list[TextPosition] | None = None
        # 定制action，防止卡顿

        auto_npc_interact = False
        # 跳过剧情
        if self.skip_is_open:
            # 点击了 跳过 后的数秒内，检查 不再提示 和 剧情梗概
            if time.time() - self.skip_btn_is_clicked_start_time < self.skip_btn_is_clicked_timeout:
                ocr_results = self._ocr_service.ocr(img)
                if self.page_action(self._skip_confirm_page, src_img, img, ocr_results):
                    return
                if self.page_action(self._skip_story_synopsis_page, src_img, img, ocr_results):
                    return
                # self.page_action(self._blank_area_page, src_img, img, ocr_results)
            elif self.skip_btn_is_clicked: # 超时了重置为未点击状态，即恢复默认检测频率，点击状态检测频率更高，无其他作用
                self.skip_btn_is_clicked = False
                return
            if not ocr_results:
                skip_text_match = self._skip_page.get_text_match_by_name("跳过|SKIP")
                ocr_results = self._ocr_service.ocr(img, skip_text_match.position)
            logger.debug("ocr_results: %s", ocr_results)
            if self.page_action(self._skip_page, src_img, img, ocr_results):
                self.skip_btn_is_clicked = True
                self.skip_btn_is_clicked_start_time = time.time()
                return
            self.page_action(self._dialogue_page, src_img, img, ocr_results)
            self.page_action(self._dialogue2_page, src_img, img, ocr_results)
        else:
            if not self._is_auto_play_enabled:
                # 打开自动播放
                if not self.page_action(self._auto_play_page, src_img, img, ocr_results):
                    self.page_action(self._auto_play2_page, src_img, img, ocr_results)
                time.sleep(0.005)
                # if self.page_action(self._auto_play_open_page, src_img, img, ocr_results):
                #     # self._is_auto_play_enabled = True
                #     pass
                # if self.page_action(self._auto_play_open2_page, src_img, img, ocr_results):
                #     # self._is_auto_play_enabled = True
                #     pass
                time.sleep(0.005)

            # 剧情对话框，不跳过，一句一句自动过剧情
            if self.page_action(self._dialogue_page, src_img, img, ocr_results):
                time.sleep(2)
            elif self.page_action(self._dialogue2_page, src_img, img, ocr_results):
                time.sleep(2)

        # NPC交互框
        if auto_npc_interact:
            self.page_action(self._npc_interact_page, src_img, img, ocr_results)

        if not self.skip_is_open:
            self._set_mouse_position_to_bottom_right()

    @staticmethod
    def page_action(page: Page, src_img: np.ndarray, img: np.ndarray, ocr_results: list[TextPosition]) -> bool:
        if not page.is_match(src_img, img, ocr_results):
            return False
        logger.info("当前页面：%s", page.name)
        page.action(page.matchPositions)
        return True

    def _set_mouse_position_to_bottom_right(self):
        if self._mouse_last_check_time is None:
            listener_thread = threading.Thread(target=self._listen_keys)
            listener_thread.daemon = True  # 设置为守护线程，当主线程退出时该线程自动结束
            listener_thread.start()
            self._listener_thread = listener_thread
            self._mouse_last_check_time = time.perf_counter()
            return
        cur_pos = self._control_service.get_mouse_position()
        x1, y1, x2, y2 = self._window_service.get_client_rect_on_screen()
        w, h = self._window_service.get_client_wh()
        center_rect = w * 256 / 2560 / 2
        if abs(cur_pos[0] - (x2 + x1) // 2) > center_rect or abs(cur_pos[1] - (y2 + y1) // 2) > center_rect:  # 要在窗口中心才行
            self._mouse_last_check_time = time.perf_counter()
            return
        logger.debug("鼠标在正中心")
        cur_time = time.perf_counter()
        if cur_time - self._mouse_last_check_time < self._mouse_idle_time:  # 数秒内未动才行
            logger.debug("鼠标悬停时间不够: %s", cur_time - self._mouse_last_check_time)
            return
        # if self._control_service.get_alt_key_state():  # 没按下alt才行
        #     self._mouse_last_check_time = time.perf_counter()
        #     return
        self._control_service.set_mouse_position_to_bottom_right()
        self._mouse_last_check_time = time.perf_counter()
        logger.debug("移动鼠标到右下角")

    def _on_press(self, key):
        logger.debug(f"按键 {key} 被按下")
        self._mouse_last_check_time = time.perf_counter()
        self._dynamic_fps_limit.refresh()

    def _listen_keys(self):
        with keyboard.Listener(on_press=self._on_press) as listener:
            listener.join()

    def get_pages(self) -> list[Page]:
        return self._story_pages

    def get_conditional_actions(self) -> list[ConditionalAction]:
        return self._story_conditional_actions

    def _build_story_pages(self):
        def skip_page_action(positions: dict[str, Position]) -> bool:
            time.sleep(0.1)
            position = positions.get("跳过|SKIP")
            self._control_service.click(*position.center)
            time.sleep(0.1)
            self._control_service.click(*position.center)
            time.sleep(0.1)
            return True

        skip_page = Page(
            name="左上角跳过|SKIP",
            targetTexts=[
                TextMatch(
                    name="跳过|SKIP",
                    text=r"^(跳过|S?KI[PE].{0,3})",
                    open_position=False, # 已在ocr时裁剪了图片，匹配文本时不再限制区域
                    position=DynamicPosition(
                        rate=(
                            0.0,
                            0.0,
                            200 / 1280,
                            150 / 720,
                        ),
                    ),
                ),
            ],
            action=skip_page_action,
        )
        self._story_pages.append(skip_page)
        self._skip_page = skip_page

        def skip_story_synopsis_action(positions: dict[str, Position]) -> bool:
            time.sleep(0.1)
            position = positions.get("跳过剧情")
            self._control_service.click(*position.center)
            time.sleep(0.5)
            return True

        skip_story_synopsis_page = Page(
            name="剧情梗概",
            targetTexts=[
                TextMatch(
                    name="继续观看",
                    text=r"^继续观看$",
                ),
                TextMatch(
                    name="跳过剧情",
                    text=r"^跳过剧情$",
                ),
            ],
            action=skip_story_synopsis_action,
        )
        self._story_pages.append(skip_story_synopsis_page)
        self._skip_story_synopsis_page = skip_story_synopsis_page

        def skip_confirm_page_action(positions: dict[str, Position]) -> bool:
            dont_notice_again_position = positions.get("本次登录不再提示")
            self._control_service.click(*dont_notice_again_position.center)
            time.sleep(0.1)
            confirm_position = positions.get("确认")
            self._control_service.click(*confirm_position.center)
            time.sleep(0.5)
            return True

        skip_confirm_page = Page(
            name="是否确认跳过|SkipConfirm",
            targetTexts=[
                TextMatch(
                    name="完整观看剧情",
                    text="完整观看剧情.*是否确认跳过",
                ),
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
                TextMatch(
                    name="本次登录不再提示",
                    text="本次登录不再提示",
                ),
            ],
            action=skip_confirm_page_action,
        )
        self._story_pages.append(skip_confirm_page)
        self._skip_confirm_page = skip_confirm_page

        def auto_play_page_action(positions: dict[str, Position]) -> bool:
            position = positions.get("自动播放|AutoPlay")
            time.sleep(1.2)
            self._control_service.click(*position.center)
            time.sleep(0.2)
            return True

        auto_play_page = Page(
            name="自动播放|AutoPlay",
            screenshot={
                Language.ZH: [
                    "Dialogue_001.png",
                ],
                Language.EN: [
                ],
            },
            targetImages=[
                ImageMatch(
                    name="自动播放|AutoPlay",
                    image="AutoPlay.png",
                    position=DynamicPosition(
                        rate=(
                            1070 / 1280,
                            0.0,
                            1.0,
                            90 / 720
                        ),
                    ),
                    open_roi_cache=True,
                    confidence=0.8,
                ),
            ],
            action=auto_play_page_action,
        )

        auto_play_2_page = Page(
            name="自动播放|AutoPlay-2",  # 电影黑边
            screenshot={
                Language.ZH: [
                    "Dialogue_001.png",
                ],
                Language.EN: [
                ],
            },
            targetImages=[
                ImageMatch(
                    name="自动播放|AutoPlay",
                    image="AutoPlay2.png",
                    position=DynamicPosition(
                        rate=(
                            1070 / 1280,
                            0.0,
                            1.0,
                            150 / 720
                        ),
                    ),
                    open_roi_cache=True,
                    confidence=0.8,
                ),
            ],
            action=auto_play_page_action,
        )

        self._story_pages.append(auto_play_page)
        self._story_pages.append(auto_play_2_page)
        self._auto_play_page = auto_play_page
        self._auto_play2_page = auto_play_2_page

        def auto_play_open_page_action(positions: dict[str, Position]) -> bool:
            return True

        auto_play_open_page = Page(
            name="自动播放已开启|AutoPlayEnabled",
            screenshot={
                Language.ZH: [
                    "",
                ],
                Language.EN: [
                ],
            },
            targetImages=[
                ImageMatch(
                    name="自动播放已开启|AutoPlayEnabled",
                    image="AutoPlayEnabled.png",
                    position=DynamicPosition(
                        rate=(
                            1070 / 1280,
                            0.0,
                            1.0,
                            150 / 720
                        ),
                    ),
                    open_roi_cache=False,
                    confidence=0.8,
                ),
            ],
            action=auto_play_open_page_action,
        )

        auto_play_open2_page = Page(
            name="自动播放已开启|AutoPlayEnabled-2",  # 电影黑边
            screenshot={
                Language.ZH: [
                    "",
                ],
                Language.EN: [
                ],
            },
            targetImages=[
                ImageMatch(
                    name="自动播放已开启|AutoPlayEnabled",
                    image="AutoPlayEnabled2.png",
                    position=DynamicPosition(
                        rate=(
                            1070 / 1280,
                            0.0,
                            1.0,
                            150 / 720
                        ),
                    ),
                    open_roi_cache=False,
                    confidence=0.8,
                ),
            ],
            action=auto_play_open_page_action,
        )

        self._story_pages.append(auto_play_open_page)
        self._story_pages.append(auto_play_open2_page)
        self._auto_play_open_page = auto_play_open_page
        self._auto_play_open2_page = auto_play_open2_page

        def dialogue_page_action(positions: dict[str, Position]) -> bool:
            if not self.skip_is_open:
                time.sleep(0.5)
                self._control_service.set_mouse_position_to_bottom_right()
                time.sleep(1.5)
            self._control_service.pick_up()
            time.sleep(0.1)
            return True

        dialogue_page = Page(
            name="对话框|Dialogue",
            screenshot={
                Language.ZH: [
                    "Dialogue_001.png",
                ],
                Language.EN: [
                ],
            },
            targetImages=[
                ImageMatch(
                    name="Dialogue",
                    image="Dialogue.png",
                    position=DynamicPosition(
                        rate=(
                            768 / 1280,
                            275 / 720,
                            975 / 1280,
                            560 / 720,
                        ),
                    ),
                    open_roi_cache=False,
                ),
            ],
            action=dialogue_page_action,
        )

        dialogue2_page = Page(
            name="对话框|Dialogue-2",  # 电影黑边
            screenshot={
                Language.ZH: [
                    "Dialogue_001.png",
                ],
                Language.EN: [
                ],
            },
            targetImages=[
                ImageMatch(
                    name="Dialogue",
                    image="Dialogue2.png",
                    position=DynamicPosition(
                        rate=(
                            768 / 1280,
                            275 / 720,
                            1060 / 1280,
                            600 / 720,
                        ),
                    ),
                    open_roi_cache=False,
                ),
            ],
            action=dialogue_page_action,
        )

        self._story_pages.append(dialogue_page)
        self._story_pages.append(dialogue2_page)
        self._dialogue_page = dialogue_page
        self._dialogue2_page = dialogue2_page

        def npc_interact_action(positions: dict[str, Position]) -> bool:
            time.sleep(0.5)
            self._control_service.pick_up()
            time.sleep(0.1)
            return True

        npc_interact_page = Page(
            name="NPC交互框|NpcInteract",
            targetImages=[
                ImageMatch(
                    name="NpcInteract",
                    image="NpcInteract.png",
                    position=DynamicPosition(
                        rate=(
                            768 / 1280,
                            275 / 720,
                            1.0,
                            600 / 720,
                        ),
                    ),
                    open_roi_cache=False,
                ),
            ],
            action=npc_interact_action,
        )
        self._story_pages.append(npc_interact_page)
        self._npc_interact_page = npc_interact_page

        # def blank_area_action(positions: dict[str, Position]) -> bool:
        #     position = positions.get("点击空白处关闭")
        #     self._control_service.click(*position.center)
        #     time.sleep(0.1)
        #     return True
        #
        # blank_area_page = Page(
        #     name="点击空白处关闭",
        #     targetTexts=[
        #         TextMatch(
        #             name="点击空白处关闭",
        #             text="点击空白处关闭",
        #         ),
        #     ],
        #     action=blank_area_action,
        # )
        # self._story_pages.append(blank_area_page)
        # self._blank_area_page = blank_area_page
