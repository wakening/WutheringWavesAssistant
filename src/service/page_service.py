import logging
import time
from abc import ABC
from typing import Optional

from src.core.geometry import TextBox
from src.core.i18n import I18N_PAGES, I18N_PAGES_ECHO_MERGE, I18N_TEXT, I18nText, I18N_PAGES_GUIDEBOOK
from src.core.interface import WindowService, PageService, OCRService, ControlService, ImgService, ODService, \
    BossInfoService, EchoMergeService, GlobalPageService, GuidebookService
from src.core.pages import I18nPage, OcrResult, I18nPageX, OcrQuery
from src.core.workflow import NodeContext

logger = logging.getLogger(__name__)


class AbstractPageService(PageService, ABC):

    def __init__(self, context: NodeContext, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService,
                 boss_info_service: BossInfoService):
        self._ctx: NodeContext = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service
        self._ocr_service: OCRService = ocr_service
        self._control_service: ControlService = control_service
        self._od_service: ODService = od_service
        self._boss_info_service: BossInfoService = boss_info_service

    def _matches(self, ocr_result: OcrResult, i18n_page: I18nPageX) -> dict[str, dict[str, TextBox]]:
        matches = {}
        if not ocr_result or not ocr_result.has_results():
            return matches

        lang = self._window_service.get_lang()
        i18n_page.lang = lang

        matcher = i18n_page.i18n_regex_pages.get(lang)
        for page_key, regex_page in matcher.items():
            match_result = regex_page.match(self._window_service.scaler, ocr_result.results)
            if match_result:
                matches[page_key] = match_result
        return matches

    def _match(self, ocr_result: OcrResult, i18n_page: I18nPageX) -> Optional[tuple[str, dict[str, TextBox]]]:
        matches = self._matches(ocr_result, i18n_page)
        return None if len(matches) == 0 else next(iter(matches.items()))

    def _is_match(self, ocr_result: OcrResult, i18n_page: I18nPageX, page_key: str) -> Optional[dict[str, TextBox]]:
        matches = self._matches(ocr_result, i18n_page)
        for match_page_key, match_data in matches.items():
            if match_page_key == page_key:
                return match_data
        return None


class PageServiceImpl(AbstractPageService, GlobalPageService):

    def __init__(self, context: NodeContext, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService,
                 boss_info_service: BossInfoService):
        super().__init__(context, window_service, img_service, ocr_service, control_service, od_service,
                         boss_info_service)
        self._ctx: NodeContext = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service
        self._ocr_service: OCRService = ocr_service
        self._control_service: ControlService = control_service
        self._od_service: ODService = od_service
        self._boss_info_service: BossInfoService = boss_info_service

        self._i18n_page_global = I18nPageX(I18N_PAGES)

        # self._login_reset_z_order = None
        self._login_reset_time = time.perf_counter()

        self._global_action = {
            I18nPage.Terminal.PAGE: self._build_UI_ESC_Terminal,
            I18nPage.Reward_LuniteSubscriptionReward.PAGE: self._build_Reward_LuniteSubscriptionReward,
            I18nPage.Reward_ReceiveRewards.PAGE: self._build_Reward_ReceiveRewards,
            # I18nPage.Boss_Crownless_ResonanceCord.PAGE: self._build_Boss_Crownless_ResonanceCord,
            # I18nPage.Boss_Dreamless_Enter.PAGE: self._build_Boss_Dreamless_Enter,
            # I18nPage.Boss_Jue_Enter.PAGE: self._build_Boss_Jue_Enter,
            # I18nPage.Boss_Hecate_Enter.PAGE: self._build_Boss_Hecate_Enter,
            # I18nPage.Boss_RecommendedLevel.PAGE: self._build_Boss_RecommendedLevel,
            # I18nPage.Boss_StartChallenge.PAGE: self._build_Boss_StartChallenge,
            # I18nPage.Fight_Fight.PAGE: self._build_Fight_Fight,
            # I18nPage.Fight_Absorption.PAGE: self._build_Fight_Absorption,
            # I18nPage.Fight_ChallengeCompleted.PAGE: self._build_Fight_ChallengeCompleted,
            I18nPage.Fight_ClickAlternatelyToBreakFree.PAGE: self._build_Fight_ClickAlternatelyToBreakFree,
            I18nPage.UI_ESC_LeaveInstance.PAGE: self._build_UI_ESC_LeaveInstance,
            I18nPage.Notice_LeaveInstance.PAGE: self._build_Notice_LeaveInstance,
            I18nPage.Notice_ForgeryChallengeComplete.PAGE: self._build_Notice_ForgeryChallengeComplete,
            I18nPage.Notice_TacetSuppression.PAGE: self._build_Notice_TacetSuppression,
            I18nPage.Notice_LoseConsciousness.PAGE: self._build_Notice_LoseConsciousness,
            I18nPage.Notice_SelectRevivalItem.PAGE: self._build_Notice_SelectRevivalItem,
            I18nPage.Notice_Replenish_Waveplate.PAGE: self._build_Notice_Replenish_Waveplate,
            I18nPage.Notice_BlankArea.PAGE: self._build_Notice_BlankArea,
            I18nPage.Login_ClickLink.PAGE: self._build_Login_ClickLink,
            I18nPage.Login_AccountLogin.PAGE: self._build_Login_AccountLogin,
            I18nPage.Login_Disconnected.PAGE: self._build_Login_Disconnected,
            I18nPage.SystemNotice_UpdateCompleteExit.PAGE: self._build_SystemNotice_UpdateCompleteExit,
            I18nPage.SystemNotice_UpdateCompleteConfirm.PAGE: self._build_SystemNotice_UpdateCompleteConfirm,
            I18nPage.SystemNotice_Confirm_DriverVersion.PAGE: self._build_SystemNotice_Confirm_DriverVersion,
            I18nPage.SystemNotice_NetworkTimeout.PAGE: self._build_SystemNotice_NetworkTimeout,
        }

    def matches(self, ocr_result: OcrResult) -> dict[str, dict[str, TextBox]]:
        return self._matches(ocr_result, self._i18n_page_global)

    def match(self, ocr_result: OcrResult) -> Optional[tuple[str, dict[str, TextBox]]]:
        return self._match(ocr_result, self._i18n_page_global)

    def is_match(self, ocr_result: OcrResult, page_key: str) -> Optional[dict[str, TextBox]]:
        return self._is_match(ocr_result, self._i18n_page_global, page_key)

    def global_page_action(self, ocr_result: OcrResult, **kwargs) -> bool:
        match_results = self.matches(ocr_result)
        logger.debug(f"match_result: {match_results}")
        if not match_results:
            return False
        for page_key, bbox_map in match_results.items():
            action = self._global_action.get(page_key)
            if action is None:
                continue
            logger.debug(f"page_key: {page_key}, action: {action.__name__}")
            try:
                action(bbox_map, ocr_result, **kwargs)
                return True
            except Exception as e:
                logger.error(f"page_key: {page_key}, action: {action.__name__}")
                raise e
        return False

    # ------------- Global action --------------

    def _build_UI_ESC_Terminal(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        self._control_service.esc()
        time.sleep(2)
        return True

    def _build_Reward_LuniteSubscriptionReward(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.Reward_LuniteSubscriptionReward.Reward)
        time.sleep(0.2)
        self._control_service.click(textbox.center)
        time.sleep(1)
        self._control_service.click(textbox.center)
        time.sleep(0.2)
        return True

    def _build_Reward_ReceiveRewards(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        self._control_service.esc()
        time.sleep(1)
        self._control_service.esc()
        time.sleep(1)
        return True

    # def _build_Boss_Crownless_ResonanceCord(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
    #     self._control_service.pick_up()
    #     return True

    # def _build_Boss_Dreamless_Enter(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
    #     self._control_service.pick_up()
    #     self._info.in_dungeon = True
    #     self._info.lastBossName = "无妄者"
    #     return True

    # def _build_Boss_Jue_Enter(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
    #     return True
    #
    # def _build_Boss_Hecate_Enter(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
    #     return True

    # def _build_Boss_RecommendedLevel(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
    #     return True
    #
    # def _build_Boss_StartChallenge(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
    #     return True

    # def _build_Fight_Fight(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
    #     return True

    def _build_Fight_Absorption(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        time.sleep(0.2)
        # if not self._ocr_service.find_text(["吸收"]):
        #     return False
        # dump_img()

        # self._info.absorptionCount += 1
        self._control_service.pick_up()
        # time.sleep(0.5)
        # self._info.needAbsorption = False
        # if self._config.CharacterHeal and not self._info.isCheckedHeal:
        #     self._check_heal()
        return True

    # def _build_Fight_ChallengeCompleted(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
    #     # is_nightmare = self._boss_info_service.is_nightmare(self._info.lastBossName)
    #     # if self._ctx.param_config.autoCombatBeta is True:
    #     #     self.combat_system.pause()
    #     #     if is_nightmare:
    #     #         self._control_service.pick_up()
    #     # else:
    #     #     time.sleep(1)
    #     #     return True
    #     #
    #     # if not is_nightmare:
    #     #     time.sleep(1)
    #     #     return True
    #     #
    #     # self.combat_system.exit_special_state(ScenarioEnum.BeforeEchoSearch)
    #     # # logger.info(f"self._info.needAbsorption: {self._info.needAbsorption}")
    #     # if self._info.needAbsorption:
    #     #     self.search_echo()
    #     #
    #     # if self._config.CharacterHeal is not True:
    #     #     return True
    #     # self._check_heal()
    #     # if self._info.needHeal:
    #     #     logger.info("有角色阵亡，开始治疗")
    #     #     # time.sleep(1)
    #     #     # self._info.lastBossName = "治疗"
    #     #     self.transfer()
    #     #     time.sleep(0.5)
    #     return True

    def _build_Fight_ClickAlternatelyToBreakFree(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        for _ in range(4):
            self._control_service.left()
            self._control_service.right()
            time.sleep(0.05)
        return True

    def _build_UI_ESC_LeaveInstance(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.UI_ESC_LeaveInstance.Confirm)
        self._control_service.click(textbox.center)
        return True

    def _build_Notice_LeaveInstance(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.Notice_LeaveInstance.Confirm)
        self._control_service.click(textbox.center)
        return True

    def _build_Notice_ForgeryChallengeComplete(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        time.sleep(0.3)
        textbox = bbox_map.get(I18nPage.Notice_ForgeryChallengeComplete.Exit)
        self._control_service.click(textbox.center)
        return True

    def _build_Notice_TacetSuppression(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.Notice_TacetSuppression.Confirm)
        self._control_service.click(textbox.center)
        return True

    def _build_Notice_LoseConsciousness(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.Notice_LoseConsciousness.Revive)
        self._control_service.click(textbox.center)
        return True

    def _build_Notice_SelectRevivalItem(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        # self._info.needHeal = True
        logger.info("队伍中有角色需要复苏")
        self._control_service.esc()
        return True

    def _build_Notice_Replenish_Waveplate(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        self._control_service.esc()
        time.sleep(2)
        return True

    def _build_Notice_BlankArea(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.Notice_BlankArea.BlankArea)
        self._control_service.click(textbox.center)
        time.sleep(1)
        return True

    def _build_Login_ClickLink(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        # if self._ctx.shared.login_mv_window and not self._login_reset_z_order:
        if time.perf_counter() - self._login_reset_time > 3:
            from src.util import hwnd_util, keymouse_util
            # 1. 先获取当前鼠标位置
            original_x, original_y = keymouse_util.get_mouse_position()
            # 2. 释放鼠标限制（如果有）
            keymouse_util.set_mouse_unlocked()
            # 3. 取消游戏窗口的置顶状态
            hwnd_util.set_window_not_topmost(self._window_service.window)
            # 4. 移动窗口
            hwnd_util.set_window_below_another(self._window_service.window, self._ctx.spec.gui_win_id)
            # hwnd_util.set_window_left_top_and_below_another(self._window_service.window, self._ctx.spec.gui_win_id)
            # 5. 将鼠标移回原位
            keymouse_util.set_mouse_position(original_x, original_y)
            # self._login_reset_z_order = True

        textbox = bbox_map.get(I18nPage.Login_ClickLink.ClickLink)
        self._control_service.click(textbox.center)
        time.sleep(0.2)
        self._control_service.click(textbox.near)
        time.sleep(0.5)
        return True

    def _build_Login_AccountLogin(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        from src.util import hwnd_util
        def click_login_page(login_hwnds) -> bool:
            contains_login_text = False

            try:
                if not isinstance(login_hwnds, list):
                    login_hwnds = [login_hwnds]

                for login_hwnd in login_hwnds:
                    self._control_service.activate_window(login_hwnd)
                    time.sleep(0.1)
                    img = self._img_service.screenshot_window(login_hwnd)
                    oq = OcrQuery(self._ctx).grab(img=img).query()
                    login_keywords = list(I18N_TEXT.get(I18nText.Login).values())
                    search_result = oq.search(login_keywords)
                    if not search_result:
                        continue

                    contains_login_text = True
                    child_hwnds = hwnd_util.get_child_hwnds(login_hwnd)
                    for child_hwnd in child_hwnds:
                        child_wh = hwnd_util.get_client_wh(child_hwnd)
                        if child_wh[0] == 0 or child_wh[1] == 0:
                            continue
                        child_img = self._img_service.screenshot_window(child_hwnd)
                        # img_util.save_img_in_temp(child_img)
                        oq = OcrQuery(self._ctx).grab(img=child_img).query()
                        logger.debug("child_ocr_result: %s", oq.results.results)

                        search_result = oq.search(login_keywords)
                        if not search_result:
                            continue
                        self._control_service.click_window(child_hwnd, *search_result[0].center)
                        time.sleep(0.1)
                        self._control_service.click_window(child_hwnd, *search_result[0].center)
                        time.sleep(0.1)
                        break
            except Exception as e:
                # logger.exception(e)
                pass

            return contains_login_text

        # 手机号登录窗口特殊，是遮盖在游戏上方的另一个窗口句柄
        # 调用游戏窗口截图会截取到登录窗口下层的游戏窗口，点击也是点不到上层
        # 先试官服
        login_hwnd_list = hwnd_util.get_login_hwnd_official()
        if click_login_page(login_hwnd_list):
            logger.info("官服点击登录")
            time.sleep(3)
            return True
        # 再试b服
        login_hwnd = hwnd_util.get_login_hwnd_bilibili()
        if click_login_page(login_hwnd):
            logger.info("b服点击登录")
            return True

        logger.debug("未找到登录页面")
        time.sleep(5)
        return False

    def _build_Login_Disconnected(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.Login_Disconnected.Confirm)
        self._control_service.click(textbox.center)
        time.sleep(2)
        return True

    def _build_SystemNotice_UpdateCompleteExit(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        self._window_service.close_window()
        time.sleep(2)
        return True

    def _build_SystemNotice_UpdateCompleteConfirm(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        self._window_service.close_window()
        time.sleep(2)
        return True

    def _build_SystemNotice_Confirm_DriverVersion(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.SystemNotice_Confirm_DriverVersion.Confirm)
        self._control_service.click(textbox.center)
        time.sleep(2)
        return True

    def _build_SystemNotice_NetworkTimeout(self, bbox_map: dict[str, TextBox], ocr_result: OcrResult, **kwargs):
        textbox = bbox_map.get(I18nPage.SystemNotice_NetworkTimeout.Confirm)
        self._control_service.click(textbox.center)
        time.sleep(2)
        return True


class EchoMergeServiceImpl(AbstractPageService, EchoMergeService):

    def __init__(self, context: NodeContext, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService,
                 boss_info_service: BossInfoService):
        super().__init__(context, window_service, img_service, ocr_service, control_service, od_service,
                         boss_info_service)
        logger.debug("Initializing %s", self.__class__.__name__)

        self._ctx: NodeContext = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service
        self._ocr_service: OCRService = ocr_service
        self._control_service: ControlService = control_service
        self._od_service: ODService = od_service
        self._boss_info_service: BossInfoService = boss_info_service

        self._i18n_page_echo_merge = I18nPageX(I18N_PAGES_ECHO_MERGE)

    def matches(self, ocr_result: OcrResult) -> dict[str, dict[str, TextBox]]:
        return self._matches(ocr_result, self._i18n_page_echo_merge)

    def match(self, ocr_result: OcrResult) -> Optional[tuple[str, dict[str, TextBox]]]:
        return self._match(ocr_result, self._i18n_page_echo_merge)

    def is_match(self, ocr_result: OcrResult, page_key: str) -> Optional[dict[str, TextBox]]:
        return self._is_match(ocr_result, self._i18n_page_echo_merge, page_key)


class GuidebookServiceImpl(AbstractPageService, GuidebookService):

    def __init__(self, context: NodeContext, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService,
                 boss_info_service: BossInfoService):
        super().__init__(context, window_service, img_service, ocr_service, control_service, od_service,
                         boss_info_service)
        logger.debug("Initializing %s", self.__class__.__name__)

        self._ctx: NodeContext = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service
        self._ocr_service: OCRService = ocr_service
        self._control_service: ControlService = control_service
        self._od_service: ODService = od_service
        self._boss_info_service: BossInfoService = boss_info_service

        self._i18n_page_guidebook = I18nPageX(I18N_PAGES_GUIDEBOOK)

    def matches(self, ocr_result: OcrResult) -> dict[str, dict[str, TextBox]]:
        return self._matches(ocr_result, self._i18n_page_guidebook)

    def match(self, ocr_result: OcrResult) -> Optional[tuple[str, dict[str, TextBox]]]:
        return self._match(ocr_result, self._i18n_page_guidebook)

    def is_match(self, ocr_result: OcrResult, page_key: str) -> Optional[dict[str, TextBox]]:
        return self._is_match(ocr_result, self._i18n_page_guidebook, page_key)
