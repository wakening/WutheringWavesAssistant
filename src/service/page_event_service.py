import logging
import time
import traceback
from abc import ABC
from datetime import datetime, timedelta
from typing import Callable

import numpy as np

from src.core.contexts import Context, Status
from src.core.interface import ControlService, OCRService, PageEventService, ImgService, WindowService, ODService
from src.core.languages import Languages
from src.core.pages import ConditionalAction, TextMatch, Page
from src.core.regions import TextPosition, DynamicPosition, Position
from src.util import keymouse_util

logger = logging.getLogger(__name__)


class PageEventAbstractService(PageEventService, ABC):
    """通过页面ocr所得文字匹配关键字触发相应事件，触发动作"""

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService):
        self._context: Context = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service
        self._ocr_service: OCRService = ocr_service
        self._control_service: ControlService = control_service
        self._od_service: ODService = od_service
        # page
        self._UI_F2_Guidebook_Activity = self.build_UI_F2_Guidebook_Activity()
        self._UI_F2_Guidebook_RecurringChallenges = self.build_UI_F2_Guidebook_RecurringChallenges()
        self._UI_F2_Guidebook_PathOfGrowth = self.build_UI_F2_Guidebook_PathOfGrowth()
        self._UI_F2_Guidebook_EchoHunting = self.build_UI_F2_Guidebook_EchoHunting()
        self._UI_F2_Guidebook_Milestones = self.build_UI_F2_Guidebook_Milestones()
        self._UI_ESC_Terminal = self.build_UI_ESC_Terminal()
        self._UI_ESC_LeaveInstance = self.build_UI_ESC_LeaveInstance()
        self._Reward_TapTheBlankAreaToClose = self.build_Reward_TapTheBlankAreaToClose()
        self._Reward_LuniteSubscriptionReward = self.build_Reward_LuniteSubscriptionReward()
        self._F_EnterForgeryChallenge = self.build_F_EnterForgeryChallenge()
        self._Challenge_EnterSoloChallenge = self.build_Challenge_EnterSoloChallenge()
        self._Reward_ClaimRewards_ForgeryChallenge = self.build_Reward_ClaimRewards_ForgeryChallenge()
        self._Reward_ClaimRewards_TacetSuppression = self.build_Reward_ClaimRewards_TacetSuppression()

    def execute(self,
                src_img: np.ndarray | None = None,
                img: np.ndarray | None = None,
                ocr_results: list[TextPosition] | None = None,
                pages: list[Page] | None = None,
                conditional_actions: list[ConditionalAction] | None = None):
        # prepare
        if pages is None:
            pages = self.get_pages()
        if conditional_actions is None:
            conditional_actions = self.get_conditional_actions()
        if not pages and not conditional_actions:
            raise ValueError("未配置匹配页面/条件操作")
        if src_img is None:
            src_img = self._img_service.screenshot()
        if img is None:
            img = self._img_service.resize(src_img)
        if ocr_results is None:
            ocr_results = self._ocr_service.ocr(img)

        # action
        for page in pages:
            if not page.is_match(src_img, img, ocr_results):
                continue
            logger.info("当前页面：%s", page.name)
            page.action(page.matchPositions)
        for conditionalAction in conditional_actions:
            if not conditionalAction():
                continue
            logger.info("当前条件操作: %s", conditionalAction.name)
            conditionalAction.action()

    def build_UI_F2_Guidebook_Activity(self, action: Callable = None) -> Page:
        return Page(
            name="UI-F2-索拉指南-活跃度|Activity",
            screenshot={
                Languages.ZH: [
                    "UI_F2_Guidebook_Activity_001.png",
                    "UI_F2_Guidebook_Activity_002.png",
                    "UI_F2_Guidebook_Activity_003.png",
                    "UI_F2_Guidebook_Activity_004.png",
                ],
                Languages.EN: [
                    "UI_F2_Guidebook_Activity_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="活跃度|Activity",
                    text=r"^(活跃度|Activity)$",
                    position=DynamicPosition(
                        rate=(
                            0.0,
                            0.0,
                            320 / 1280,
                            90 / 720,
                        ),
                    ),
                ),
                TextMatch(
                    name="刷新时间|Reset time",
                    text=r"(.*小时.*分钟后刷新|Resets\s*after\s*\d{1,2}h\s*\d{1,2}m)$",
                ),
                TextMatch(
                    name="领取|Claim",
                    text=r"^(领取|Claim)$",
                    must=False,
                    position=DynamicPosition(
                        rate=(
                            920 / 1280,
                            0.0,
                            1.0,
                            1.0,
                        ),
                    ),
                ),
            ],
            action=action if action else Page.error_action
        )


    def build_UI_F2_Guidebook_RecurringChallenges(self, action: Callable = None) -> Page:
        return Page(
            name="UI-F2-索拉指南-周期挑战|RecurringChallenges",
            screenshot={
                Languages.ZH: [
                    "UI_F2_Guidebook_RecurringChallenges_001.png",
                ],
                Languages.EN: [
                    "UI_F2_Guidebook_RecurringChallenges_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="周期挑战|Recurring Challenges",
                    text=r"^(周期挑战|Recurring\s*Challenges)$",
                    position=DynamicPosition(
                        rate=(
                            0.0,
                            0.0,
                            320 / 1280,
                            90 / 720,
                        ),
                    ),
                ),
                TextMatch(
                    name="凝素领域|Forgery Challenge",
                    text=r"^(凝素领域|Forgery\s*Challenge)$",
                ),
                TextMatch(
                    name="模拟领域|Simulation Challenge",
                    text=r"^(模拟领域|Simulation\s*Challenge)$",
                ),
                TextMatch(
                    name="讨伐强敌|Boss Challenge",
                    text=r"^(讨伐强敌|Boss\s*Challenge)$",
                ),
                TextMatch(
                    name="无音清剿|Tacet Suppression",
                    text=r"^(无音清剿|Tacet\s*Suppression)$",
                ),
                TextMatch(
                    name="战歌重奏|Weekly Challenge",
                    text=r"^(战歌重奏|Weekly\s*Challenge)$",
                ),
                # TextMatch(
                #     name="逆境深塔",
                #     text=r"^逆境深塔$",
                #     must=False,
                # ),
                # TextMatch(
                #     name="冥歌海墟",
                #     text=r"^冥歌海墟$",
                #     must=False,
                # ),
                TextMatch(
                    name="今日剩余双倍奖励次数|Double Drop Chances Remaining",
                    text=r"今日剩余双倍奖励次数|Double\s*Drop\s*Chances\s*Remaining",
                    must=False,
                ),
                TextMatch(
                    name="体力值|waveplate",
                    text=r"\d{1,3}/\d{3}",
                    must=False,
                    position=DynamicPosition(
                        rate=(
                            1 / 2,
                            0.0,
                            1.0,
                            120 / 720,
                        ),
                    ),
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_UI_F2_Guidebook_PathOfGrowth(self, action: Callable = None) -> Page:
        return Page(
            name="UI-F2-索拉指南-强者之路|PathOfGrowth",
            screenshot={
                Languages.ZH: [
                    "UI_F2_Guidebook_PathOfGrowth_001.png",
                ],
                Languages.EN: [
                ],
            },
            targetTexts=[
                TextMatch(
                    name="强者之路|PathOfGrowth",
                    text=r"^强者之路",
                    position=DynamicPosition(
                        rate=(
                            0.0,
                            0.0,
                            180 / 1280,
                            90 / 720,
                        ),
                    ),
                ),
                TextMatch(
                    name="全息战略",
                    text=r"^全息战略$",
                ),
                TextMatch(
                    name="角色教学",
                    text=r"^角色教学$",
                ),
                TextMatch(
                    name="基础训练",
                    text=r"^基础训练$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_UI_F2_Guidebook_EchoHunting(self, action: Callable = None) -> Page:
        return Page(
            name="UI-F2-索拉指南-残象探寻|EchoHunting",
            screenshot={
                Languages.ZH: [
                    "UI_F2_Guidebook_EchoHunting_001.png",
                ],
                Languages.EN: [
                ],
            },
            targetTexts=[
                TextMatch(
                    name="残象探寻|EchoHunting",
                    text=r"^残象探寻$",
                    position=DynamicPosition(
                        rate=(
                            0.0,
                            0.0,
                            180 / 1280,
                            90 / 720,
                        ),
                    ),
                ),
                TextMatch(
                    name="鸣钟之龟",
                    text=r"^鸣钟之龟$",
                ),
                TextMatch(
                    name="伤痕",
                    text=r"^伤痕$",
                ),
                TextMatch(
                    name="无妄者",
                    text=r"^无妄者$",
                ),
                TextMatch(
                    name="探测",
                    text=r"^探测$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_UI_F2_Guidebook_Milestones(self, action: Callable = None) -> Page:
        return Page(
            name="UI-F2-索拉指南-漂泊日志|Milestones",
            screenshot={
                Languages.ZH: [
                    "UI_F2_Guidebook_Milestones_001.png",
                ],
                Languages.EN: [
                ],
            },
            targetTexts=[
                TextMatch(
                    name="漂泊日志|Milestones",
                    text=r"^(漂泊日志|Milestones)$",
                    position=DynamicPosition(
                        rate=(
                            0.0,
                            0.0,
                            180 / 1280,
                            90 / 720,
                        ),
                    ),
                ),
                TextMatch(
                    name="任务进度",
                    text=r"^任务进度$",
                    position=DynamicPosition(
                        rate=(
                            1 / 2,
                            0.0,
                            1.0,
                            1.0,
                        ),
                    ),
                ),
                TextMatch(
                    name="阶段奖励",
                    text=r"^阶段奖励$",
                    position=DynamicPosition(
                        rate=(
                            1 / 2,
                            0.0,
                            1.0,
                            1.0,
                        ),
                    ),
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_UI_ESC_Terminal(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.esc()
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="UI-终端|Terminal",
            screenshot={
                Languages.ZH: [
                    "UI_ESC_Terminal_001.png",
                ],
                Languages.EN: [
                    "UI_ESC_Terminal_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="终端|Terminal",
                    text=r"^(终端|Terminal)$",
                    position=DynamicPosition(
                        rate=(
                            0.0,
                            0.0,
                            280 / 1280,
                            90 / 720,
                        ),
                    ),
                ),
                TextMatch(
                    name="生日|Birthday",
                    text=r"^(生日|Birthday)$",
                ),
                TextMatch(
                    name="活动|Events",
                    text=r"^(活动|Events)$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Reward_TapTheBlankAreaToClose(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = positions.get("点击空白区域关闭|Tap the blank area to close")
                self._control_service.click(*position.center)
                time.sleep(1)
                return True

            action = default_action

        return Page(
            name="奖励|Reward-TapTheBlankAreaToClose",
            screenshot={
                Languages.ZH: [
                    "Reward_LuniteSubscriptionReward_001.png"
                ],
                Languages.EN: [
                    "UI_F2_Guidebook_Activity_Reward_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="获得|Items Obtained",
                    text=r"^(获得|Items\s*Obtained)$",
                ),
                TextMatch(
                    name="点击空白区域关闭|Tap the blank area to close",
                    text=r"^(点击空白区域关闭|Tap\s*the\s*blank\s*area\s*to\s*close)$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_UI_ESC_LeaveInstance(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.activate()
                time.sleep(0.2)
                if self._need_retry() and not self._info.needHeal:
                    self.click_position(positions["重新挑战|Restart"])
                    if not self._info.lastBossName:
                        self._info.lastBossName = self._config.TargetBoss[0]
                    logger.info(f"重新挑战{self._info.lastBossName}副本")
                    time.sleep(4)
                    self._info.in_dungeon = True
                    self._info.status = Status.idle
                    now = datetime.now()
                    self._info.lastFightTime = now
                    self._info.fightTime = now
                    self._info.waitBoss = True
                else:
                    pos = positions.get("确认|Confirm")
                    self.click_position(pos)
                    time.sleep(3)
                    self.wait_home()
                    logger.info(f"{self._info.lastBossName}副本结束")
                    time.sleep(2)
                    self._info.in_dungeon = False
                    self._info.status = Status.idle
                    now = datetime.now()
                    self._info.lastFightTime = now + timedelta(seconds=self._config.MaxFightTime / 2)
                self._info.isCheckedHeal = False
                return True

            action = default_action

        return Page(
            name="UI-离开副本|LeaveInstance",
            screenshot={
                Languages.ZH: [
                    # "UI_ESC_LeaveInstance_001.png",
                ],
                Languages.EN: [
                    "UI_ESC_LeaveInstance_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="提示|Note",
                    text=r"^(提示|Note)$",
                ),
                TextMatch(
                    name="确认|Confirm",
                    text=r"^(确认|Confirm)$",
                ),
                TextMatch(
                    name="重新挑战|Restart",
                    text=r"^(重新挑战|Restart)$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_F_EnterForgeryChallenge(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.pick_up()
                time.sleep(5)
                return True

            action = default_action

        return Page(
            name="F-进入凝素领域|EnterForgeryChallenge",
            screenshot={
                Languages.ZH: [
                    "F_EnterForgeryChallenge_001.png"
                ],
                Languages.EN: [
                    "F_EnterForgeryChallenge_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="进入凝素领域|EnterForgeryChallenge",
                    text=r"^(进入.{0,2}凝素领域.{0,2}|Enter\s*the.{0,2}ForgeryChallenge.{0,2})$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Challenge_EnterSoloChallenge(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = positions.get("单人挑战|Solo Challenge")
                self._control_service.click(*position.center)
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="F-进入凝素领域|EnterForgeryChallenge",
            screenshot={
                Languages.ZH: [
                    "F_EnterForgeryChallenge_001.png"
                ],
                Languages.EN: [
                    "F_EnterForgeryChallenge_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="单人挑战|Solo Challenge",
                    text=r"^(单人挑战|Solo\s*Challenge)$",
                ),
                TextMatch(
                    name="多人匹配|Match",
                    text=r"^(多人匹配|Match)$",
                ),
                TextMatch(
                    name="等级|Level",
                    text=r"^(等级\d{2}|Match\d{2})$",
                ),
                # TextMatch(
                #     name="欲燃之森|Marigold Woods",
                #     text=r"^(欲燃之森|Marigold\s*Woods)$",
                # ),
            ],
            action=action if action else Page.error_action
        )

    def build_Reward_ClaimRewards_ForgeryChallenge(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                # TODO
                # position = positions.get("确认|Confirm")
                # self._control_service.click(*position.center)
                self._control_service.esc()
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="Reward-领取奖励|ClaimRewards-凝素领域|ForgeryChallenge",
            screenshot={
                Languages.ZH: [
                    "Reward_ClaimRewards_001.png"
                    "Reward_ClaimRewards_002.png"
                ],
                Languages.EN: [
                    "Reward_ClaimRewards_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="领取奖励|Claim Rewards",
                    text=r"^(领取奖励|Claim\s*Rewards)$",
                ),
                TextMatch(
                    name="取消|Cancel",
                    text=r"^(取消|Cancel)$",
                ),
                TextMatch(
                    name="确认|Confirm",
                    text=r"^(确认|Confirm)$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Reward_ClaimRewards_TacetSuppression(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                # TODO
                # position = positions.get("单倍领取|Claim")
                # self._control_service.click(*position.center)
                self._control_service.esc()
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="Reward-领取奖励|ClaimRewards-无音清剿|TacetSuppression",
            screenshot={
                Languages.ZH: [
                    "Reward_ClaimRewards_001.png"
                    "Reward_ClaimRewards_002.png"
                ],
                Languages.EN: [
                    "Reward_ClaimRewards_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="领取奖励|Claim Rewards",
                    text=r"^(领取奖励|Claim\s*Rewards)$",
                ),
                TextMatch(
                    name="单倍领取|Claim",
                    text=r"^(单倍领取|Claim)$",
                ),
                TextMatch(
                    name="双倍领取|Claimx2",
                    text=r"^(双倍领取|Claim.?2)$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Fight_Unconscious(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = positions.get("复苏")
                self._control_service.click(*position.center)
                return True

            action = default_action

        return Page(
            name="失去意识",
            screenshot={
                Languages.ZH: [
                    "",
                ],
                Languages.EN: [
                    "",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="失去意识",
                    text="失去意识",
                ),
                TextMatch(
                    name="复苏",
                    text="复苏",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Boss_Crownless_ResonanceCord(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.pick_up()
                return True

            action = default_action

        return Page(
            name="声弦|Resonance Cord",
            targetTexts=[
                TextMatch(
                    name="声弦|Resonance Cord",
                    text=r"^(声弦|Resonance Cord)$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Confirm_DriverVersion(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = positions["确认"]
                self._control_service.click(*position.center)
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="检测到设备显卡驱动版本过旧",
            targetTexts=[
                TextMatch(
                    name="显卡驱动版本过旧",
                    text="显卡驱动版本过旧",
                ),
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Fight_Absorption(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                time.sleep(2)
                if not self._ocr_service.find_text(["吸收"]):
                    return False
                # dump_img()

                self._info.absorptionCount += 1
                self._control_service.pick_up()
                time.sleep(2)
                self._info.needAbsorption = False
                if self._config.CharacterHeal and not self._info.isCheckedHeal:
                    self._check_heal()
                return True

            action = default_action

        return Page(
            name="吸收",
            targetTexts=[
                TextMatch(
                    name="吸收",
                    text="吸收",
                ),
            ],
            excludeTexts=[
                TextMatch(
                    name="领取奖励",
                    text="领取奖励",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Fight_ChallengeSuccess(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                time.sleep(1)
                self._control_service.forward_run(2)
                time.sleep(0.5)
                return True

            action = default_action

        return Page(
            name="挑战成功",
            targetTexts=[
                TextMatch(
                    name="挑战成功",
                    text="^挑战成功$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Fight_select_recovery_items(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._info.needHeal = True
                logger.info("队伍中有角色需要复苏")
                self._control_service.esc()
                return True

            action = default_action

        return Page(
            name="选择复苏物品",
            targetTexts=[
                TextMatch(
                    name="选择复苏物品",
                    text="选择复苏物品",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Fight(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                if self._info.status != Status.fight:
                    self._info.fightCount += 1
                    self._info.needAbsorption = True
                    self._info.fightTime = datetime.now()
                self.release_skills()
                self._info.status = Status.fight
                self._info.lastFightTime = datetime.now()
                return True

            action = default_action

        return Page(
            name="战斗画面",
            targetTexts=[
                TextMatch(
                    name="战斗",
                    text=r"(击败|对战|泰缇斯系统|凶戾之齿|倦怠之翼|妒恨之眼|(无餍?之舌)|(僭?越之矛)|(谵?妄之爪)|爱欲之容|盖希诺姆)",
                ),
            ],
            excludeTexts=[
                TextMatch(
                    name="活跃度",
                    text="^活跃度$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Reward_LuniteSubscriptionReward(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = positions.get("点击领取今日月相观测卡奖励|claim today's Lunite Subscription reward")
                time.sleep(0.2)
                self._control_service.click(*position.center)
                time.sleep(1)
                self._control_service.click(*position.center)
                time.sleep(0.2)
                return True

            action = default_action

        return Page(
            name="每日月卡奖励|Lunite Subscription reward",
            targetTexts=[
                TextMatch(
                    name="点击领取今日月相观测卡奖励|claim today's Lunite Subscription reward",
                    text=r"(点击领取今日月相|Lunite\s*Subscription\s*reward)",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Replenish_Waveplate(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.esc()
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="补充结晶波片",
            targetTexts=[
                TextMatch(
                    name="补充结晶波片",
                    text="补充结晶波片",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_receive_rewards(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.esc()
                time.sleep(1)
                self._control_service.esc()
                return True

            action = default_action

        return Page(
            name="领取奖励",
            targetTexts=[
                TextMatch(
                    name="领取奖励",
                    text="^领取奖励$",
                ),
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
                TextMatch(
                    name="取消",
                    text="^取消$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_blank_area(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = TextPosition.get(positions, "空白区域")
                self._control_service.click(*position.center)
                time.sleep(1)
                self._control_service.esc()
                time.sleep(1)
                return True

            action = default_action

        return Page(
            name="空白区域",
            targetTexts=[
                TextMatch(
                    name="空白区域",
                    text="空白区域",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Boss_Dreamless_Enter(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.pick_up()
                self._info.in_dungeon = True
                self._info.lastBossName = "无妄者"
                return True

            action = default_action

        return Page(
            name="无冠者之像·心脏",
            targetTexts=[
                TextMatch(
                    name="无冠者之像",
                    text="无冠者之像",
                ),
                TextMatch(
                    name="心脏",
                    text="心脏",
                ),
                TextMatch(
                    name="进入",
                    text="进入",
                ),
            ],
            excludeTexts=[
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
                TextMatch(
                    name="快速旅行",
                    text="快速旅行",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Boss_Jue_Enter(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.pick_up()
                self._info.in_dungeon = True
                self._info.lastBossName = "角"
                return True

            action = default_action

        return Page(
            name="时序之寰",
            targetTexts=[
                TextMatch(
                    name="时序之寰",
                    text="进入时序之",
                ),
            ],
            excludeTexts=[
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Boss_Hecate_Enter(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.pick_up()
                self._info.in_dungeon = True
                self._info.lastBossName = "赫卡忒"
                return True

            action = default_action

        return Page(
            name="声之领域",
            targetTexts=[
                TextMatch(
                    name="声之领域",
                    text="进入声之领域",
                ),
            ],
            excludeTexts=[
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Boss_RecommendedLevel(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.pick_up()
                if self._info.DungeonWeeklyBossLevel != 0:
                    dungeon_weekly_boss_level = self._info.DungeonWeeklyBossLevel  # 如果已有自动搜索结果，那么直接使用自动搜索的结果值
                elif (self._config.DungeonWeeklyBossLevel is None
                      or self._config.DungeonWeeklyBossLevel < 40
                      or self._config.DungeonWeeklyBossLevel % 10 != 0):
                    dungeon_weekly_boss_level = 40  # 如果没有自动搜索的结果，且没有Config值或为值异常，则从40开始判断
                else:
                    dungeon_weekly_boss_level = self._config.DungeonWeeklyBossLevel  # 如果没有自动搜索的结果，但有Config值且不为默认值，则使用Config值
                result = self._ocr_service.wait_text("推荐等级" + str(dungeon_weekly_boss_level))
                if not result:
                    for i in range(1, 5):
                        self._control_service.esc()
                        result = self._ocr_service.wait_text("推荐等级" + str(dungeon_weekly_boss_level + (10 * i)))
                        if result:
                            self._info.DungeonWeeklyBossLevel = dungeon_weekly_boss_level + (10 * i)
                            break
                if not result:
                    self._control_service.esc()
                    return False
                for i in range(2):
                    self._control_service.click(*result.center)
                    time.sleep(0.5)
                result = self._ocr_service.find_text("单人挑战")
                if not result:
                    self._control_service.esc()
                    return False
                logger.info(f"最低推荐等级为{dungeon_weekly_boss_level}级")
                self._control_service.click(*result.center)
                self._info.waitBoss = True
                self._info.lastFightTime = datetime.now()
                time.sleep(1)
                return True

            action = default_action

        return Page(
            name="推荐等级",
            targetTexts=[
                TextMatch(
                    name="推荐等级",
                    text="推荐等级",
                ),
                TextMatch(
                    name="单人挑战",
                    text="单人挑战",
                ),
                TextMatch(
                    name="结晶波片",
                    text="结晶波片",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_UI_Boss_StartChallenge(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = positions.get("开启挑战|StartChallenge")
                self._control_service.click(*position.center)
                time.sleep(0.5)
                _info = self._context.boss_task_ctx
                _info.lastFightTime = datetime.now()
                return True

            action = default_action

        return Page(
            name="开启挑战|StartChallenge",  # 副本选完刷取等级后，点击单人挑战后弹出的队伍选择页面
            screenshot={
                Languages.ZH: [
                    "",
                ],
                Languages.EN: [
                    "UI_Boss_StartChallenge_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="快速编队|QuickSetup",
                    text=r"^(快速编队|QuickSetup)$",
                ),
                TextMatch(
                    name="开启挑战|StartChallenge",
                    text=r"^(开启挑战|StartChallenge)$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Waveplate_NotEnough(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = positions["确认"]
                self._control_service.click(*position.center)
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="结晶波片不足",
            targetTexts=[
                TextMatch(
                    name="结晶波片不足",
                    text="结晶波片不足",
                ),
                TextMatch(
                    name="确认",
                    text="^确认$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def release_skills(self):
        # adapts()
        if self._info.waitBoss:
            self.boss_wait(self._info.lastBossName)
        self._control_service.activate()
        role_is_change = self.select_role(self._info.resetRole)
        self._control_service.camera_reset()
        if len(self._config.FightTactics) < self._info.roleIndex:
            # config.FightTactics.append("e,q,r,a,0.1,a,0.1,a,0.1,a,0.1,a,0.1")
            self._config.FightTactics.append("e,q,r,a(2)")
        # if role_is_change:
        tactics = self._config.FightTactics[self._info.roleIndex - 1].split(",")
        # else:
        #     tactics = ["a"]
        for tactic in tactics:  # 遍历对应角色的战斗策略
            try:
                try:
                    wait_time = float(tactic)  # 如果是数字，等待时间
                    time.sleep(wait_time)
                    continue
                except Exception:
                    pass
                time.sleep(np.random.uniform(0, 0.02))  # 随机等待
                if len(tactic) == 1:  # 如果只有一个字符，且为普通攻击，进行连续0.3s的点击
                    if tactic == "a":  # 默认普通0.3秒
                        continuous_tap_time = 0.3
                        tap_start_time = time.time()
                        while time.time() - tap_start_time < continuous_tap_time:
                            self._control_service.fight_click()
                            time.sleep(0.05)
                    elif tactic == "s":
                        self._control_service.fight_tap("SPACE")
                    elif tactic == "l":  # 闪避
                        self._control_service.dash_dodge()
                    elif tactic == "r":
                        self._control_service.fight_tap(tactic)
                        time.sleep(0.2)
                    # elif tactic == "e":
                    #     self._control_service.fight_tap(tactic)
                    #     time.sleep(0.1)
                    else:
                        self._control_service.fight_tap(tactic)
                        # time.sleep(0.05)
                elif len(tactic) >= 2 and tactic[1] == "~":  # 如果没有指定时间，默认0.5秒
                    click_time = 0.5 if len(tactic) == 2 else float(tactic.split("~")[1])
                    if tactic[0] == "a":
                        self._control_service.fight_click(seconds=click_time)
                    else:
                        self._control_service.fight_tap(tactic[0], seconds=click_time)
                elif "(" in tactic and ")" in tactic:  # 以设置的连续按键时间进行连续按键，识别格式：key(float)
                    continuous_tap_time = float(tactic[tactic.find("(") + 1: tactic.find(")")])
                    try:
                        continuous_tap_time = float(continuous_tap_time)
                    except ValueError:
                        pass
                    tap_start_time = time.time()
                    while time.time() - tap_start_time < continuous_tap_time:
                        if tactic[0] == "a":
                            self._control_service.fight_click(seconds=0.02)
                        elif tactic == "s":
                            self._control_service.fight_tap("SPACE")
                        elif tactic == "l":  # 闪避
                            self._control_service.dash_dodge()
                        else:
                            self._control_service.fight_tap(tactic)
            except Exception as e:
                logger.warning(f"释放技能失败: {e}")
                continue

    def select_role(self, reset_role: bool = False) -> bool:
        now = datetime.now()
        if (now - self._info.lastSelectRoleTime).seconds < self._config.SelectRoleInterval:
            return False
        self._info.lastSelectRoleTime = now
        if reset_role:
            self._info.roleIndex = 1
            self._info.resetRole = False
        else:
            self._info.roleIndex += 1
            if self._info.roleIndex > 3:
                self._info.roleIndex = 1
        if len(self._config.FightOrder) == 1:
            self._config.FightOrder.append(2)
        if len(self._config.FightOrder) == 2:
            self._config.FightOrder.append(3)
        select_role_index = self._config.FightOrder[self._info.roleIndex - 1]
        self._control_service.toggle_team_member(select_role_index)
        return True

    def boss_wait(self, bossName):
        """
        根据boss名称判断是否需要等待boss起身

        :param bossName: boss名称
        """
        self._info.resetRole = True

        match bossName:
            case "鸣钟之龟":
                logger.debug("龟龟需要等待16秒开始战斗！")
                time.sleep(16)
            case "聚械机偶":
                logger.debug("聚械机偶需要等待7秒开始战斗！")
                time.sleep(7)
            case "无妄者":
                logger.debug(f"无妄者需要等待{self._config.BossWaitTime_Dreamless}秒开始战斗！")
                time.sleep(self._config.BossWaitTime_Dreamless)
            case "角":
                logger.debug(f"角需要等待{self._config.BossWaitTime_Jue}秒开始战斗！")
                time.sleep(self._config.BossWaitTime_Jue)
            case "无归的谬误":
                logger.debug(f"无归的谬误需要等待{self._config.BossWaitTime_fallacy}秒开始战斗！")
                time.sleep(self._config.BossWaitTime_fallacy)
            case "异构武装":
                logger.debug(f"异构武装需要等待{self._config.BossWaitTime_sentry_construct}秒开始战斗！")
                time.sleep(self._config.BossWaitTime_sentry_construct)
            case "梦魇朔雷之鳞":
                # control.dodge()
                pass
            case "赫卡忒":
                time.sleep(0.3)
                self._control_service.forward_run(2.1)
            case _:
                pass

        self._info.waitBoss = False

    def absorption_action(self, search_type: str = "echo"):
        self._info.needAbsorption = False
        time.sleep(2)
        # 是否在副本中
        if self.absorption_and_receive_rewards({}):
            # if self._info.in_dungeon:
            #     self._control_service.esc()
            #     time.sleep(1)
            return
        start_time = datetime.now()  # 开始时间
        # 最大吸收时间为最大空闲时间的一半与设定MaxSearchEchoesTime取较大值
        if self._config.MaxIdleTime / 2 > self._config.MaxSearchEchoesTime:
            absorption_max_time = self._config.MaxIdleTime / 2
        else:
            absorption_max_time = self._config.MaxSearchEchoesTime

        if absorption_max_time <= 10 and self._info.in_dungeon:
            absorption_max_time = 20

        last_echo_box = None
        stop_search = False
        self._control_service.activate()
        self._control_service.camera_reset()
        time.sleep(0.5)

        search_region = DynamicPosition(
            rate=(
                788 / 1280,
                300 / 720,
                1100 / 1280,
                560 / 720,
            ),
        )

        while not stop_search and (datetime.now() - start_time).seconds < absorption_max_time:  # 未超过最大吸收时间

            # time.sleep(0.2)
            echo_box = None

            # 转动视角搜索声骸
            max_range = 5
            for i in range(max_range):
                img = self._img_service.screenshot()

                absorb = self._ocr_service.find_text("^吸收$", img, search_region)
                if absorb and self.absorption_and_receive_rewards({}):
                    stop_search = True
                    time.sleep(0.2)
                    break
                echo_box = self._od_service.search_echo(img)
                if echo_box is None:
                    logger.debug("未发现声骸")
                    self._control_service.left(0.1)
                    time.sleep(0.2)
                    self._control_service.camera_reset()
                    time.sleep(0.8)
                    if i == max_range - 1:
                        # 可能掉在正前方被人物挡住，前进一下再最后看一次
                        for _ in range(4):
                            self._control_service.up(0.1)
                            time.sleep(0.1)
                        for _ in range(2):
                            self._control_service.left(0.1)
                        time.sleep(0.3)
                        img = self._img_service.screenshot()
                        echo_box = self._od_service.search_echo(img)
                        if echo_box is not None:
                            break
                        stop_search = True
                        break
                    # else:
                    #     time.sleep(0.2)
                    #     continue
                else:
                    # logger.debug("发现声骸")
                    break
            if stop_search:
                break
            if echo_box is None:
                if last_echo_box is None:
                    continue
                else:
                    # 避免前往目标点过程中被遮挡等导致目标丢失
                    echo_box = last_echo_box
            else:
                last_echo_box = echo_box

            # 前往声骸
            window_width = self._window_service.get_client_wh()[0]
            # role_width = int(window_width * 50 / 1280)
            echo_x1, echo_y1, echo_width, echo_height = echo_box
            echo_x2 = echo_x1 + echo_width
            # echo_y2 = echo_y1 + echo_height
            half_window_width = window_width // 2
            # half_role_width = role_width // 2

            # echo_search_config_mapping = {"角": (8, 4, 4, 7)}

            if echo_x1 > half_window_width:  # 声骸中在角色右侧
                logger.info("发现声骸 向右移动")
                self._control_service.right(0.1)
                time.sleep(0.05)
            elif echo_x2 < half_window_width:  # 声骸中在角色左侧
                logger.info("发现声骸 向左移动")
                self._control_service.left(0.1)
                time.sleep(0.05)
            else:
                logger.info("发现声骸 向前移动")
                # self._control_service.up(0.1)
                # time.sleep(0.01)
                for _ in range(5):
                    self._control_service.up(0.1)
                    time.sleep(0.05)
                time.sleep(0.5)
            # time.sleep(0.05)
            # if self.absorption_and_receive_rewards({}):
            #     time.sleep(0.2)
            #     break
        # if self._info.in_dungeon:
        #     self._control_service.esc()
        #     time.sleep(1)

    def search_reward_action(self):

        position = DynamicPosition(
            rate=(
                1 / 2,
                0.0,
                1.0,
                1.0
            )
        )

        if self._ocr_service.find_text("领取奖励", position=position):
            self._control_service.pick_up()
            # logger.info("模拟领取奖励(实际未领取仅关闭小窗)")
            # logger.info("模拟领取奖励(实际未领取仅关闭小窗)")
            # logger.info("模拟领取奖励(实际未领取仅关闭小窗)")
            # time.sleep(5)
            # self._control_service.esc()
            # time.sleep(0.5)
            # TODO
            time.sleep(0.5)
            # src_img = self._img_service.screenshot()
            # img = self._img_service.resize(src_img)
            # ocr_results = self._ocr_service.ocr(img)
            # is_match = self._Reward_ClaimRewards_ForgeryChallenge.is_match(src_img, img, ocr_results)
            # logger.debug("is_match: %s", is_match)
            # position = self._Reward_ClaimRewards_ForgeryChallenge.matchPositions.get("确认|Confirm")
            # self._control_service.click(*position.center)
            # time.sleep(2)
            # position = self._ocr_service.wait_text("退出副本")
            # self._control_service.click(*position.center)
            # time.sleep(2)
            return True

        self._control_service.activate()
        self._control_service.camera_reset()
        time.sleep(0.5)
        start_time = datetime.now()
        last_od_box = None
        stop_search = False

        while not stop_search and (datetime.now() - start_time).seconds < 20:
            od_box = None
            # 转动视角搜索声骸
            max_range = 5
            for i in range(max_range):
                img = self._img_service.screenshot()

                if self._ocr_service.find_text("领取奖励", img=img, position=position):
                    self._control_service.pick_up()
                    # logger.info("模拟领取奖励(实际未领取仅关闭小窗)")
                    # logger.info("模拟领取奖励(实际未领取仅关闭小窗)")
                    # logger.info("模拟领取奖励(实际未领取仅关闭小窗)")
                    # time.sleep(5)
                    # self._control_service.esc()
                    # time.sleep(0.5)
                    # TODO
                    time.sleep(0.5)
                    # src_img = self._img_service.screenshot()
                    # img = self._img_service.resize(src_img)
                    # ocr_results = self._ocr_service.ocr(img)
                    # is_match = self._Reward_ClaimRewards_ForgeryChallenge.is_match(src_img, img, ocr_results)
                    # logger.debug("is_match: %s", is_match)
                    # position = self._Reward_ClaimRewards_ForgeryChallenge.matchPositions.get("确认|Confirm")
                    # self._control_service.click(*position.center)
                    # time.sleep(2)
                    # position = self._ocr_service.wait_text("退出副本")
                    # self._control_service.click(*position.center)
                    # time.sleep(2)
                    return True

                od_box = self._od_service.search_reward(img)
                if od_box is None:
                    logger.debug("未发现声骸")
                    self._control_service.left(0.1)
                    time.sleep(0.2)
                    self._control_service.camera_reset()
                    time.sleep(0.8)
                    if i == max_range - 1:
                        # 可能掉在正前方被人物挡住，前进一下再最后看一次
                        for _ in range(4):
                            self._control_service.up(0.1)
                            time.sleep(0.1)
                        for _ in range(2):
                            self._control_service.left(0.1)
                        time.sleep(0.3)
                        img = self._img_service.screenshot()
                        echo_box = self._od_service.search_echo(img)
                        if echo_box is not None:
                            break
                        stop_search = True
                        break
                    # else:
                    #     time.sleep(0.2)
                    #     continue
                else:
                    # logger.debug("发现声骸")
                    break
            if stop_search:
                break
            if od_box is None:
                if last_od_box is None:
                    continue
                else:
                    # 避免前往目标点过程中被遮挡等导致目标丢失
                    od_box = last_od_box
            else:
                last_od_box = od_box

            # 前往声骸
            window_width = self._window_service.get_client_wh()[0]
            # role_width = int(window_width * 50 / 1280)
            echo_x1, echo_y1, echo_width, echo_height = od_box
            echo_x2 = echo_x1 + echo_width
            # echo_y2 = echo_y1 + echo_height
            half_window_width = window_width // 2
            # half_role_width = role_width // 2

            # echo_search_config_mapping = {"角": (8, 4, 4, 7)}

            if echo_x1 > half_window_width:  # 声骸中在角色右侧
                logger.info("发现声骸 向右移动")
                self._control_service.right(0.1)
                time.sleep(0.05)
            elif echo_x2 < half_window_width:  # 声骸中在角色左侧
                logger.info("发现声骸 向左移动")
                self._control_service.left(0.1)
                time.sleep(0.05)
            else:
                logger.info("发现声骸 向前移动")
                for _ in range(5):
                    self._control_service.up(0.1)
                    time.sleep(0.05)
        return False

    def transfer(self) -> bool:
        self._info.isCheckedHeal = False
        if self._config.CharacterHeal and self._info.needHeal:  # 检查是否需要治疗
            logger.info("有角色阵亡，开始治疗")
            time.sleep(1)
            self._info.lastBossName = "治疗"
            self._transfer_to_heal()

        bossName = self._config.TargetBoss[self._info.bossIndex % len(self._config.TargetBoss)]

        self._control_service.activate()
        time.sleep(0.2)
        self._control_service.guide_book()
        time.sleep(1)
        if not self._ocr_service.wait_text(["日志", "活跃", "挑战", "强者", "残象", "周期", "探寻", "漂泊"], timeout=7):
            logger.warning("未进入索拉指南")
            self._control_service.esc()
            self._info.lastFightTime = datetime.now()
            return False
        time.sleep(1)
        self._info.bossIndex += 1
        return self.transfer_to_boss(bossName)

    def _transfer_to_heal(self):
        # control.activate()
        # control.tap("m")
        self._control_service.activate()
        self._control_service.map()
        time.sleep(2)
        toggle_map = self._ocr_service.find_text("切换地图")
        if not toggle_map:
            # control.esc()
            self._control_service.esc()
            logger.info("未找到切换地图")
            return False
        try:
            # tmp_x = int((toggle_map.x1 + toggle_map.x2) // 2)
            # tmp_y = int((toggle_map.y1 + toggle_map.y2) // 2)
            # random_click(tmp_x, tmp_y, ratio=False)
            self.click_position(toggle_map)
            huanglong_text = self._ocr_service.wait_text("瑝?珑")
            self.click_position(huanglong_text)
            time.sleep(0.5)
            self.click_position(huanglong_text)
            time.sleep(1.5)
            if jzc_text := self._ocr_service.wait_text("今州城"):
                self.click_position(jzc_text)
                time.sleep(0.5)
                self.click_position(jzc_text)
                time.sleep(1.5)
                jzcj_text = self._ocr_service.wait_text("今州城界")
                tmp_x = jzcj_text.x1 - 5
                tmp_y = jzcj_text.y1 - 40
                # random_click(tmp_x, tmp_y, ratio=False)
                self._control_service.click(tmp_x, tmp_y)
                time.sleep(2)
                if transfer := self._ocr_service.wait_text("快速旅行"):
                    self.click_position(transfer)
                    time.sleep(0.1)
                    self.click_position(transfer)
                    logger.info("治疗_等待传送完成")
                    time.sleep(3)
                    self.wait_home()  # 等待回到主界面
                    logger.info("治疗_传送完成")
                    now = datetime.now()
                    self._info.idleTime = now  # 重置空闲时间
                    self._info.lastFightTime = now  # 重置最近检测到战斗时间
                    self._info.fightTime = now  # 重置战斗时间
                    self._info.needHeal = False
                    self._info.healCount += 1
                    return True
        except Exception:
            error_message = traceback.format_exc()
            logger.error(f"前往复活点过程中出现异常: {error_message}")
            self._control_service.activate()
            for i in range(3):
                time.sleep(2.5)
                toggle_map = self._ocr_service.find_text("切换地图")
                if toggle_map:
                    self._control_service.esc()
                    continue
                else:
                    break
        return False

    def absorption_and_receive_rewards2(self, positions: dict[str, Position]) -> bool:
        if self._ocr_service.find_text("吸收"):
            logger.info("模拟吸收声骸")
            return True
        return False

    def absorption_and_receive_rewards(self, positions: dict[str, Position]) -> bool:
        """
        吸收和领取奖励重合
        :param positions: 位置信息
        :return:
        """
        self._control_service.activate()
        count = 0
        absorb_try_more = 0
        while True:
            if not self._ocr_service.find_text("吸收"):
                if absorb_try_more > 0:
                    break
                else:
                    # 多搜一次，有时吸收前突然蹦出个蓝羽蝶，导致误判误吸
                    absorb_try_more += 1
                    time.sleep(0.1)
                    continue
            if count % 2:
                logger.info("向下滚动后尝试吸收")
                keymouse_util.scroll_mouse(self._window_service.window, -1)
                time.sleep(1)
            count += 1
            self._control_service.pick_up()
            time.sleep(2)
            if self._ocr_service.find_text(["确认", "收取物资"]):
                logger.info("点击到领取奖励，关闭页面")
                self._control_service.esc()
                time.sleep(2)
        if count == 0:
            return False
        logger.info("吸收声骸")
        if self._info.fightCount is None or self._info.fightCount == 0:
            self._info.fightCount = 1
            self._info.absorptionCount = 1
        elif self._info.fightCount < self._info.absorptionCount:
            self._info.fightCount = self._info.absorptionCount
        else:
            self._info.absorptionCount += 1
        absorption_rate = self._info.absorptionCount / self._info.fightCount
        logger.info("目前声骸吸收率为：%s", str(format(absorption_rate * 100, ".2f")))
        return True

    def transfer_to_boss(self, bossName):
        # 传送后向前行走次数，适合短距离
        forward_walk_times_mapping = {"无妄者": 5, "角": 4, "赫卡忒": 4}
        # 传送后向前奔跑时间，秒，适合长距离
        forward_run_seconds_mapping = {
            "无归的谬误": 5.5, "辉萤军势": 3.6, "鸣钟之龟": 3.6, "燎照之骑": 4.2, "无常凶鹭": 4, "聚械机偶": 6.8,
            "哀声鸷": 4.8, "朔雷之鳞": 3.2, "云闪之鳞": 3, "飞廉之猩": 6, "无冠者": 3,
            "异构武装": 4, "罗蕾莱": 4.5, "叹息古龙": 5.6, "梦魇无常凶鹭": 5.3, "梦魇云闪之鳞": 4.8,
            "梦魇朔雷之鳞": 3.2,
            "梦魇无冠者": 2.4, "梦魇燎照之骑": 4.5, "梦魇哀声鸷": 3.6, "梦魇飞廉之猩": 1,
        }
        # position = self.find_pic(template_img_name="UI_F2_Guidebook_EchoHunting.png", threshold=0.5)
        position = self._img_service.match_template(img=None, template_img="UI_F2_Guidebook_EchoHunting.png",
                                                    threshold=0.5)
        if not position:
            logger.info("识别残像探寻失败", "WARN")
            self._control_service.esc()
            return False
        self._control_service.click(*position.center)  # 进入残像探寻
        if not self._ocr_service.wait_text("探测"):
            logger.warning("未进入残象探寻")
            self._control_service.esc()
            return False
        logger.info(f"当前目标boss：{bossName}")
        # model_boss_yolo(bossName)
        boss_name_reg_mapping = {
            "哀声鸷": "哀声鸷?",
            "赫卡忒": "赫卡忒?",
            "梦魇飞廉之猩": "梦.*飞廉之猩",
            "梦魇无常凶鹭": "梦.*无常凶鹭",
            "梦魇云闪之鳞": "梦.*云闪之鳞",
            "梦魇朔雷之鳞": "梦.*朔雷之鳞",
            "梦魇无冠者": "梦.*无冠者",
            "梦魇燎照之骑": "梦.*燎照之骑",
            "梦魇哀声鸷": "梦.*哀声鸷?",
        }
        find_boss_name_reg = boss_name_reg_mapping.get(bossName, bossName)
        findBoss = None
        y = 133
        while y < 700:
            y = y + 22
            if y > 700:
                y = 700
            findBoss = self._ocr_service.find_text(find_boss_name_reg)
            if findBoss:
                break
            # control.click(855 * width_ratio, y * height_ratio)
            # random_click(855, y, 1, 3)
            # self._control_service.click(855, y)
            self._control_service.click(570, y)
            time.sleep(0.5)
        if not findBoss:
            self._control_service.esc()
            logger.warning("未找到目标boss")
            return False
        self.click_position(findBoss)
        self.click_position(findBoss)
        time.sleep(1)
        detection_text = self._ocr_service.wait_text("^探测$", timeout=5)
        if not detection_text:
            self._control_service.esc()
            return False
        time.sleep(1)
        self.click_position(detection_text)
        time.sleep(2.5)
        if transfer := self._ocr_service.wait_text("^快速旅行$", timeout=5):
            time.sleep(0.5)
            self.click_position(transfer)
            logger.info("等待传送完成")
            time.sleep(1.5)
            self.wait_home()  # 等待回到主界面
            logger.info("传送完成")
            self._control_service.activate()

            if bossName == "罗蕾莱":
                self.lorelei_clock_adjust()

            # 走/跑向boss
            forward_walk_times = forward_walk_times_mapping.get(bossName, 0)
            forward_run_seconds = forward_run_seconds_mapping.get(bossName, 0)
            time.sleep(1.2)  # 等站稳了再动
            if forward_walk_times > 0:
                if bossName == "赫卡忒" and self._ocr_service.find_text("进入声之领域"):
                    pass
                else:
                    self._control_service.forward_walk(forward_walk_times)
            elif forward_run_seconds > 0:
                self._control_service.forward_run(forward_run_seconds)

            if bossName == "无冠者":
                i = 0
                while i < 8 and not self._ocr_service.find_text("^声弦$"):
                    self._control_service.forward_walk(3)
                    i += 1

            now = datetime.now()
            self._info.idleTime = now  # 重置空闲时间
            self._info.lastFightTime = now  # 重置最近检测到战斗时间
            self._info.fightTime = now  # 重置战斗时间
            self._info.lastBossName = bossName
            self._info.waitBoss = True
            return True
        else:
            logger.warning("未找到快速旅行, 可能未解锁boss传送")
        self._control_service.esc()
        return False

    def lorelei_clock_adjust(self):
        time.sleep(2)
        self._control_service.activate()
        find_sit_and_wait_text = self._ocr_service.find_text(["坐上椅子等待", "坐上椅子", "的到来"])
        if not find_sit_and_wait_text:
            return
        logger.info("罗蕾莱不在家，等她")
        self._control_service.esc()
        time.sleep(2)
        if not self._ocr_service.wait_text("^终端$", timeout=5):
            self._control_service.esc()
            return
        # random_click(1374, 1038)
        self._control_service.click(1374, 1038)
        time.sleep(2)
        tomorrow = self._ocr_service.wait_text("^次日$", timeout=5)
        if not tomorrow:
            logger.warning("未找到次日")
            self._control_service.esc()
            return
        self.click_position(tomorrow)
        time.sleep(1)
        confirm_text = self._ocr_service.find_text("确定")
        self.click_position(confirm_text)
        time.sleep(2)
        self._ocr_service.wait_text("时间", timeout=10)
        time.sleep(1)
        self._control_service.esc()
        self._ocr_service.wait_text("^终端$", timeout=5)
        time.sleep(1)
        self._control_service.esc()
        time.sleep(0.5)

    @property
    def _info(self):
        return self._context.boss_task_ctx

    @property
    def _config(self):
        return self._context.config.app

    def _check_heal(self):
        self._info.isCheckedHeal = True
        logger.debug("Current roleIndex: %s", self._info.roleIndex)
        for i in range(3):
            role_index = (self._info.roleIndex + i) % 3
            # logger.debug("role_index: %s", role_index)
            self._control_service.toggle_team_member(role_index + 1)
            time.sleep(0.5)
        # position = Position.build(325, 190, 690, 330)
        if self._ocr_service.wait_text("选择复苏物品", timeout=2):
            logger.debug("检测到角色需要复苏")
            self._info.needHeal = True
            self._control_service.esc()
            time.sleep(1.2)

    def click_position(self, position: Position):
        self._control_service.click(*position.center)

    def _need_retry(self):
        return len(self._config.TargetBoss) == 1 and self._config.TargetBoss[0] in ["无妄者", "角", "赫卡忒"]

    def wait_home(self, timeout=120) -> bool:
        """
        等待回到主界面
        :param timeout:  超时时间
        :return:
        """
        start = datetime.now()
        time.sleep(0.1)
        # i = 0
        while True:
            # i += 1
            # logger(f"i={i}", "DEBUG")
            self._control_service.activate()
            # 修复部分情况下导致无法退出该循环的问题。
            if (datetime.now() - start).seconds > timeout:
                self._window_service.close_window()
                raise Exception("等待回到主界面超时")
            img = self._img_service.screenshot()
            if img is None:
                time.sleep(0.3)
                continue

            # 获取右下角四分之一部分
            h, w = img.shape[:2]  # 获取高度和宽度
            cropped_img = img[h // 2:, w // 2:]  # 裁剪右下角

            # is_ok = False
            results = self._ocr_service.ocr(cropped_img)
            text_result = self._ocr_service.search_text(results, "快速旅行")
            if text_result:
                text_result.confidence = text_result.confidence
                # logger.debug("Match text: Fast Travel, %s", text_result)
                time.sleep(0.3)
                continue
            text_result = self._ocr_service.search_text(results, "特征码|^特征.+\d{5,}")
            if text_result:
                text_result.confidence = text_result.confidence
                # logger.debug("Match text: UID, %s", text_result)
                return True
                # is_ok = True
            # else:
            #     logger.debug("No match for text: UID")
            # 图片检测
            pic_array = [
                ("Quests.png", 0.8),
                ("Backpack.png", 0.8),
                ("Guidebook.png", 0.8),
            ]
            for template_img, threshold in pic_array:
                position = self._img_service.match_template(img=img, template_img=template_img, threshold=threshold)
                if position:
                    # logger.debug(f"Match template: {pic_name}, {position}")
                    return True
                    # is_ok = True
                # else:
                #     logger.debug(f"No match for template: {pic_name}")
                time.sleep(0.01)
            # if is_ok:
            #     return is_ok
            time.sleep(0.3)

    def _od_search(self, img, search_type: str):
        if search_type == "boss":
            return self._od_service.search_echo(img)
        elif search_type == "reward":
            return self._od_service.search_reward(img)
        else:
            raise NotImplemented("未实现的搜索方式")