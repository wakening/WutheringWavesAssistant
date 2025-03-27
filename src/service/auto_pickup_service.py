import logging
import time

import numpy as np

from src.core.contexts import Context
from src.core.interface import ControlService, OCRService, ImgService, WindowService, ODService
from src.core.pages import Page, Position, TextMatch, ConditionalAction
from src.core.regions import DynamicPosition, TextPosition
from src.service.page_event_service import PageEventAbstractService
from src.util.wrap_util import timeit

logger = logging.getLogger(__name__)


class AutoPickupServiceImpl(PageEventAbstractService):
    """自动拾取"""

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__(context, window_service, img_service, ocr_service, control_service, od_service)
        self._img_service.set_capture_mode(ImgService.CaptureEnum.FG)

        self._pickup_pages: list[Page] = []
        self._build_pickup_pages()
        self._story_conditional_actions: list[ConditionalAction] = []

        self._is_first_skip: bool = True
        self._is_first_auto_play: bool = True

        self._last_execute_time = time.monotonic()

        # fps limit
        self._fps = 15
        self._fps_seconds = 1 / self._fps

    def execute(self, **kwargs):
        if not self._window_service.is_foreground_window():
            time.sleep(0.5)
            return

        start_time = time.perf_counter_ns()
        self._execute()
        use_time = time.perf_counter_ns() - start_time
        if use_time > 0.0:
            logger.debug(f"fps: {(1e9 / use_time)}")
        use_seconds = use_time / 1e9
        if use_seconds + 0.0001 < self._fps_seconds:
            sleep_seconds = self._fps_seconds - use_seconds
            logger.debug("sleep: %s", sleep_seconds)
            time.sleep(sleep_seconds)
        use_time = time.perf_counter_ns() - start_time
        if use_time > 0.0:
            logger.debug(f"final fps: {(1e9 / use_time)}")
        return

    @timeit(ignore=3)
    def _execute(self):
        dynamic_position = self._auto_pickup_page.targetTexts[0].position
        src_img = self._img_service.screenshot(dynamic_position)
        img = self._img_service.resize_by_ratio(src_img)
        ocr_results = self._ocr_service.ocr(img)
        logger.debug(ocr_results)
        # img_util.save_img_in_temp(img)
        is_action = self.page_action(self._auto_pickup_page, img, img, ocr_results)
        logger.debug("is_action: %s", is_action)
        # time.sleep(0.1)

    @staticmethod
    def page_action(page: Page, src_img: np.ndarray, img: np.ndarray, ocr_results: list[TextPosition]) -> bool:
        if not page.is_match(src_img, img, ocr_results):
            return False
        logger.info("当前页面：%s", page.name)
        page.action(page.matchPositions)
        return True

    def get_pages(self) -> list[Page]:
        return self._pickup_pages

    def get_conditional_actions(self) -> list[ConditionalAction]:
        return self._story_conditional_actions

    def _build_pickup_pages(self):

        def auto_pickup_page_action(positions: dict[str, Position]) -> bool:
            position = TextPosition.get(positions, "自动拾取")
            logger.debug("拾取: %s", position.text)
            # sleep_seconds = round(random.uniform(0.0001, 0.002), 6)
            self._control_service.pick_up(0.0001)
            if position.text == "辉光奇藏箱":
                time.sleep(0.1)
                self._control_service.dash_dodge()
            # self._control_service.pick_up(0.00001)
            # time.sleep(0.05)
            # self._control_service.pick_up(sleep_seconds)
            return True

        self._pickup_mapping = {
            # 声骸、武器
            "吸收": "吸收",
            "拾取": "拾取",
            # 采集物
            "莲实": "莲实",
            "木莲": "木莲",
            "鸢尾花": "鸢尾花",
            "地涌莲": "地涌莲",
            "灯笼果": "灯笼果",
            "金阳凤": "金阳凤",
            "云芝": "云芝",
            "傲寒钟": "傲寒钟",
            "紫珊瑚": "紫珊瑚",
            "金铃子": "金铃子",
            "珍珠草": "珍珠草",
            "云露": "云露",
            "夜息香": "夜息香",
            "鸳鸯花": "鸳鸯花",
            "香苏": "香苏",
            "清芬草": "清芬草",
            "香柠草": "香柠草",
            "蚀夜幽兰": "蚀夜幽兰",
            "水灯花": "水灯花",
            "月藻": "月藻",
            "锦色贝": "锦色贝",
            "雨声蜗": "雨声蜗",
            "崖仙子": "崖仙子",
            "伞下客": "伞下客",
            "龙衔珠": "龙衔珠",
            "隐火蜕": "隐火蜕",
            "雀翎果": "雀翎果",
            "龙吐珠": "龙吐珠",
            "银雪莲": "银雪莲",
            "暂星": "暂星",
            "伪贝母": "伪贝母",
            "桂叶": "月桂丛",  # 月桂丛拾取后是桂实、桂叶
            "桂实": "月桂丛",
            "盾金龟": "盾金龟",
            "多肉海兔": "多肉海兔",  # 多肉海兔拾取后是毒莴裙藻，打掉是海兔肉
            "海兔肉": "海兔肉",
            "毒莴裙藻": "毒莴裙藻",
            "铛铛蟹": "铛铛蟹",
            "云凝乳香": "云凝乳香",
            "日冕菊": "日冕菊",
            "青枝果": "青枝果",
            "垂青橄榄": "垂青橄榄",
            "金羊毛": "金羊毛",
            "剑菖蒲": "剑菖蒲",
            "花蕈": "花(?:蕈|草)",
            "妙弋花": "妙.?花",
            "菱果": "白花菱",  # 白花菱拾取后是菱果
            "地丁堇": "地丁.",
            "礼花蒴": "礼花.?",
            # 补充药材
            "银环蜥": "银环蜥",
            "蓝棘蜥": "蓝棘蜥",
            "青竹蜥": "青竹蜥",
            "黑纹蛙": "黑纹蛙",
            "金背蛙": "金背蛙",
            "金环蜓": "金环蜓",
            "蓝羽蝶": "蓝羽蝶",
            "赤羽蝶": "赤羽蝶",
            "羽毛": "羽毛",
            "叶翅蛉": "叶翅.?",
            "霄凤蝶": ".?凤蝶",
            # 补充食材
            "禽肉": "禽肉",
            "鸟蛋": "鸟蛋",
            "兽肉": "兽肉",
            "鱼肉": "鱼肉",
            "群彩": "群彩",
            # 宝箱
            "可疑的宝箱": "可疑的宝箱",
            "朴素奇藏箱": "朴素奇藏箱",
            "基准奇藏箱": "基准奇藏箱",
            "精密奇藏箱": "精密奇藏箱",
            "辉光奇藏箱": "辉光奇藏箱",
            "潮汐之遗": "潮汐之遗",
        }

        # 需完全匹配
        self._pickup_regex_text = (r"^(" + "|".join(set(self._pickup_mapping.values())) + r")$")

        auto_pickup_page = Page(
            name="自动拾取",
            targetTexts=[
                TextMatch(
                    name="自动拾取",
                    text=self._pickup_regex_text,
                    open_position=False,  # 关闭自动限制文本区域，手动处理
                    position=DynamicPosition(
                        rate=(
                            788 / 1280,
                            300 / 720,
                            1100 / 1280,
                            560 / 720,
                        ),
                    ),
                ),
            ],
            excludeTexts=[
                TextMatch(
                    name="背包",
                    text="^(富集区采集|拾方药房|野外采集|商行购买)$",
                ),
            ],
            action=auto_pickup_page_action,
        )
        self._pickup_pages.append(auto_pickup_page)
        self._auto_pickup_page = auto_pickup_page
