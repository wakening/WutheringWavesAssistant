import logging
import time
import traceback
from datetime import datetime, timedelta

import numpy as np

from src.core.contexts import Status, Context
from src.core.interface import ControlService, OCRService, ODService, ImgService, WindowService
from src.core.pages import Page, Position, TextMatch, ConditionalAction
from src.service.page_event_service import PageEventAbstractService
from src.util import hwnd_util, keymouse_util

logger = logging.getLogger(__name__)


class AutoBossServiceImpl(PageEventAbstractService):
    """自动刷boss"""

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__(context, window_service, img_service, ocr_service, control_service, od_service)
        self._img_service.set_capture_mode(ImgService.CaptureEnum.BG)

        self._boss_pages: list[Page] = []
        self._general_pages: list[Page] = []
        self._dreamless_pages: list[Page] = []

        self._common_pages: list[Page] = []
        self._login_pages: list[Page] = []
        self._dead_pages: list[Page] = []
        self._transfer_pages: list[Page] = []
        self._daily_activity_pages: list[Page] = []

        self._build_boss_pages()
        self._build_general_pages()
        self._build_dreamless_pages()
        # 合并通用页面和boss页面
        self._boss_pages_all = self._general_pages + self._boss_pages + self._dreamless_pages

        self._conditional_actions: list[ConditionalAction] = []
        self._build_conditional_actions()

    def get_pages(self) -> list[Page]:
        return self._boss_pages_all

    def get_conditional_actions(self) -> list[ConditionalAction]:
        return self._conditional_actions

    def _build_boss_pages(self):

        # def unconscious_action(positions: dict[str, Position]) -> bool:
        #     """
        #     失去意识
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     position = positions.get("复苏")
        #     self._control_service.click(*position.center)
        #     return True
        #
        # unconscious_action_page = Page(
        #     name="失去意识",
        #     targetTexts=[
        #         TextMatch(
        #             name="失去意识",
        #             text="失去意识",
        #         ),
        #         TextMatch(
        #             name="复苏",
        #             text="复苏",
        #         ),
        #     ],
        #     action=unconscious_action,
        # )
        unconscious_action_page = self.build_Fight_Unconscious()
        self._boss_pages.append(unconscious_action_page)

        # def voice_string_interaction_action(positions: dict[str, Position]) -> bool:
        #     self._control_service.pick_up()
        #     return True
        #
        # voice_string_interaction_page = Page(
        #     name="声弦交互",
        #     targetTexts=[
        #         TextMatch(
        #             name="声弦",
        #             text="^声弦$",
        #         ),
        #     ],
        #     action=voice_string_interaction_action,
        # )
        voice_string_interaction_page = self.build_Boss_Crownless_ResonanceCord()
        self._boss_pages.append(voice_string_interaction_page)

    def _build_general_pages(self):

        # 游戏更新完成后，通过点击退出按钮来重新启动游戏。
        def update_game_exit(positions: dict[str, Position]) -> bool:
            """
            更新完成，请重新启动游戏。
            :param positions: 位置信息
            :return:
            """
            position = positions["退出"]
            self._control_service.click(*position.center)
            time.sleep(2)
            return True

        update_game_exit_page = Page(
            name="更新完成，请重新启动游戏",
            targetTexts=[
                TextMatch(
                    name="更新完成，请重新启动游戏",
                    text="更新完成，请重新启动游戏",
                ),
                TextMatch(
                    name="退出",
                    text="^退出$",
                ),
            ],
            action=update_game_exit,
        )
        self._general_pages.append(update_game_exit_page)

        # def driver_version_is_too_old_action(positions: dict[str, Position]) -> bool:
        #     """
        #     更新完成，请重新启动游戏。
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     position = positions["确认"]
        #     self._control_service.click(*position.center)
        #     time.sleep(2)
        #     return True
        #
        # driver_version_is_too_old_page = Page(
        #     name="检测到设备显卡驱动版本过旧",
        #     targetTexts=[
        #         TextMatch(
        #             name="显卡驱动版本过旧",
        #             text="显卡驱动版本过旧",
        #         ),
        #         TextMatch(
        #             name="确认",
        #             text="^确认$",
        #         ),
        #     ],
        #     action=driver_version_is_too_old_action,
        # )
        driver_version_is_too_old_page = self.build_Confirm_DriverVersion()
        self._general_pages.append(driver_version_is_too_old_page)

        # # 吸收声骸
        # def absorption_action(positions: dict[str, Position]) -> bool:
        #     """
        #     吸收声骸
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     time.sleep(2)
        #     if not self._ocr_service.find_text(["吸收"]):
        #         return False
        #     # dump_img()
        #
        #     self._info.absorptionCount += 1
        #     self._control_service.pick_up()
        #     time.sleep(2)
        #     self._info.needAbsorption = False
        #     if self._config.CharacterHeal and not self._info.isCheckedHeal:
        #         self._check_heal()
        #     return True

        # absorption_page = Page(
        #     name="吸收",
        #     targetTexts=[
        #         TextMatch(
        #             name="吸收",
        #             text="吸收",
        #         ),
        #     ],
        #     excludeTexts=[
        #         TextMatch(
        #             name="领取奖励",
        #             text="领取奖励",
        #         ),
        #     ],
        #     action=absorption_action,
        # )
        absorption_page = self.build_Fight_Absorption()
        self._general_pages.append(absorption_page)

        # def fight_success_action(positions: dict[str, Position]) -> bool:
        #     time.sleep(1)
        #     self._control_service.forward_run(2)
        #     time.sleep(0.5)
        #     return True
        #
        # fight_success_page = Page(
        #     name="挑战成功",
        #     targetTexts=[
        #         TextMatch(
        #             name="挑战成功",
        #             text="^挑战成功$",
        #         ),
        #     ],
        #     action=fight_success_action,
        # )
        #
        # fight_success_page = self.build_Fight_ChallengeSuccess()
        # self._general_pages.append(fight_success_page)

        # # 选择复苏物品
        # def select_recovery_items(positions: dict[str, Position]) -> bool:
        #     """
        #     取消选择复苏物品
        #     :param positions:
        #     :return:
        #     """
        #     self._info.needHeal = True
        #     logger.info("队伍中有角色需要复苏")
        #     self._control_service.esc()
        #     return True

        # select_recovery_items_page = Page(
        #     name="选择复苏物品",
        #     targetTexts=[
        #         TextMatch(
        #             name="选择复苏物品",
        #             text="选择复苏物品",
        #         ),
        #     ],
        #     action=select_recovery_items,
        # )
        select_recovery_items_page = self.build_Fight_select_recovery_items()
        self._general_pages.append(select_recovery_items_page)

        # 退出副本
        def exit_instance(positions: dict[str, Position]) -> bool:
            """
            退出副本
            :param positions:
            :return:
            """
            result = self._ocr_service.find_text("重新挑战")
            if result is not None and self._need_retry():
                logger.debug("点击重新挑战: %s", result)
                self.click_position(result)
                return True
            position = positions.get("退出副本", None)
            if position is None:
                return False
            logger.debug("点击退出副本: %s", position)
            self._control_service.click(*position.center)
            return True

        exit_instance_page = Page(
            name="退出副本",
            targetTexts=[
                TextMatch(
                    name="退出副本",
                    text="退出副本",
                ),
            ],
            action=exit_instance,
        )

        self._general_pages.append(exit_instance_page)

        # # 终端
        # def terminal_action(positions: dict[str, Position]) -> bool:
        #     """
        #     终端
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.esc()
        #     time.sleep(2)
        #     return True
        #
        # terminal_page = Page(
        #     name="终端",
        #     targetTexts=[
        #         TextMatch(
        #             name="终端",
        #             text="^终端$",
        #         ),
        #         TextMatch(
        #             name="生日",
        #             text="^生日$",
        #         ),
        #     ],
        #     action=terminal_action,
        # )
        terminal_page = self.build_UI_ESC_Terminal()

        self._general_pages.append(terminal_page)

        # # 击败 战斗状态
        # def fight_action(positions: dict[str, Position]) -> bool:
        #     """
        #     击败 战斗状态
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     if self._info.status != Status.fight:
        #         self._info.fightCount += 1
        #         self._info.needAbsorption = True
        #         self._info.fightTime = datetime.now()
        #     self.release_skills()
        #     self._info.status = Status.fight
        #     self._info.lastFightTime = datetime.now()
        #     return True

        # fight_page = Page(
        #     name="战斗画面",
        #     targetTexts=[
        #         TextMatch(
        #             name="战斗",
        #             text=r"(击败|对战|泰缇斯系统|凶戾之齿|倦怠之翼|妒恨之眼|(无餍?之舌)|(僭?越之矛)|(谵?妄之爪)|爱欲之容|盖希诺姆)",
        #         ),
        #     ],
        #     action=fight_action,
        # )
        fight_page = self.build_Fight()

        self._general_pages.append(fight_page)

        # # 点击领取今日月卡奖励
        # def click_receive_monthly_card_rewards(positions: dict[str, Position]) -> bool:
        #     """
        #     点击领取今日月卡奖励
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     position = positions.get("点击领取今日月相")
        #     time.sleep(0.5)
        #     self._control_service.click(*position.center)
        #     time.sleep(0.5)
        #     self._control_service.click(*position.center)
        #     return True
        #
        # receive_monthly_card_rewards_page = Page(
        #     name="每日月卡奖励",
        #     targetTexts=[
        #         TextMatch(
        #             name="点击领取今日月相",
        #             text="点击领取今日月相",
        #         ),
        #     ],
        #     action=click_receive_monthly_card_rewards,
        # )
        _Reward_LuniteSubscriptionReward = self.build_Reward_LuniteSubscriptionReward()
        self._general_pages.append(_Reward_LuniteSubscriptionReward)

        # # 补充结晶波片
        # def supplement_crystal_wave(positions: dict[str, Position]) -> bool:
        #     """
        #     补充结晶波片
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.esc()  # 退出
        #     time.sleep(2)
        #     return True
        #
        # supplement_crystal_wave_page = Page(
        #     name="补充结晶波片",
        #     targetTexts=[
        #         TextMatch(
        #             name="补充结晶波片",
        #             text="补充结晶波片",
        #         ),
        #     ],
        #     action=supplement_crystal_wave,
        # )
        supplement_crystal_wave_page = self.build_Replenish_Waveplate()
        self._general_pages.append(supplement_crystal_wave_page)

        # # 领取奖励
        # def receive_rewards(positions: dict[str, Position]) -> bool:
        #     """
        #     领取奖励
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.esc()  # 退出
        #     time.sleep(1)
        #     self._control_service.esc()
        #     return True
        #
        # receive_rewards_page = Page(
        #     name="领取奖励",
        #     targetTexts=[
        #         TextMatch(
        #             name="领取奖励",
        #             text="^领取奖励$",
        #         ),
        #         TextMatch(
        #             name="确认",
        #             text="^确认$",
        #         ),
        #         TextMatch(
        #             name="取消",
        #             text="^取消$",
        #         ),
        #     ],
        #     action=receive_rewards,
        # )
        receive_rewards_page = self.build_receive_rewards()
        self._general_pages.append(receive_rewards_page)

        # absorption_and_receive_rewards_page = Page(
        #     name="吸收和领取奖励重合",
        #     targetTexts=[
        #         TextMatch(
        #             name="领取奖励",
        #             text="领取奖励",
        #         ),
        #         TextMatch(
        #             name="吸收",
        #             text="吸收",
        #         ),
        #     ],
        #     action=absorption_and_receive_rewards,
        # )
        # # TODO 这个页面没绑定
        # self._general_pages.append(absorption_and_receive_rewards_page)

        # def blank_area(positions: dict[str, Position]) -> bool:
        #     """
        #     空白区域
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.activate()
        #     # TODO
        #     # self._control_service.click(480 * width_ratio, 540 * height_ratio)
        #     self._control_service.click(480, 540)
        #     time.sleep(1)
        #     self._control_service.esc()  # 退出
        #     time.sleep(1)
        #     return True
        #
        # blank_area_page = Page(
        #     name="空白区域",
        #     targetTexts=[
        #         TextMatch(
        #             name="空白区域",
        #             text="空白区域",
        #         ),
        #     ],
        #     action=blank_area,
        # )
        blank_area_page = self.build_blank_area()
        self._general_pages.append(blank_area_page)

        def login_action(positions: dict[str, Position]) -> bool:
            position = positions.get("点击连接")
            self._control_service.click(*position.center)
            time.sleep(0.5)
            return True

        login_page = Page(
            name="点击连接",
            targetTexts=[
                TextMatch(
                    name="点击连接",
                    text="点击连接",
                ),
            ],
            action=login_action,
        )
        self._general_pages.append(login_page)

        def confirm_page_action(positions: dict[str, Position]) -> bool:
            """
            点击确认
            :param positions: 位置信息
            :return:
            """
            position = positions["确认"]
            self._control_service.click(*position.center)
            time.sleep(2)
            return True

        disconnected_page = Page(
            name="连接已断开",
            targetTexts=[
                TextMatch(
                    name="连接已断开",
                    text="连接已断开",
                ),
                TextMatch(
                    name="登录超时，请重新尝试",
                    text="登录超时",
                ),
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
            ],
            action=confirm_page_action,
        )
        self._general_pages.append(disconnected_page)

        network_timeout_page = Page(
            name="系统提示",
            targetTexts=[
                TextMatch(
                    name="系统提示",
                    text="系统提示",
                ),
                TextMatch(
                    name="网络请求超时，无法连接服务器，请稍后再尝试",
                    text="网络请求超时",
                ),
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
            ],
            action=confirm_page_action,
        )
        self._general_pages.append(network_timeout_page)

        def account_login_action(positions: dict[str, Position]) -> bool:
            def click_login_page(ck_login_hwnd):
                # TODO 登录
                # try:
                #     ocr_text_result = find_text_in_login_hwnd("^登录$", ck_login_hwnd)
                #     if ocr_text_result is None:
                #         return False
                #     # 文本相对于登录框的位置
                #     # logger.info(f"position: {ocr_text_result}")
                #     click_position_in_login_hwnd(
                #         ocr_text_result, specified_hwnd=ck_login_hwnd
                #     )
                # except Exception as e:
                #     pass
                # time.sleep(3)
                return True

            # 手机号登录窗口特殊，是遮盖在游戏上方的另一个窗口句柄，费老半天才搞明白 by wakening
            # 调用游戏窗口截图会截取到登录窗口下层的游戏窗口，点击也是点不到上层
            # 先试官服
            login_hwnd_list = hwnd_util.get_login_hwnd_official()
            if login_hwnd_list is not None and len(login_hwnd_list) > 0:
                for login_hwnd in login_hwnd_list:
                    if click_login_page(login_hwnd):
                        logger.info("官服点击登录")
                        return True

            # 再试b服
            login_hwnd = hwnd_util.get_login_hwnd_bilibili()
            if click_login_page(login_hwnd):
                logger.info("b服点击登录")
                return True

            logger.debug("未找到登录页面")
            time.sleep(5)
            return False

        # 游戏掉线等原因出现的登录窗口，覆盖在游戏窗口之上，
        # 点击登录后才会出现点击连接，以此区分
        account_login_page = Page(
            name="账户登录",
            targetTexts=[
                TextMatch(
                    name="退出",
                    text="退出",
                ),
                TextMatch(
                    name="登入",
                    text="登入",
                ),
            ],
            excludeTexts=[
                TextMatch(
                    name="点击连接",
                    text="点击连接",
                ),
            ],
            action=account_login_action,
        )
        self._general_pages.append(account_login_page)

    def _build_dreamless_pages(self):
        # # 进入
        # def enter_action_dreamless(positions: dict[str, Position]) -> bool:
        #     """
        #     进入
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.pick_up()
        #     self._info.in_dungeon = True
        #     self._info.lastBossName = "无妄者"
        #     return True

        # enter_page_dreamless = Page(
        #     name="无冠者之像·心脏",
        #     targetTexts=[
        #         TextMatch(
        #             name="无冠者之像",
        #             text="无冠者之像",
        #         ),
        #         TextMatch(
        #             name="心脏",
        #             text="心脏",
        #         ),
        #         TextMatch(
        #             name="进入",
        #             text="进入",
        #         ),
        #     ],
        #     excludeTexts=[
        #         TextMatch(
        #             name="确认",
        #             text="^确认$",
        #         ),
        #         TextMatch(
        #             name="快速旅行",
        #             text="快速旅行",
        #         ),
        #     ],
        #     action=enter_action_dreamless,
        # )
        enter_page_dreamless = self.build_Boss_Dreamless_Enter()
        self._dreamless_pages.append(enter_page_dreamless)

        # # 进入
        # def enter_action_jue(positions: dict[str, Position]) -> bool:
        #     """
        #     进入
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.pick_up()
        #     self._info.in_dungeon = True
        #     self._info.lastBossName = "角"
        #     return True

        # enter_page_jue = Page(
        #     name="时序之寰",
        #     targetTexts=[
        #         TextMatch(
        #             name="时序之寰",
        #             text="进入时序之",
        #         ),
        #     ],
        #     excludeTexts=[
        #         TextMatch(
        #             name="确认",
        #             text="^确认$",
        #         ),
        #     ],
        #     action=enter_action_jue,
        # )
        enter_page_jue = self.build_Boss_Jue_Enter()
        self._dreamless_pages.append(enter_page_jue)

        # def enter_action_hecate(positions: dict[str, Position]) -> bool:
        #     """
        #     进入
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.pick_up()
        #     self._info.in_dungeon = True
        #     self._info.lastBossName = "赫卡忒"
        #     return True

        # enter_page_hecate = Page(
        #     name="声之领域",
        #     targetTexts=[
        #         TextMatch(
        #             name="声之领域",
        #             text="进入声之领域",
        #         ),
        #     ],
        #     excludeTexts=[
        #         TextMatch(
        #             name="确认",
        #             text="^确认$",
        #         ),
        #     ],
        #     action=enter_action_hecate,
        # )
        enter_page_hecate = self.build_Boss_Hecate_Enter()
        self._dreamless_pages.append(enter_page_hecate)

        # # 推荐等级
        # def recommended_level_action(positions: dict[str, Position]) -> bool:
        #     """
        #     推荐等级
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.pick_up()
        #     if self._info.DungeonWeeklyBossLevel != 0:
        #         dungeon_weekly_boss_level = self._info.DungeonWeeklyBossLevel  # 如果已有自动搜索结果，那么直接使用自动搜索的结果值
        #     elif (
        #             self._config.DungeonWeeklyBossLevel is None
        #             or self._config.DungeonWeeklyBossLevel < 40
        #             or self._config.DungeonWeeklyBossLevel % 10 != 0):
        #         dungeon_weekly_boss_level = 40  # 如果没有自动搜索的结果，且没有Config值或为值异常，则从40开始判断
        #     else:
        #         dungeon_weekly_boss_level = self._config.DungeonWeeklyBossLevel  # 如果没有自动搜索的结果，但有Config值且不为默认值，则使用Config值
        #     result = self._ocr_service.wait_text("推荐等级" + str(dungeon_weekly_boss_level))
        #     if not result:
        #         for i in range(1, 5):
        #             self._control_service.esc()
        #             result = self._ocr_service.wait_text("推荐等级" + str(dungeon_weekly_boss_level + (10 * i)))
        #             if result:
        #                 self._info.DungeonWeeklyBossLevel = dungeon_weekly_boss_level + (10 * i)
        #                 break
        #     if not result:
        #         self._control_service.esc()
        #         return False
        #     for i in range(2):
        #         self.click_position(result)
        #         time.sleep(0.5)
        #     result = self._ocr_service.find_text("单人挑战")
        #     if not result:
        #         self._control_service.esc()
        #         return False
        #     logger.info(f"最低推荐等级为{dungeon_weekly_boss_level}级")
        #     self.click_position(result)
        #     self._info.waitBoss = True
        #     self._info.lastFightTime = datetime.now()
        #     time.sleep(1)
        #
        # recommended_level_page = Page(
        #     name="推荐等级",
        #     targetTexts=[
        #         TextMatch(
        #             name="推荐等级",
        #             text="推荐等级",
        #         ),
        #     ],
        #     action=recommended_level_action,
        # )
        recommended_level_page = self.build_Boss_RecommendedLevel()
        self._dreamless_pages.append(recommended_level_page)

        # # 开启挑战
        # def start_challenge_action(positions: dict[str, Position]) -> bool:
        #     """
        #     开启挑战
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     position = positions["开启挑战"]
        #     self._control_service.click(*position.center)
        #     time.sleep(0.5)
        #     self._info.lastFightTime = datetime.now()
        #     return True
        #
        # start_challenge_page = Page(
        #     name="开启挑战",
        #     targetTexts=[
        #         TextMatch(
        #             name="开启挑战",
        #             text="开启挑战",
        #         ),
        #     ],
        #     action=start_challenge_action,
        # )
        start_challenge_page = self.build_UI_Boss_StartChallenge()
        self._dreamless_pages.append(start_challenge_page)

        # 确认离开
        # def confirm_leave_action(positions: dict[str, Position]) -> bool:
        #     """
        #     确认离开
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     self._control_service.activate()
        #     time.sleep(0.2)
        #     if self._need_retry() and not self._info.needHeal:
        #         self.click_position(positions["重新挑战"])
        #         if not self._info.lastBossName:
        #             self._info.lastBossName = self._config.TargetBoss[0]
        #         logger.info(f"重新挑战{self._info.lastBossName}副本")
        #         time.sleep(4)
        #         self._info.in_dungeon = True
        #         self._info.status = Status.idle
        #         now = datetime.now()
        #         self._info.lastFightTime = now
        #         self._info.fightTime = now
        #         self._info.waitBoss = True
        #     else:
        #         pos = positions.get("确认", positions.get("退出副本"))
        #         self.click_position(pos)
        #         time.sleep(3)
        #         self.wait_home()
        #         logger.info(f"{self._info.lastBossName}副本结束")
        #         time.sleep(2)
        #         self._info.in_dungeon = False
        #         self._info.status = Status.idle
        #         now = datetime.now()
        #         self._info.lastFightTime = now + timedelta(seconds=self._config.MaxFightTime / 2)
        #     self._info.isCheckedHeal = False
        #     return True

        # confirm_leave_page = Page(
        #     name="确认离开",
        #     targetTexts=[
        #         TextMatch(
        #             name="确认离开",
        #             text="确认离开",
        #         ),
        #         TextMatch(
        #             name="确认",
        #             text="^确认$",
        #         ),
        #         TextMatch(
        #             name="重新挑战",
        #             text="^重新挑战$",
        #         ),
        #     ],
        #     action=confirm_leave_action,
        # )
        confirm_leave_page = self.build_UI_ESC_LeaveInstance()
        self._dreamless_pages.append(confirm_leave_page)

        # # 结晶波片不足
        # def crystal_wave_action(positions: dict[str, Position]) -> bool:
        #     """
        #     结晶波片不足
        #     :param positions: 位置信息
        #     :return:
        #     """
        #     position = positions["确认"]
        #     self._control_service.click(*position.center)
        #     time.sleep(2)
        #     return True
        #
        # crystal_wave_page = Page(
        #     name="结晶波片不足",
        #     targetTexts=[
        #         TextMatch(
        #             name="结晶波片不足",
        #             text="结晶波片不足",
        #         ),
        #         TextMatch(
        #             name="确认",
        #             text="^确认$",
        #         ),
        #     ],
        #     action=crystal_wave_action,
        # )
        crystal_wave_page = self.build_Waveplate_NotEnough()
        self._dreamless_pages.append(crystal_wave_page)

    def _build_conditional_actions(self):

        def judgment_absorption_action():
            if self._config.SearchEchoes:
                self.absorption_action()
            else:
                self._control_service.up(0.1)
            if self._config.CharacterHeal and not self._info.isCheckedHeal:
                self._check_heal()
            return True

        # 战斗完成 等待搜索声骸 吸收
        def judgment_absorption() -> bool:
            time.sleep(0.1)
            return (
                    self._info.needAbsorption  # 未吸收
                    # 空闲时间未超过最大空闲时间 且 空闲时间超过最大空闲时间的一半
                    and self._config.MaxIdleTime / 2 < (
                            datetime.now() - self._info.lastFightTime).seconds < self._config.MaxIdleTime

            )

        judgment_absorption_condition_action = ConditionalAction(
            name="搜索声骸", condition=judgment_absorption, action=judgment_absorption_action
        )
        self._conditional_actions.append(judgment_absorption_condition_action)

        # 超过最大空闲时间
        def judgment_idle() -> bool:
            time.sleep(0.1)
            return (
                    not self._info.in_dungeon and
                    (datetime.now() - self._info.lastFightTime).seconds > self._config.MaxIdleTime
            )

        def judgment_idle_action() -> bool:
            self._info.status = Status.idle
            return self.transfer()

        judgment_idle_conditional_action = ConditionalAction(
            name="超过最大空闲时间,前往boss",
            condition=judgment_idle,
            action=judgment_idle_action,
        )
        self._conditional_actions.append(judgment_idle_conditional_action)

        # 超过最大战斗时间 大世界boss，非独立场景boss（无妄者）
        def judgment_fight() -> bool:
            time.sleep(0.1)
            return (
                    not self._info.in_dungeon and
                    (datetime.now() - self._info.fightTime).seconds > self._config.MaxFightTime
            )

        def judgment_fight_action() -> bool:
            self._info.status = Status.idle
            self._info.fightTime = datetime.now()
            return self.transfer()

        judgment_fight_conditional_action = ConditionalAction(
            name="超过最大战斗时间,前往boss",
            condition=judgment_fight,
            action=judgment_fight_action,
        )

        self._conditional_actions.append(judgment_fight_conditional_action)

        def judgment_leave() -> bool:
            time.sleep(0.1)
            return (
                    self._info.in_dungeon and
                    (datetime.now() - self._info.lastFightTime).seconds > self._config.MaxIdleTime
            )

        def judgment_leave_action() -> bool:
            # 重置最后战斗时间
            if self._info.needAbsorption:
                self.absorption_action()
            else:
                self.absorption_and_receive_rewards({})
            if self._config.CharacterHeal and not self._info.isCheckedHeal:
                self._check_heal()
            logger.debug("tap---------------esc--------------")
            self._control_service.esc()
            time.sleep(1)
            self._info.lastFightTime = datetime.now()
            return True

        judgment_leave_conditional_action = ConditionalAction(
            name="副本内超过最大空闲时间,离开",
            condition=judgment_leave,
            action=judgment_leave_action,
        )
        self._conditional_actions.append(judgment_leave_conditional_action)

    # def release_skills(self):
    #     # adapts()
    #     if self._info.waitBoss:
    #         self.boss_wait(self._info.lastBossName)
    #     # control.activate()
    #     self._control_service.activate()
    #     self.select_role(self._info.resetRole)
    #     # control.mouse_middle()
    #     self._control_service.camera_reset()
    #     if len(self._config.FightTactics) < self._info.roleIndex:
    #         # config.FightTactics.append("e,q,r,a,0.1,a,0.1,a,0.1,a,0.1,a,0.1")
    #         self._config.FightTactics.append("e,q,r,a(2)")
    #     tactics = self._config.FightTactics[self._info.roleIndex - 1].split(",")
    #     for tactic in tactics:  # 遍历对应角色的战斗策略
    #         try:
    #             try:
    #                 wait_time = float(tactic)  # 如果是数字，等待时间
    #                 time.sleep(wait_time)
    #                 continue
    #             except:
    #                 pass
    #             time.sleep(np.random.uniform(0, 0.02))  # 随机等待
    #             if len(tactic) == 1:  # 如果只有一个字符，且为普通攻击，进行连续0.3s的点击
    #                 if tactic == "a":
    #                     continuous_tap_time = 0.3
    #                     tap_start_time = time.time()
    #                     while time.time() - tap_start_time < continuous_tap_time:
    #                         # control.click()
    #                         # control.fight_click()
    #                         self._control_service.fight_click()
    #                 elif tactic == "s":
    #                     # control.space()
    #                     # control.fight_space()
    #                     # self._control_service.fight_tap(tactic)
    #                     pass
    #                 elif tactic == "l":
    #                     # control.dodge()  # 闪避
    #                     self._control_service.dash_dodge()
    #                 elif tactic == "r":  # 大招时判断是否释放
    #                     # control.fight_tap(tactic)
    #                     self._control_service.fight_tap(tactic)
    #                     time.sleep(0.2)
    #                 else:
    #                     # control.fight_tap(tactic)
    #                     self._control_service.fight_tap(tactic)
    #             elif len(tactic) >= 2 and tactic[1] == "~":  # 如果没有指定时间，默认0.5秒
    #                 click_time = 0.5 if len(tactic) == 2 else float(tactic.split("~")[1])
    #                 if tactic[0] == "a":
    #                     self._control_service.fight_click(seconds=click_time)
    #                     # control.mouse_press()
    #                     # time.sleep(click_time)
    #                     # control.mouse_release()
    #                 else:
    #                     self._control_service.fight_tap(tactic[0], seconds=click_time)
    #                     # control.key_press(tactic[0])
    #                     # time.sleep(click_time)
    #                     # control.key_release(tactic[0])
    #             elif "(" in tactic and ")" in tactic:  # 以设置的连续按键时间进行连续按键，识别格式：key(float)
    #                 continuous_tap_time = float(tactic[tactic.find("(") + 1: tactic.find(")")])
    #                 try:
    #                     continuous_tap_time = float(continuous_tap_time)
    #                 except ValueError:
    #                     pass
    #                 tap_start_time = time.time()
    #                 while time.time() - tap_start_time < continuous_tap_time:
    #                     if tactic[0] == "a":
    #                         # control.fight_click()
    #                         self._control_service.fight_click()
    #                     elif tactic == "s":
    #                         # control.fight_space()
    #                         pass
    #                     elif tactic == "l":
    #                         # control.dodge()  # 闪避
    #                         pass
    #                     else:
    #                         # control.fight_tap(tactic)
    #                         self._control_service.fight_tap(tactic)
    #         except Exception as e:
    #             logger.warning(f"释放技能失败: {e}")
    #             continue
    #
    # def select_role(self, reset_role: bool = False):
    #     now = datetime.now()
    #     if (now - self._info.lastSelectRoleTime).seconds < self._config.SelectRoleInterval:
    #         return
    #     self._info.lastSelectRoleTime = now
    #     if reset_role:
    #         self._info.roleIndex = 1
    #         self._info.resetRole = False
    #     else:
    #         self._info.roleIndex += 1
    #         if self._info.roleIndex > 3:
    #             self._info.roleIndex = 1
    #     if len(self._config.FightOrder) == 1:
    #         self._config.FightOrder.append(2)
    #     if len(self._config.FightOrder) == 2:
    #         self._config.FightOrder.append(3)
    #     select_role_index = self._config.FightOrder[self._info.roleIndex - 1]
    #     # control.tap(str(select_role_index))
    #     self._control_service.toggle_team_member(select_role_index)
    #
    # def boss_wait(self, bossName):
    #     """
    #     根据boss名称判断是否需要等待boss起身
    #
    #     :param bossName: boss名称
    #     """
    #     self._info.resetRole = True
    #
    #     match bossName:
    #         case "鸣钟之龟":
    #             logger.debug("龟龟需要等待16秒开始战斗！")
    #             time.sleep(16)
    #         case "聚械机偶":
    #             logger.debug("聚械机偶需要等待7秒开始战斗！")
    #             time.sleep(7)
    #         case "无妄者":
    #             logger.debug(f"无妄者需要等待{self._config.BossWaitTime_Dreamless}秒开始战斗！")
    #             time.sleep(self._config.BossWaitTime_Dreamless)
    #         case "角":
    #             logger.debug(f"角需要等待{self._config.BossWaitTime_Jue}秒开始战斗！")
    #             time.sleep(self._config.BossWaitTime_Jue)
    #         case "无归的谬误":
    #             logger.debug(f"无归的谬误需要等待{self._config.BossWaitTime_fallacy}秒开始战斗！")
    #             time.sleep(self._config.BossWaitTime_fallacy)
    #         case "异构武装":
    #             logger.debug(f"异构武装需要等待{self._config.BossWaitTime_sentry_construct}秒开始战斗！")
    #             time.sleep(self._config.BossWaitTime_sentry_construct)
    #         case "梦魇朔雷之鳞":
    #             # control.dodge()
    #             pass
    #         case "赫卡忒":
    #             time.sleep(0.3)
    #             self._control_service.forward_run(2.1)
    #         case _:
    #             pass
    #
    #     self._info.waitBoss = False
    #
    # def absorption_action(self):
    #     self._info.needAbsorption = False
    #     time.sleep(2)
    #     # 是否在副本中
    #     if self.absorption_and_receive_rewards({}):
    #         # if self._info.in_dungeon:
    #         #     self._control_service.esc()
    #         #     time.sleep(1)
    #         return
    #     start_time = datetime.now()  # 开始时间
    #     # 最大吸收时间为最大空闲时间的一半与设定MaxSearchEchoesTime取较大值
    #     if self._config.MaxIdleTime / 2 > self._config.MaxSearchEchoesTime:
    #         absorption_max_time = self._config.MaxIdleTime / 2
    #     else:
    #         absorption_max_time = self._config.MaxSearchEchoesTime
    #
    #     if absorption_max_time <= 10 and self._info.in_dungeon:
    #         absorption_max_time = 20
    #
    #     last_echo_box = None
    #     stop_search = False
    #     self._control_service.activate()
    #     self._control_service.camera_reset()
    #     time.sleep(0.5)
    #     while not stop_search and (datetime.now() - start_time).seconds < absorption_max_time:  # 未超过最大吸收时间
    #
    #         # time.sleep(0.2)
    #         echo_box = None
    #
    #         # 转动视角搜索声骸
    #         max_range = 5
    #         for i in range(max_range):
    #             img = self._img_service.screenshot()
    #             absorb = self._ocr_service.find_text("^吸收$", img)
    #             if absorb and self.absorption_and_receive_rewards({}):
    #                 stop_search = True
    #                 time.sleep(0.2)
    #                 break
    #             echo_box = self._od_service.search_echo(img)
    #             if echo_box is None:
    #                 logger.debug("未发现声骸")
    #                 self._control_service.left(0.1)
    #                 time.sleep(0.2)
    #                 self._control_service.camera_reset()
    #                 time.sleep(0.8)
    #                 if i == max_range - 1:
    #                     # 可能掉在正前方被人物挡住，前进一下再最后看一次
    #                     for _ in range(5):
    #                         self._control_service.up(0.08)
    #                         time.sleep(0.08)
    #                     for _ in range(3):
    #                         self._control_service.left(0.08)
    #                     time.sleep(0.1)
    #                     img = self._img_service.screenshot()
    #                     echo_box = self._od_service.search_echo(img)
    #                     if echo_box is not None:
    #                         break
    #                     stop_search = True
    #                     break
    #                 # else:
    #                 #     time.sleep(0.2)
    #                 #     continue
    #             else:
    #                 # logger.debug("发现声骸")
    #                 break
    #         if stop_search:
    #             break
    #         if echo_box is None:
    #             if last_echo_box is None:
    #                 continue
    #             else:
    #                 # 避免前往目标点过程中被遮挡等导致目标丢失
    #                 echo_box = last_echo_box
    #         else:
    #             last_echo_box = echo_box
    #
    #         # 前往声骸
    #         window_width = self._window_service.get_client_wh()[0]
    #         # role_width = int(window_width * 50 / 1280)
    #         echo_x1, echo_y1, echo_width, echo_height = echo_box
    #         echo_x2 = echo_x1 + echo_width
    #         # echo_y2 = echo_y1 + echo_height
    #         half_window_width = window_width // 2
    #         # half_role_width = role_width // 2
    #
    #         # echo_search_config_mapping = {"角": (8, 4, 4, 7)}
    #
    #         if echo_x1 > half_window_width:  # 声骸中在角色右侧
    #             logger.info("发现声骸 向右移动")
    #             self._control_service.right(0.1)
    #             time.sleep(0.05)
    #         elif echo_x2 < half_window_width:  # 声骸中在角色左侧
    #             logger.info("发现声骸 向左移动")
    #             self._control_service.left(0.1)
    #             time.sleep(0.05)
    #         else:
    #             logger.info("发现声骸 向前移动")
    #             # self._control_service.up(0.1)
    #             # time.sleep(0.01)
    #             for _ in range(5):
    #                 self._control_service.up(0.1)
    #                 time.sleep(0.05)
    #         # time.sleep(0.05)
    #         # if self.absorption_and_receive_rewards({}):
    #         #     time.sleep(0.2)
    #         #     break
    #     # if self._info.in_dungeon:
    #     #     self._control_service.esc()
    #     #     time.sleep(1)
    #
    # def transfer(self) -> bool:
    #     self._info.isCheckedHeal = False
    #     if self._config.CharacterHeal and self._info.needHeal:  # 检查是否需要治疗
    #         logger.info("有角色阵亡，开始治疗")
    #         time.sleep(1)
    #         self._info.lastBossName = "治疗"
    #         self._transfer_to_heal()
    #
    #     bossName = self._config.TargetBoss[self._info.bossIndex % len(self._config.TargetBoss)]
    #
    #     self._control_service.activate()
    #     time.sleep(0.2)
    #     self._control_service.guide_book()
    #     time.sleep(1)
    #     if not self._ocr_service.wait_text(["日志", "活跃", "挑战", "强者", "残象", "周期", "探寻", "漂泊"], timeout=7):
    #         logger.warning("未进入索拉指南")
    #         self._control_service.esc()
    #         self._info.lastFightTime = datetime.now()
    #         return False
    #     time.sleep(1)
    #     self._info.bossIndex += 1
    #     return self.transfer_to_boss(bossName)
    #
    # def _transfer_to_heal(self):
    #     # control.activate()
    #     # control.tap("m")
    #     self._control_service.activate()
    #     self._control_service.map()
    #     time.sleep(2)
    #     toggle_map = self._ocr_service.find_text("切换地图")
    #     if not toggle_map:
    #         # control.esc()
    #         self._control_service.esc()
    #         logger.info("未找到切换地图")
    #         return False
    #     try:
    #         # tmp_x = int((toggle_map.x1 + toggle_map.x2) // 2)
    #         # tmp_y = int((toggle_map.y1 + toggle_map.y2) // 2)
    #         # random_click(tmp_x, tmp_y, ratio=False)
    #         self.click_position(toggle_map)
    #         huanglong_text = self._ocr_service.wait_text("瑝?珑")
    #         self.click_position(huanglong_text)
    #         time.sleep(0.5)
    #         self.click_position(huanglong_text)
    #         time.sleep(1.5)
    #         if jzc_text := self._ocr_service.wait_text("今州城"):
    #             self.click_position(jzc_text)
    #             time.sleep(0.5)
    #             self.click_position(jzc_text)
    #             time.sleep(1.5)
    #             jzcj_text = self._ocr_service.wait_text("今州城界")
    #             tmp_x = jzcj_text.x1 - 5
    #             tmp_y = jzcj_text.y1 - 40
    #             # random_click(tmp_x, tmp_y, ratio=False)
    #             self._control_service.click(tmp_x, tmp_y)
    #             time.sleep(2)
    #             if transfer := self._ocr_service.wait_text("快速旅行"):
    #                 self.click_position(transfer)
    #                 time.sleep(0.1)
    #                 self.click_position(transfer)
    #                 logger.info("治疗_等待传送完成")
    #                 time.sleep(3)
    #                 self.wait_home()  # 等待回到主界面
    #                 logger.info("治疗_传送完成")
    #                 now = datetime.now()
    #                 self._info.idleTime = now  # 重置空闲时间
    #                 self._info.lastFightTime = now  # 重置最近检测到战斗时间
    #                 self._info.fightTime = now  # 重置战斗时间
    #                 self._info.needHeal = False
    #                 self._info.healCount += 1
    #                 return True
    #     except Exception:
    #         error_message = traceback.format_exc()
    #         logger.error(f"前往复活点过程中出现异常: {error_message}")
    #         self._control_service.activate()
    #         for i in range(3):
    #             time.sleep(2.5)
    #             toggle_map = self._ocr_service.find_text("切换地图")
    #             if toggle_map:
    #                 self._control_service.esc()
    #                 continue
    #             else:
    #                 break
    #     return False
    #
    # def absorption_and_receive_rewards2(self, positions: dict[str, Position]) -> bool:
    #     if self._ocr_service.find_text("吸收"):
    #         logger.info("模拟吸收声骸")
    #         return True
    #     return False
    #
    # def absorption_and_receive_rewards(self, positions: dict[str, Position]) -> bool:
    #     """
    #     吸收和领取奖励重合
    #     :param positions: 位置信息
    #     :return:
    #     """
    #     self._control_service.activate()
    #     count = 0
    #     absorb_try_more = 0
    #     while True:
    #         if not self._ocr_service.find_text("吸收"):
    #             if absorb_try_more > 0:
    #                 break
    #             else:
    #                 # 多搜一次，有时吸收前突然蹦出个蓝雨蝶，导致误判误吸
    #                 absorb_try_more += 1
    #                 time.sleep(0.1)
    #                 continue
    #         if count % 2:
    #             logger.info("向下滚动后尝试吸收")
    #             keymouse_util.scroll_mouse(self._window_service.window, -1)
    #             time.sleep(1)
    #         count += 1
    #         self._control_service.pick_up()
    #         time.sleep(2)
    #         if self._ocr_service.find_text(["确认", "收取物资"]):
    #             logger.info("点击到领取奖励，关闭页面")
    #             self._control_service.esc()
    #             time.sleep(2)
    #     if count == 0:
    #         return False
    #     logger.info("吸收声骸")
    #     if self._info.fightCount is None or self._info.fightCount == 0:
    #         self._info.fightCount = 1
    #         self._info.absorptionCount = 1
    #     elif self._info.fightCount < self._info.absorptionCount:
    #         self._info.fightCount = self._info.absorptionCount
    #     else:
    #         self._info.absorptionCount += 1
    #     absorption_rate = self._info.absorptionCount / self._info.fightCount
    #     logger.info("目前声骸吸收率为：%s", str(format(absorption_rate * 100, ".2f")))
    #     return True
    #
    # def transfer_to_boss(self, bossName):
    #     # 传送后向前行走次数，适合短距离
    #     forward_walk_times_mapping = {"无妄者": 5, "角": 4, "赫卡忒": 4}
    #     # 传送后向前奔跑时间，秒，适合长距离
    #     forward_run_seconds_mapping = {
    #         "无归的谬误": 5.5, "辉萤军势": 3.6, "鸣钟之龟": 3.6, "燎照之骑": 4.2, "无常凶鹭": 4, "聚械机偶": 6.8,
    #         "哀声鸷": 4.8, "朔雷之鳞": 3.2, "云闪之鳞": 3, "飞廉之猩": 6, "无冠者": 3,
    #         "异构武装": 4, "罗蕾莱": 4.5, "叹息古龙": 5.6, "梦魇无常凶鹭": 5.3, "梦魇云闪之鳞": 4.8,
    #         "梦魇朔雷之鳞": 3.2,
    #         "梦魇无冠者": 2.4, "梦魇燎照之骑": 4.5, "梦魇哀声鸷": 3.6, "梦魇飞廉之猩": 1,
    #     }
    #     # position = self.find_pic(template_img_name="UI_F2_Guidebook_EchoHunting.png", threshold=0.5)
    #     position = self._img_service.match_template(img=None, template_img="UI_F2_Guidebook_EchoHunting.png", threshold=0.5)
    #     if not position:
    #         logger.info("识别残像探寻失败", "WARN")
    #         self._control_service.esc()
    #         return False
    #     self._control_service.click(*position.center)  # 进入残像探寻
    #     if not self._ocr_service.wait_text("探测"):
    #         logger.warning("未进入残象探寻")
    #         self._control_service.esc()
    #         return False
    #     logger.info(f"当前目标boss：{bossName}")
    #     # model_boss_yolo(bossName)
    #     boss_name_reg_mapping = {
    #         "哀声鸷": "哀声鸷?",
    #         "赫卡忒": "赫卡忒?",
    #         "梦魇飞廉之猩": "梦.*飞廉之猩",
    #         "梦魇无常凶鹭": "梦.*无常凶鹭",
    #         "梦魇云闪之鳞": "梦.*云闪之鳞",
    #         "梦魇朔雷之鳞": "梦.*朔雷之鳞",
    #         "梦魇无冠者": "梦.*无冠者",
    #         "梦魇燎照之骑": "梦.*燎照之骑",
    #         "梦魇哀声鸷": "梦.*哀声鸷?",
    #     }
    #     find_boss_name_reg = boss_name_reg_mapping.get(bossName, bossName)
    #     findBoss = None
    #     y = 133
    #     while y < 907:
    #         y = y + 34
    #         if y > 907:
    #             y = 907
    #         findBoss = self._ocr_service.find_text(find_boss_name_reg)
    #         if findBoss:
    #             break
    #         # control.click(855 * width_ratio, y * height_ratio)
    #         # random_click(855, y, 1, 3)
    #         self._control_service.click(855, y)
    #         time.sleep(0.3)
    #     if not findBoss:
    #         self._control_service.esc()
    #         logger.warning("未找到目标boss")
    #         return False
    #     self.click_position(findBoss)
    #     self.click_position(findBoss)
    #     time.sleep(1)
    #     detection_text = self._ocr_service.wait_text("^探测$", timeout=5)
    #     if not detection_text:
    #         self._control_service.esc()
    #         return False
    #     time.sleep(1)
    #     self.click_position(detection_text)
    #     time.sleep(2.5)
    #     if transfer := self._ocr_service.wait_text("^快速旅行$", timeout=5):
    #         time.sleep(0.5)
    #         self.click_position(transfer)
    #         logger.info("等待传送完成")
    #         time.sleep(1.5)
    #         self.wait_home()  # 等待回到主界面
    #         logger.info("传送完成")
    #         self._control_service.activate()
    #
    #         if bossName == "罗蕾莱":
    #             self.lorelei_clock_adjust()
    #
    #         # 走/跑向boss
    #         forward_walk_times = forward_walk_times_mapping.get(bossName, 0)
    #         forward_run_seconds = forward_run_seconds_mapping.get(bossName, 0)
    #         time.sleep(1.2)  # 等站稳了再动
    #         if forward_walk_times > 0:
    #             if bossName == "赫卡忒" and self._ocr_service.find_text("进入声之领域"):
    #                 pass
    #             else:
    #                 self._control_service.forward_walk(forward_walk_times)
    #         elif forward_run_seconds > 0:
    #             self._control_service.forward_run(forward_run_seconds)
    #
    #         if bossName == "无冠者":
    #             i = 0
    #             while i < 8 and not self._ocr_service.find_text("^声弦$"):
    #                 self._control_service.forward_walk(3)
    #                 i += 1
    #
    #         now = datetime.now()
    #         self._info.idleTime = now  # 重置空闲时间
    #         self._info.lastFightTime = now  # 重置最近检测到战斗时间
    #         self._info.fightTime = now  # 重置战斗时间
    #         self._info.lastBossName = bossName
    #         self._info.waitBoss = True
    #         return True
    #     else:
    #         logger.warning("未找到快速旅行, 可能未解锁boss传送")
    #     self._control_service.esc()
    #     return False
    #
    # def lorelei_clock_adjust(self):
    #     time.sleep(2)
    #     self._control_service.activate()
    #     find_sit_and_wait_text = self._ocr_service.find_text(["坐上椅子等待", "坐上椅子", "的到来"])
    #     if not find_sit_and_wait_text:
    #         return
    #     logger.info("罗蕾莱不在家，等她")
    #     self._control_service.esc()
    #     time.sleep(2)
    #     if not self._ocr_service.wait_text("^终端$", timeout=5):
    #         self._control_service.esc()
    #         return
    #     # random_click(1374, 1038)
    #     self._control_service.click(1374, 1038)
    #     time.sleep(2)
    #     tomorrow = self._ocr_service.wait_text("^次日$", timeout=5)
    #     if not tomorrow:
    #         logger.warning("未找到次日")
    #         self._control_service.esc()
    #         return
    #     self.click_position(tomorrow)
    #     time.sleep(1)
    #     confirm_text = self._ocr_service.find_text("确定")
    #     self.click_position(confirm_text)
    #     time.sleep(2)
    #     self._ocr_service.wait_text("时间", timeout=10)
    #     time.sleep(1)
    #     self._control_service.esc()
    #     self._ocr_service.wait_text("^终端$", timeout=5)
    #     time.sleep(1)
    #     self._control_service.esc()
    #     time.sleep(0.5)
    #
    # @property
    # def _info(self):
    #     return self._context.boss_task_ctx
    #
    # @property
    # def _config(self):
    #     return self._context.config.app
    #
    # def _check_heal(self):
    #     self._info.isCheckedHeal = True
    #     logger.debug("Current roleIndex: %s", self._info.roleIndex)
    #     for i in range(3):
    #         role_index = (self._info.roleIndex + i) % 3
    #         # logger.debug("role_index: %s", role_index)
    #         self._control_service.toggle_team_member(role_index + 1)
    #         time.sleep(0.5)
    #     position = Position.build(325, 190, 690, 330)
    #     if self._ocr_service.wait_text("复苏", timeout=2, position=position):
    #         logger.debug("检测到角色需要复苏")
    #         self._info.needHeal = True
    #         self._control_service.esc()
    #         time.sleep(1.2)
    #
    # def click_position(self, position: Position):
    #     self._control_service.click(*position.center)
    #
    # def _need_retry(self):
    #     return len(self._config.TargetBoss) == 1 and self._config.TargetBoss[0] in ["无妄者", "角", "赫卡忒"]
    #
    # def wait_home(self, timeout=120) -> bool:
    #     """
    #     等待回到主界面
    #     :param timeout:  超时时间
    #     :return:
    #     """
    #     start = datetime.now()
    #     time.sleep(0.1)
    #     # i = 0
    #     while True:
    #         # i += 1
    #         # logger(f"i={i}", "DEBUG")
    #         self._control_service.activate()
    #         # 修复部分情况下导致无法退出该循环的问题。
    #         if (datetime.now() - start).seconds > timeout:
    #             self._window_service.close_window()
    #             raise Exception("等待回到主界面超时")
    #         img = self._img_service.screenshot()
    #         if img is None:
    #             time.sleep(0.3)
    #             continue
    #
    #         # 获取右下角四分之一部分
    #         h, w = img.shape[:2]  # 获取高度和宽度
    #         cropped_img = img[h // 2:, w // 2:]  # 裁剪右下角
    #
    #         # is_ok = False
    #         results = self._ocr_service.ocr(cropped_img)
    #         text_result = self._ocr_service.search_text(results, "快速旅行")
    #         if text_result:
    #             text_result.confidence = text_result.confidence
    #             # logger.debug("Match text: Fast Travel, %s", text_result)
    #             time.sleep(0.3)
    #             continue
    #         text_result = self._ocr_service.search_text(results, "特征码|^特征.+\d{5,}")
    #         if text_result:
    #             text_result.confidence = text_result.confidence
    #             # logger.debug("Match text: UID, %s", text_result)
    #             return True
    #             # is_ok = True
    #         # else:
    #         #     logger.debug("No match for text: UID")
    #         # 图片检测
    #         pic_array = [
    #             ("Quests.png", 0.8),
    #             ("Backpack.png", 0.8),
    #             ("Guidebook.png", 0.8),
    #         ]
    #         for template_img, threshold in pic_array:
    #             position = self._img_service.match_template(img=img, template_img=template_img, threshold=threshold)
    #             if position:
    #                 # logger.debug(f"Match template: {pic_name}, {position}")
    #                 return True
    #                 # is_ok = True
    #             # else:
    #             #     logger.debug(f"No match for template: {pic_name}")
    #             time.sleep(0.01)
    #         # if is_ok:
    #         #     return is_ok
    #         time.sleep(0.3)
