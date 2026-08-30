import ctypes
import logging
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import win32con

from src.core.color import ColorRule, Color, RuleMode
from src.core.combat.combat_system import CombatSystem
from src.core.exceptions import StopError
from src.core.geometry import AnchorBBox, Align, AnchorPoint, Scaler
from src.core.i18n import I18nText, Language
from src.core.pages import UIOp
from src.core.resonator import TeamMember, Resonator
from src.core.resource import Resource, Icon
from src.core.workflow import NodeContext, AbstractWorkflow
from src.service.common_workflow import RateLimiter
from src.util import img_util, img_template_util
from src.util.img_sift_util import SIFTFeatureMatcher

logger = logging.getLogger(__name__)


class KeyListener:
    def __init__(self, *, event, interval=0.001):
        """
        interval: 轮询间隔(秒)，建议 0.001~0.005
        """
        self.interval = interval
        self.event = event
        self._running = False
        self._thread = None

        self._callbacks = {}
        self._last_state = {}

    def register(self, vk, callback):
        """
        callback(vk, is_down)
        """
        self._callbacks[vk] = callback
        self._last_state[vk] = False

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def join(self, timeout=None):
        if self._thread:
            self._thread.join(timeout)

    def _loop(self):
        while self._running and self.event.is_set():
            for vk, callback in self._callbacks.items():
                down = bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)

                last = self._last_state[vk]

                if down != last:
                    self._last_state[vk] = down
                    callback(vk, down)

            time.sleep(self.interval)


class ExploreWorkflow(AbstractWorkflow):

    def __init__(self, ctx: NodeContext):
        super().__init__(ctx)

        self.combat_system = None
        self.click_cooldown = 0.5  # 防止重复点击间隔时间，秒
        self.last_time = time.monotonic() - self.click_cooldown
        self.ui = UIOp(ctx)
        self.ctx = ctx
        self.matcher = SIFTFeatureMatcher()
        self.members_roi = [
            AnchorBBox(
                AnchorPoint(1140, 116, Align.Top | Align.Right),
                AnchorPoint(1280, 210, Align.Top | Align.Right),
            ),
            AnchorBBox(
                AnchorPoint(1140, 210, Align.Top | Align.Right),
                AnchorPoint(1280, 300, Align.Top | Align.Right),
            ),
            AnchorBBox(
                AnchorPoint(1130, 300, Align.Top | Align.Right),
                AnchorPoint(1280, 400, Align.Top | Align.Right),
            ),
        ]
        self.pickup_texts = ctx.tr([
            I18nText.PickAbsorb,
            I18nText.PickPickUp,
            # I18nText.PickActivate,
            I18nText.PickLotusSeeds,
            I18nText.PickClimbingFig,
            I18nText.PickIris,
            I18nText.PickTerraspawnFungus,
            I18nText.PickLanternberry,
            I18nText.PickPecokFlower,
            I18nText.PickCoriolus,
            I18nText.PickWintryBell,
            I18nText.PickVioletCoral,
            I18nText.PickBittberry,
            I18nText.PickPearlLeaf,
            I18nText.PickDewvetch,
            I18nText.PickNoctemint,
            I18nText.PickHoneysuckle,
            I18nText.PickPerilla,
            I18nText.PickAngelica,
            I18nText.PickLemongrass,
            I18nText.PickErodorchid,
            I18nText.PickWaterlamp,
            I18nText.PickBunnywort,
            I18nText.PickChromeshell,
            I18nText.PickDripsnail,
            I18nText.PickCliffrecluse,
            I18nText.PickUmbragricus,
            I18nText.PickGemberry,
            I18nText.PickGloomSlough,
            I18nText.PickPavoPlum,
            I18nText.PickLoongsPearl,
            I18nText.PickSilverLotus,
            I18nText.PickNova,
            I18nText.PickAirsailer,
            I18nText.PickSeaFlytrap,
            I18nText.PickLaurusSprouts,
            I18nText.PickGoldcrestScarab,
            I18nText.PickSeaBunny,
            I18nText.PickHeliobaneFungia,
            I18nText.PickBellCrab,
            I18nText.PickMasticNuvola,
            I18nText.PickSunflareEverlasting,
            I18nText.PickViscumBerry,
            I18nText.PickFelicitousOlives,
            I18nText.PickGoldenFleece,
            I18nText.PickSwordAcorus,
            I18nText.PickEdodes,
            I18nText.PickBellePoppy,
            I18nText.PickCaltrop,
            I18nText.PickViola,
            I18nText.PickFirecrackerJewelweed,
            I18nText.PickSeasideCendrelis,
            I18nText.PickOaknut,
            I18nText.PickBambooIris,
            I18nText.PickBloodleafViburnum,
            I18nText.PickAbyssLuminary,
            I18nText.PickAfterlife,
            I18nText.PickPaintedMantisShrimp,
            I18nText.PickSliverglowBloom,
            I18nText.PickLuminousCalendula,
            I18nText.PickStoneRose,
            I18nText.PickSummerFlower,
            I18nText.PickCreepingTorchpineNeedle,
            I18nText.PickDuskHoneypot,
            I18nText.PickFernSpore,
            I18nText.PickCradleLichen,
            I18nText.PickGeminiSpore,
            I18nText.PickRimewisp,
            I18nText.PickArithmeticShell,
            I18nText.PickWaxweaverWeb,
            I18nText.PickEdelschnee,
            I18nText.PickMossAmber,
            I18nText.PickFoxtailKelp,
            I18nText.PickFrostwort,
            I18nText.PickDreamOfStars,
            I18nText.PickRedbell,
            I18nText.PickForgetMeNot,
            I18nText.PickPrismFruit,
            I18nText.PickPastReveries,
            I18nText.PickCloudperchSeed,
            I18nText.PickFlowborneDream,
            I18nText.PickBladeBlossom,
            I18nText.PickUncrackedJade,
            I18nText.PickClimberShoots,
            I18nText.PickWhiteJadeBeauty,
            I18nText.PickOpusStone,
            I18nText.PickLeafweaver,
            I18nText.PickFloralCrestJade,
            I18nText.PickSilverBandedLizard,
            I18nText.PickAzureLizard,
            I18nText.PickGreenPitLizard,
            I18nText.PickBlackStripedFrog,
            I18nText.PickGoldenbackFrog,
            I18nText.PickGoldenringedDragonfly,
            I18nText.PickBlueFeatherButterfly,
            I18nText.PickRedFeatherButterfly,
            I18nText.PickFeather,
            I18nText.PickChrysopa,
            I18nText.PickPhoenixButterfly,
            I18nText.PickFowl,
            I18nText.PickBirdEgg,
            I18nText.PickRawMeat,
            I18nText.PickFish,
            I18nText.PickTetra,
            I18nText.PickSuspiciousChest,
            I18nText.PickBasicSupplyChest,
            I18nText.PickStandardSupplyChest,
            I18nText.PickAdvancedSupplyChest,
            I18nText.PickPremiumSupplyChest,
            I18nText.PickTidalSupplyChest,
            I18nText.PickTidalHeritage,
            I18nText.PickAdvancedSupplyPack,
        ])

        self.count = 1

        self.task_limiter = RateLimiter(1)
        self.pickup_task_limiter = RateLimiter(5)
        self.foreground_window_limiter = RateLimiter(2)
        self.active_limiter = RateLimiter(0.5)

        self.combat_lock = threading.Lock()
        self.async_skip_lock = threading.Lock()
        self.async_init_lock = threading.Lock()
        self.async_init_ocr_lock = threading.Lock()

        self.executor = ThreadPoolExecutor(max_workers=3)
        self.__async_init()

    def execute(self, **kwargs):
        logger.debug(f"task: {self.__class__.__name__}")

        cfg = self.ctx.runtime.cfg.explore
        logger.debug(f"{cfg}")
        logger.info(
            f"AutoCombat: {cfg.autoCombat}, AutoPickup: {cfg.autoPickup}, SkipStory: {cfg.skipStory}, AutoDialogue: {cfg.autoDialogue}")
        if not cfg.autoCombat and not cfg.autoPickup and not cfg.skipStory and not cfg.autoDialogue:
            return

        # 自动战斗任务
        listener = None
        if cfg.autoCombat:
            listener = KeyListener(event=self.ctx.runtime.stop_event, interval=0.005)
            listener.register(win32con.VK_XBUTTON1, self._on_click)
            listener.register(win32con.VK_ESCAPE, self._on_press)
            listener.start()

        ui = UIOp(self.ctx)
        idx = 0
        last_pickup_task_limit = 0

        while ui.is_set():
            try:
                # 游戏必须在前台
                if self.foreground_window_limiter() == 0 and not self.ctx.window_service.is_foreground_window():
                    # logger.info(f"foreground window disabled")
                    ui.sleep(1)
                    continue

                # 战斗中不做其他事
                if self.combat_system is not None:
                    ui.sleep(0.3)
                    continue

                # 循环间隔
                ui.sleep(0.1)
                idx += 1

                # 定时
                if self.active_limiter() == 0:
                    ui.activate()

                # 限速
                if self.task_limiter() == 0:
                    # logger.info(f"idx task: {idx}")
                    img = ui.grap()

                    # 剧情：跳过剧情
                    if cfg.skipStory and self._skip(img):
                        continue

                    # 剧情：自动对话
                    if not cfg.skipStory and cfg.autoDialogue and self._dialogue(img):
                        continue

                    # 剧情：自动播放
                    if (cfg.skipStory or cfg.autoDialogue) and self._play(img):
                        continue

                    # 大世界：自动拾取
                    if cfg.autoPickup and self._pickup(img):
                        continue
                elif cfg.autoPickup:
                    limit = self.pickup_task_limiter()
                    if limit > 0:
                        last_pickup_task_limit = limit
                        # logger.info(f"pickup_task_limit: {limit}")
                        continue
                    # 最小等待时间
                    if last_pickup_task_limit == 0 and limit == 0:
                        # logger.info(f"Min pickup sleep: {idx}")
                        ui.sleep(0.1)
                    last_pickup_task_limit = limit

                    # logger.info(f"idx pickup: {idx}")

                    # start_time = time.monotonic()
                    img = ui.grap()
                    if cfg.autoPickup and self._pickup(img):
                        # logger.info(f"pickup耗时：{time.monotonic() - start_time}")
                        continue
                    # logger.info(f"pickup耗时：{time.monotonic() - start_time}")

            except (KeyboardInterrupt, StopError) as e:
                raise e
            except Exception as e:
                logger.exception(e)

        if listener is not None:
            listener.join()

    def __async_init(self):

        def _foo():
            with self.async_init_lock:
                TeamMember.load_role_features()

        def _bar():
            with self.async_init_ocr_lock:
                # 预热
                UIOp(self.ctx).snapshot(img=img_util.create_dummy())

        self.executor.submit(_foo)
        self.executor.submit(_bar)

    def _skip(self, img):
        ui = UIOp(self.ctx)
        if ui.is_on_homepage(img):
            return False

        roi = AnchorBBox(
            AnchorPoint(0, 0, Align.Left | Align.Top),
            AnchorPoint(100, 150, Align.Left | Align.Top),
        )
        search_btn = lambda _img: self.__search_btn(
            _img, Icon.plotBtnSkip(), roi,
            scale_min=0.238,  # 全屏：score=0.9217, scale=0.314，黑边；score=0.9108, scale=0.238
            scale_max=0.314,
            scale_step=0.314 - 0.238,
            early_score=0.85,
            score_max=0.75,
        )
        if not (icon_point := search_btn(img)):
            return False

        logger.info(f"Skip")
        ui.click_point(icon_point, times=3, interval=0.2)

        # # 等待初始化完成
        # with self.async_init_ocr_lock:
        #     pass

        last_time = time.monotonic()
        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        build = lambda x, y: scaler.as_point(AnchorPoint(x, y, Align.Center | Align.Middle))

        # summary
        summary_points = [
            build(335, 518),
            build(346, 513),
            build(458, 499),
            build(466, 496),
            build(335 + 790 - 335, 518),
            build(346 + 790 - 335, 513),
            build(458 + 790 - 335, 499),
            build(466 + 790 - 335, 496),
        ]
        summary_cutscene_points = [
            build(415, 476),
            build(524, 478),
            build(503, 465),
            build(510, 461),
            build(415 + 754 - 415, 476),
            build(524 + 754 - 415, 478),
            build(503 + 754 - 415, 465),
            build(510 + 754 - 415, 461),
        ]
        summary_cr = ColorRule().points(summary_points).colors(Color.bgr(255, 255, 255), mode=RuleMode.ALL)
        summary_cutscene_cr = ColorRule().points(summary_cutscene_points).colors(
            Color.bgr(255, 255, 255), mode=RuleMode.ALL)

        # skip confirm
        btn_black_points = [
            build(355, 460),
            build(372, 458),
            build(477, 445),
            build(489, 443),
            build(355 + 764 - 355, 460),
            build(372 + 764 - 355, 458),
            build(477 + 764 - 355, 445),
            build(489 + 764 - 355, 443),
        ]
        bg_white_points = [
            build(578, 236),
            build(677, 236),
            build(793, 236),
            build(627, 455),
        ]
        btn_black_cr = ColorRule().points(btn_black_points).colors(Color.bgr(21, 21, 21), mode=RuleMode.ALL)
        bg_white_cr = ColorRule().points(bg_white_points).colors(Color.bgr(244, 244, 244), mode=RuleMode.ALL)

        def _():
            if not self.async_skip_lock.acquire(blocking=False):
                return True

            try:
                deadline = time.monotonic() + 4
                idx = 0
                while ui.is_set() and time.monotonic() < deadline:
                    nonlocal last_time

                    # _start_time = time.monotonic()
                    # ui.snapshot()
                    # logger.info(f"async skip耗时: {time.monotonic() - _start_time:2f}")
                    # if (ui.search(self.ctx.tr(I18nText.Summary))
                    #         and ui.search(self.ctx.tr(I18nText.SummaryResume))
                    #         and ui.click_text(self.ctx.tr(I18nText.SummarySkip), times=3, interval=0.2)):
                    #
                    #     img_util.save_img_in_temp(ui.img)
                    #
                    #     return True
                    # elif (ui.search(self.ctx.tr(I18nText.AreYouSureYouWantToProceed))
                    #       and ui.click_text(self.ctx.tr(I18nText.DoNotShowAgain), delay=0.2)
                    #       and ui.click_text(self.ctx.tr(I18nText.Confirm), delay=0.1, times=2, interval=0.3)):
                    #     return True

                    _img = ui.grap()

                    if summary_cr.match(_img):  # 全屏
                        logger.debug(f"summary_cr")
                        ui.click_point(build(865, 509), delay=0.1, times=3, interval=0.3)
                        return True
                    elif summary_cutscene_cr.match(_img):  # 黑边
                        logger.debug(f"summary_cutscene_cr")
                        ui.click_point(build(809, 471), delay=0.1, times=3, interval=0.3)
                        return True
                    elif btn_black_cr.match(_img) and bg_white_cr.match(_img):
                        logger.debug(f"confirm_cr")
                        ui.click_point(build(642, 397), delay=0.3)
                        ui.click_point(build(841, 453), delay=0.1, times=3, interval=0.3)
                        return True
                    else:
                        logger.debug(f"cr none")

                    if idx > 0 and time.monotonic() - last_time > 0.5 and ui.is_on_homepage(_img):
                        return True

                    if _icon_point := search_btn(_img):
                        logger.debug(f"skip: {_icon_point}")
                        ui.click_point(_icon_point, times=2, interval=0.2)

                    idx += 1
                    ui.sleep(0.3)
            finally:
                self.async_skip_lock.release()

            return False

        # 锁被占用，控制并发
        if not self.async_skip_lock.locked():
            # 锁未被占用，异步检查跳过剧情弹窗
            self.executor.submit(_)
        return True

    def _play(self, img):
        ui = UIOp(self.ctx)
        if ui.is_on_homepage(img):
            return False

        roi = AnchorBBox(
            AnchorPoint(1088, 0, Align.Right | Align.Top),
            AnchorPoint(1183, 150, Align.Right | Align.Top),
        )
        if icon_point := self.__search_btn(
                img, Icon.plotBtnPlay(), roi,
                scale_min=0.229,  # 全屏：score=0.9082, scale=0.308，黑边：score=0.8751, scale=0.229
                scale_max=0.308,
                scale_step=0.308 - 0.229,
                early_score=0.83,
                score_max=0.75,
        ):
            logger.info(f"Autoplay")
            ui.click_point(icon_point)
            return True
        return False

    def _dialogue(self, img):
        roi = AnchorBBox(
            AnchorPoint(768, 275, Align.Right | Align.Top),
            AnchorPoint(1060, 600, Align.Right | Align.Top),
        )
        if self.__search_btn(
                img, Icon.interactionIcon04(), roi,
                scale_min=0.417,  # 全屏：score=0.9131, scale=0.417，黑边：
                scale_max=0.417,
                scale_step=0.01,
                early_score=0.85,
                score_max=0.75,
        ):
            ui = UIOp(self.ctx)
            logger.info(f"Dialogue")
            ui.sleep(1.5)
            ui.pick_up()
            return True
        return False

    def _pickup(self, img):
        ui = UIOp(self.ctx)
        if not ui.is_on_homepage(img):
            return False

        # 检查F
        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        pick_points = [
            scaler.as_point(AnchorPoint(815, 366, Align.Center | Align.Middle)),
            scaler.as_point(AnchorPoint(826, 366, Align.Center | Align.Middle)),
            scaler.as_point(AnchorPoint(815, 377, Align.Center | Align.Middle)),
            scaler.as_point(AnchorPoint(826, 377, Align.Center | Align.Middle)),
        ]
        pick_cr = ColorRule().points(pick_points).colors(Color.bgr(240, 240, 240), mode=RuleMode.ALL)
        if not pick_cr.match(img, scaler):
            return False

        with self.async_init_ocr_lock:
            pass

        roi = AnchorBBox(
            AnchorPoint(788, 300, Align.Center | Align.Middle),
            AnchorPoint(1100, 560, Align.Center | Align.Middle),
        )
        ui.snapshot(img=img, roi=roi)

        for text in self.pickup_texts:
            res = ui.search(text)
            if not res:
                continue
            logger.info(text.raw)
            ui.pick_up(times=max(3, min(5, len(res) + 1)), interval=round(random.uniform(0.06, 0.10), 3))
            return True
        return False

    @staticmethod
    def __search_btn(
            img: np.ndarray, icon: np.ndarray, roi: AnchorBBox,
            scale_min,
            scale_max,
            scale_step,
            early_score=0.90,
            score_max=0.85,
    ) -> tuple[int, int] | None:
        scaler = Scaler(cur_wh=(img.shape[1], img.shape[0]))
        roi = scaler.as_bbox(roi).as_tuple()
        bbox = img_template_util.find_icon_in_roi_accelerated(
            img,
            icon,
            roi=roi,
            scale_min=scale_min,
            scale_max=scale_max,
            scale_step=scale_step,
            early_score=early_score,
        )
        logger.debug(f"bbox: {bbox}")
        if bbox is None or bbox.score < score_max:
            return None
        return bbox.random

    def _on_click(self, button, pressed):
        if not pressed:  # 忽略弹起信号
            return True
        try:
            # logger.info(f"[{self.count:03d}] XButton1 在位置 ({x}, {y}) 被按下")
            with self.combat_lock:
                # 没启动就启动，已启动就停止
                if self.combat_system is None:
                    if not self.ctx.window_service.is_foreground_window():
                        logger.info(f"[{self.count:03d}] Not in foreground")
                        return True

                    logger.info(f"[{self.count:03d}] XButton1 start")
                    self.last_time = time.monotonic()

                    # 等待资源加载
                    with self.async_init_lock:
                        pass

                    img = self.ui.grap()
                    if not self.ui.is_on_homepage(img):
                        logger.warning(f"[{self.count:03d}] Not in the overworld")
                        # return True

                    member_count = TeamMember.get_size(img)
                    logger.debug(f"member_count: {member_count}")

                    team_members = TeamMember.member_keys(img)
                    for i in range(3):
                        if i + 1 <= member_count:
                            if not team_members[i] or not (tr_res := self.ctx.tr(team_members[i], lang=Language.ZH)):
                                team_members[i] = "unknown"
                                continue
                            team_members[i] = tr_res.raw
                        else:
                            team_members[i] = None

                    combat_system = CombatSystem(self.ctx.control_service, self.ctx.img_service)
                    combat_system.set_resonators(team_members)
                    combat_system.is_async = True
                    combat_system.check_boss_hp = False
                    combat_system.auto_pickup = True
                    combat_system.start(10 * 60)
                    self.combat_system = combat_system
                else:
                    if time.monotonic() - self.last_time < self.click_cooldown:
                        logger.info(f"[{self.count:03d}] Click Cooldown")
                        return True
                    logger.info(f"[{self.count:03d}] XButton1 stop")
                    self.count += 1
                    combat_system = self.combat_system
                    self.combat_system = None
                    if combat_system is not None:
                        combat_system.stop()
        except KeyboardInterrupt as e:
            return False
        except StopError as e:
            pass
        except Exception as e:
            logger.exception(e)
        return True

    def _on_press(self, key, pressed):
        if not pressed:  # 忽略弹起信号
            return True
        try:
            with self.combat_lock:
                combat_system = self.combat_system
                self.combat_system = None
                if combat_system is not None:
                    logger.info(f"[{self.count:03d}] ESC stop")
                    self.count += 1
                    combat_system.stop()
                else:
                    logger.info(f"[{self.count:03d}] ESC skip")
        except KeyboardInterrupt as e:
            return False
        except StopError as e:
            pass
        except Exception as e:
            logger.exception(e)
        return True
