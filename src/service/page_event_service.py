import logging
import re
import time
from abc import ABC
from datetime import datetime, timedelta
from typing import Callable

import numpy as np

from src.core.boss import BossNameEnum, MoveMode, Direction, RouteStep
from src.core.color import ColorRule, Color, ColorMatch
from src.core.combat.combat_core import ResonatorNameEnum, BaseResonator, ScenarioEnum
from src.core.combat.combat_system import CombatSystem
from src.core.contexts import Context, Status
from src.core.geometry import AnchorPoint, Align, AnchorBBox
from src.core.i18n import Language
from src.core.interface import ControlService, OCRService, PageEventService, ImgService, WindowService, ODService, \
    BossInfoService
from src.core.pages import ConditionalAction, TextMatch, Page
from src.core.regions import TextPosition, DynamicPosition, Position, DynamicPointTransformer, AlignEnum

logger = logging.getLogger(__name__)


class PageEventAbstractService(PageEventService, ABC):
    """通过页面ocr所得文字匹配关键字触发相应事件，触发动作"""

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService,
                 boss_info_service: BossInfoService):
        self._context: Context = context
        self._window_service: WindowService = window_service
        self._img_service: ImgService = img_service
        self._ocr_service: OCRService = ocr_service
        self._control_service: ControlService = control_service
        self._od_service: ODService = od_service
        self._boss_info_service: BossInfoService = boss_info_service
        # page
        self._UI_F2_Guidebook_Activity = self.build_UI_F2_Guidebook_Activity()
        self._UI_F2_Guidebook_RecurringChallenges = self.build_UI_F2_Guidebook_RecurringChallenges()
        self._UI_F2_Guidebook_PathOfGrowth = self.build_UI_F2_Guidebook_PathOfGrowth()
        self._UI_F2_Guidebook_EchoHunting = self.build_UI_F2_Guidebook_EchoHunting()
        self._UI_F2_Guidebook_Milestones = self.build_UI_F2_Guidebook_Milestones()
        self._UI_ESC_Terminal = self.build_UI_ESC_Terminal()
        self._UI_ESC_LeaveInstance = self.build_UI_ESC_LeaveInstance()
        self._UI_ESC_LeaveInstance_NightmareHecate = self.build_UI_ESC_LeaveInstance_NightmareHecate()
        self._Reward_TapTheBlankAreaToClose = self.build_Reward_TapTheBlankAreaToClose()
        self._Reward_LuniteSubscriptionReward = self.build_Reward_LuniteSubscriptionReward()
        self._F_EnterForgeryChallenge = self.build_F_EnterForgeryChallenge()
        self._Challenge_EnterSoloChallenge = self.build_Challenge_EnterSoloChallenge()
        self._Reward_ClaimRewards_ForgeryChallenge = self.build_Reward_ClaimRewards_ForgeryChallenge()
        self._Reward_ClaimRewards_TacetSuppression = self.build_Reward_ClaimRewards_TacetSuppression()
        self._build_Reward_ClaimRewards_Boss = self.build_Reward_ClaimRewards_Boss()

        self.combat_system = CombatSystem(control_service, img_service)
        self.combat_system.is_async = True

        # param
        self._echo_hunting_pos_1280_list = [(50, 487), (50, 578), (50, 396)]

        # 左侧图标坐标
        self.activitySidebar = AnchorPoint(50, 128, Align.Top | Align.Left)
        self.materialsSpotsSidebar = AnchorPoint(50, 218, Align.Top | Align.Left)
        self.recurringChallengesSidebar = AnchorPoint(50, 308, Align.Top | Align.Left)
        self.pathOfGrowthSidebar = AnchorPoint(50, 396, Align.Top | Align.Left)
        self.enemyTracingSidebar = [
            AnchorPoint(50, 487, Align.Top | Align.Left),
            AnchorPoint(50, 578, Align.Top | Align.Left),
            AnchorPoint(50, 396, Align.Top | Align.Left),
        ]
        self.milestonesSidebar = AnchorPoint(50, 578, Align.Top | Align.Left)

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

        logger.debug(ocr_results)
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
                Language.ZH: [
                    "UI_F2_Guidebook_Activity_001.png",
                    "UI_F2_Guidebook_Activity_002.png",
                    "UI_F2_Guidebook_Activity_003.png",
                    "UI_F2_Guidebook_Activity_004.png",
                ],
                Language.EN: [
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
                Language.ZH: [
                    "UI_F2_Guidebook_RecurringChallenges_001.png",
                ],
                Language.EN: [
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
                Language.ZH: [
                    "UI_F2_Guidebook_PathOfGrowth_001.png",
                ],
                Language.EN: [
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
                Language.ZH: [
                    "UI_F2_Guidebook_EchoHunting_001.png",
                ],
                Language.EN: [
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
                Language.ZH: [
                    "UI_F2_Guidebook_Milestones_001.png",
                ],
                Language.EN: [
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
                if self._context.param_config.autoCombatBeta is True and self.combat_system.resonators is None:
                    self.team_members_ocr(positions.get("编队|Team"))
                else:
                    self._control_service.esc()
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="UI-终端|Terminal",
            screenshot={
                Language.ZH: [
                    "UI_ESC_Terminal_001.png",
                ],
                Language.EN: [
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
                # TextMatch(
                #     name="生日|Birthday",
                #     text=r"^(生日|Birthday)$",
                # ),
                TextMatch(
                    name="编队|Team",
                    text=r"^(编队|Team)$",
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
                Language.ZH: [
                    "Reward_LuniteSubscriptionReward_001.png"
                ],
                Language.EN: [
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
                    if self._boss_info_service.is_nightmare(self._info.lastBossName):
                        logger.info("治疗次数：%s", self._info.healCount)
                    elif self._boss_info_service.is_auto_pickup(self._info.lastBossName):
                        logger.info("战斗次数：%s 治疗次数：%s", self._info.fightCount, self._info.healCount)
                    else:
                        logger.info("战斗次数：%s 吸收次数：%s 治疗次数：%s", self._info.fightCount,
                                    self._info.absorptionCount, self._info.healCount)
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
                Language.ZH: [
                    # "UI_ESC_LeaveInstance_001.png",
                ],
                Language.EN: [
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

    def build_UI_ESC_LeaveInstance_NightmareHecate(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.activate()
                time.sleep(0.2)
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
            name="UI-离开副本|LeaveInstance-NightmareHecate",
            screenshot={
                Language.ZH: [
                    # "UI_ESC_LeaveInstance_001.png",
                ],
                Language.EN: [
                    # "UI_ESC_LeaveInstance_001_EN.png",
                ],
            },
            targetTexts=[
                TextMatch(
                    name="提示|Notice",
                    text=r"^(提示|Notice)$",
                ),
                TextMatch(
                    name="确认离开|Leave this domain",
                    text=r"^(确认离开|Leave\s*this\s*domain)",
                ),
                TextMatch(
                    name="确认|Confirm",
                    text=r"^(确认|Confirm)$",
                ),
                TextMatch(
                    name="取消|Cancel",
                    text=r"^(取消|Cancel)$",
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
                Language.ZH: [
                    "F_EnterForgeryChallenge_001.png",
                ],
                Language.EN: [
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
                Language.ZH: [
                    "F_EnterForgeryChallenge_001.png",
                ],
                Language.EN: [
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
                Language.ZH: [
                    "Reward_ClaimRewards_001.png",
                    "Reward_ClaimRewards_002.png",
                ],
                Language.EN: [
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
                Language.ZH: [
                    "Reward_ClaimRewards_001.png",
                    "Reward_ClaimRewards_002.png",
                ],
                Language.EN: [
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

    def build_Reward_ClaimRewards_Boss(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                self._control_service.esc()
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="Reward-领取奖励|ClaimRewards-Boss",
            screenshot={
                Language.ZH: [
                ],
                Language.EN: [
                ],
            },
            targetTexts=[
                TextMatch(
                    name="领取奖励|Claim Rewards",
                    text=r"^(领取奖励|Claim\s*Rewards)$",
                ),
                TextMatch(
                    name="重新挑战|Restart",
                    text=r"^(重新挑战|Restart)$",
                ),
                TextMatch(
                    name="确认|Confirm",
                    text=r"^(确认|Confirm)$",
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
                Language.ZH: [
                    "",
                ],
                Language.EN: [
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

    def build_Login_Confirm_UpdateFinished(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                position = positions["确认"]
                self._control_service.click(*position.center)
                time.sleep(2)
                return True

            action = default_action

        return Page(
            name="更新完成，游戏即将重启",
            targetTexts=[
                TextMatch(
                    name="更新完成",
                    text=r"^更新完成.*游戏即将重启",
                ),
                TextMatch(
                    name="确认|Confirm",
                    text=r"^(确认|Confirm)$",
                ),
            ],
            action=action if action else Page.error_action
        )

    def build_Fight_Absorption(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                # if self._info.lastBossName == BossNameEnum.Fenrico.value:
                #     return False

                time.sleep(0.2)
                if not self._ocr_service.find_text(["吸收"]):
                    return False
                # dump_img()

                self._info.absorptionCount += 1
                self._control_service.pick_up()
                time.sleep(0.5)
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
                is_nightmare = self._boss_info_service.is_nightmare(self._info.lastBossName)
                if self._context.param_config.autoCombatBeta is True:
                    self.combat_system.pause()
                    if is_nightmare:
                        self._control_service.pick_up()
                else:
                    time.sleep(1)
                    return True

                if not is_nightmare:
                    time.sleep(1)
                    return True

                self.combat_system.exit_special_state(ScenarioEnum.BeforeEchoSearch)
                # logger.info(f"self._info.needAbsorption: {self._info.needAbsorption}")
                if self._info.needAbsorption:
                    self.search_echo()

                if self._config.CharacterHeal is not True:
                    return True
                self._check_heal()
                if self._info.needHeal:
                    logger.info("有角色阵亡，开始治疗")
                    # time.sleep(1)
                    # self._info.lastBossName = "治疗"
                    self.transfer()
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
                if self._context.param_config.autoCombatBeta is True:
                    if self._info.waitBoss:
                        logger.info("智能连招beta开启")  # 放这里不会频繁打印
                        self.boss_wait(self._info.lastBossName)
                    if self.combat_system.resonators is None:
                        self.team_members_ocr()
                        return True
                    if self.combat_system.is_boss_health_bar_exist():
                        self.combat_system.auto_pickup = self._boss_info_service.is_auto_pickup(self._info.lastBossName)
                        self.combat_system.start(3.5)
                        time.sleep(1.5)
                    else:
                        time.sleep(0.75)
                else:
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
                    # text=r"(击败|对战|泰缇斯系统|凶戾之齿|倦怠之翼|妒恨之眼|(无餍之舌)|(僭?越之矛)|(谵?妄之爪)|爱欲之容|盖希诺姆|(愚执之瞳?)|背誓之脊|遗恨之指|异海归途)",
                    text=r"(击败|对战|泰缇斯系统|凶戾之齿|倦怠之翼|妒恨之眼|(无.?之舌)|(.?越之矛)|(.?妄之爪)|爱欲之容|盖希诺姆|(愚执之.?)|背誓之脊|遗恨之指|异海归途|荣光的灰.?)",
                ),
            ],
            excludeTexts=[
                TextMatch(
                    name="活跃度",
                    text="^活跃度$",
                ),
                TextMatch(
                    name="挑战成功",
                    text="^挑战成功$",
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
                if self._context.param_config.autoCombatBeta is True and self.combat_system.resonators is None:
                    self.team_members_ocr()

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
                if self._context.param_config.autoCombatBeta is True and self.combat_system.resonators is None:
                    self.team_members_ocr()

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
                if self._context.param_config.autoCombatBeta is True and self.combat_system.resonators is None:
                    self.team_members_ocr()

                self._control_service.pick_up()
                self._info.in_dungeon = True
                # TODO 启动时就站在声之领域门口，无法区分是打哪个boss
                if not self._info.lastBossName:
                    if BossNameEnum.Fleurdelys.value in self._config.TargetBoss:
                        self._info.lastBossName = BossNameEnum.Fleurdelys.value
                    elif BossNameEnum.NightmareHecate.value in self._config.TargetBoss:
                        self._info.lastBossName = BossNameEnum.NightmareHecate.value
                    elif BossNameEnum.Hecate.value in self._config.TargetBoss:
                        self._info.lastBossName = BossNameEnum.Hecate.value
                    elif BossNameEnum.LadyOfTheSea.value in self._config.TargetBoss:
                        self._info.lastBossName = BossNameEnum.LadyOfTheSea.value
                    elif BossNameEnum.TheFalseSovereign.value in self._config.TargetBoss:
                        self._info.lastBossName = BossNameEnum.TheFalseSovereign.value
                    elif BossNameEnum.ThrenodianLeviathan.value in self._config.TargetBoss:
                        self._info.lastBossName = BossNameEnum.ThrenodianLeviathan.value
                    elif BossNameEnum.Sigillum.value in self._config.TargetBoss:
                        self._info.lastBossName = BossNameEnum.Sigillum.value
                    else:
                        self._info.lastBossName = BossNameEnum.Hecate.value
                return True

            action = default_action

        return Page(
            name="声之领域|梦魇领域|最终章",
            targetTexts=[
                TextMatch(
                    name="声之领域|梦魇领域|最终章",
                    text=r"^(进入声之领域|进入梦.?领域|进入.*最终章.*)$",
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

                final_level = None
                for i in range(6):
                    level = (dungeon_weekly_boss_level + 10 * i - 40) % 60 + 40
                    result = self._ocr_service.wait_text("推荐等级" + str(level))
                    if not result:
                        continue
                    self._control_service.click(*result.center)
                    time.sleep(0.3)
                    result = self._ocr_service.find_text("单人挑战")
                    if not result:
                        self._control_service.esc()
                        break
                    self._control_service.click(*result.center)
                    time.sleep(0.2)
                    result = self._ocr_service.wait_text("等级差距过大", 1, wait_time=0.2)
                    if result:
                        time.sleep(0.2)
                        self._control_service.esc()
                        time.sleep(0.5)
                        continue
                    self._info.DungeonWeeklyBossLevel = level
                    final_level = level
                    break

                if not final_level:
                    self._control_service.esc()
                    time.sleep(0.5)
                    return False

                find_challenge = False
                for _ in range(2):
                    result = self._ocr_service.wait_text(["开启挑战", "结晶波片不足"], timeout=3, wait_time=0.3)
                    if not result:
                        return False
                    if challenge := self._ocr_service.search_text([result], "开启挑战"):
                        find_challenge = True
                        time.sleep(0.3)
                        self._control_service.click(*challenge.center)
                        time.sleep(0.2)
                        self._control_service.click(*challenge.center)
                        time.sleep(0.5)
                        break
                    elif self._ocr_service.search_text([result], "结晶波片不足"):
                        result = self._ocr_service.find_text("本次登录不再提示")
                        if result:
                            self._control_service.click(*result.center)
                            time.sleep(0.1)
                        result = self._ocr_service.find_text("^确认$")
                        if result:
                            self._control_service.click(*result.center)
                            time.sleep(0.3)

                if not find_challenge:
                    self._control_service.esc()
                    time.sleep(0.5)
                    return False

                logger.info(f"最低推荐等级为{self._info.DungeonWeeklyBossLevel}级")
                self._info.waitBoss = True
                time.sleep(1)
                self._info.lastFightTime = datetime.now()
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
                # TextMatch(
                #     name="结晶波片",
                #     text="结晶波片",
                # ),
                TextMatch(
                    name="可收取次数",
                    text="可收取次数",
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
                Language.ZH: [
                    "",
                ],
                Language.EN: [
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

    def build_Fight_Click_alternately_to_break_free(self, action: Callable = None) -> Page:

        if action is None:
            def default_action(positions: dict[str, Position]) -> bool:
                for _ in range(4):
                    self._control_service.left()
                    self._control_service.right()
                return True

            action = default_action

        return Page(
            name="交替点击进行挣脱|Click alternately to break free",
            targetTexts=[
                TextMatch(
                    name="交替点击进行挣脱|Click alternately to break free",
                    text=r"^(交替点击进行挣脱|Click\s*alternately\s*to\s*break\s*free)$",
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

        is_nightmare = self._boss_info_service.is_nightmare(self._info.lastBossName)
        if is_nightmare:
            self._control_service.fight_tap("F", 0.01)
        for index, tactic in enumerate(tactics):  # 遍历对应角色的战斗策略
            try:
                if is_nightmare and index % 2 == 0:
                    self._control_service.fight_tap("F", 0.01)
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
                time.sleep(14)
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
            case "赫卡忒":
                time.sleep(0.3)
                self._control_service.forward_run(2.1)
            case "芙露德莉斯":
                time.sleep(0.3)
                self._control_service.forward_run(2.1)
            case BossNameEnum.LadyOfTheSea.value:
                time.sleep(0.3)
                self._control_service.forward_run(1.0)
            case _:
                pass

        self._info.waitBoss = False

    def absorption_action(self, search_type: str = "echo"):
        self._info.needAbsorption = False
        time.sleep(2)

        if self._context.param_config.autoCombatBeta is True:
            self.combat_system.exit_special_state(ScenarioEnum.BeforeEchoSearch)

        # 是否在副本中
        if self.absorption_and_receive_rewards({}):
            # if self._info.in_dungeon:
            #     self._control_service.esc()
            #     time.sleep(1)
            return

        if self._info.lastBossName in [
            BossNameEnum.Fleurdelys.value,
            BossNameEnum.ThrenodianLeviathan.value,
            BossNameEnum.SeedOfIllusoryOrigin.value,
            BossNameEnum.Denia.value,
            BossNameEnum.NightmareAdamSmasherLimitedTime.value,
            BossNameEnum.NightmareAdamSmasher.value,
        ]:
            self.absorption_action_fleurdelys()
            return
        elif self._info.lastBossName == BossNameEnum.Fenrico.value:
            self.absorption_action_fenrico()
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

        search_region = self.get_dialogue_region()

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

                # # train
                # img = self._img_service.screenshot()
                # from src.util import img_util
                # from src.util import file_util
                # img_name = self._boss_info_service.get_boss_name_zh_en(self._info.lastBossName)
                # img_path = file_util.create_img_path(prefix=img_name)
                # img_util.save_img(img, img_path)

                if echo_box is None:
                    logger.debug("未发现声骸")
                    self._control_service.left(0.1)
                    time.sleep(0.2)
                    self._control_service.camera_reset()
                    time.sleep(0.8)
                    if i == max_range - 1:
                        # # 可能掉在正前方被人物挡住，前进一下再最后看一次
                        # for _ in range(4):
                        #     self._control_service.up(0.1)
                        #     time.sleep(0.1)
                        # for _ in range(2):
                        #     self._control_service.left(0.1)
                        # time.sleep(0.3)
                        # img = self._img_service.screenshot()
                        # echo_box = self._od_service.search_echo(img)
                        # if echo_box is not None:
                        #     break
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

        if self._info.lastBossName == BossNameEnum.TheFalseSovereign.value:
            self.absorption_action_the_false_sovereign()
            return

    def absorption_action_fleurdelys(self):
        search_region = self.get_dialogue_region()
        run_param = [("w", 0.22), ("w", 0.23), ("a", 0.22), ("s", 0.27), ("s", 0.27), ("d", 0.22), ("w", 0.27),
                     ("d", 0.22), ("w", 0.23), ("s", 0.53)]
        for i in range(len(run_param)):
            key, sleep_time = run_param[i]
            if i > 0:
                self._control_service.player().fight_tap(key, 0.05)
                self._control_service.player().fight_tap(key, 0.05)
            self._control_service.forward_run(sleep_time, key)
            time.sleep(0.75)
            if self._ocr_service.find_text("^吸收$", None, search_region):
                self.absorption_and_receive_rewards({})
                return

    def absorption_action_fenrico(self):
        self._info.challengeFenricoCount += 1

        # 牢芬打完得时停一下才爆金币
        time.sleep(2)
        for i in range(3):
            if self._ocr_service.find_text("^(芬莱克|仍可留下)$"):
                time.sleep(1.25)
                continue
            break

        # 单刷
        is_solo_boss = len(self._config.TargetBoss) == 1 and self._config.TargetBoss[0] == BossNameEnum.Fenrico.value

        search_region = self.get_dialogue_region()
        dpt = DynamicPointTransformer(self._window_service.get_client_wh())

        skip_search = False
        absorb = self._ocr_service.find_text("^吸收$", None, search_region)
        if absorb and self.absorption_and_receive_rewards({}):
            time.sleep(0.2)
            skip_search = True

        # 单刷就刷几轮再去一次性全吸收，声骸位置固定都在一起
        if is_solo_boss and self._info.challengeFenricoCount % 3 != 1:
            skip_search = True

        for step in range(3):
            # 正好在脚下，已经吸收了，跳过搜索
            if step == 0 and skip_search:
                continue

            # 捡完声骸，仅单选这个boss时才触发寻找重新挑战，若多选boss，退出正常触发传送下一个boss
            if step > 0 and not is_solo_boss:
                return

            time.sleep(1.0)
            self._control_service.map()
            time.sleep(2.5)
            lumen_tower_pos = self._ocr_service.wait_text(r"^(涌明高塔|Lumen\s*Tower)$", timeout=5)
            if not lumen_tower_pos:
                logger.warning("未找到涌明高塔")
                self._control_service.esc()
                time.sleep(2.0)
                return

            # 通过文本动态计算相对位置
            lumen_tower_pos_1280_720 = dpt.untransform((lumen_tower_pos.x1, lumen_tower_pos.y1), AlignEnum.CENTER)
            fenrico_pos_1280_720 = (
                lumen_tower_pos_1280_720[0] - (605 - 600),
                lumen_tower_pos_1280_720[1] - (351 - 300)
            )
            fenrico_pos = dpt.transform(fenrico_pos_1280_720, AlignEnum.CENTER)

            time.sleep(0.7)
            self._control_service.click(*fenrico_pos)
            time.sleep(0.7)
            position = self._ocr_service.wait_text(r"^(快速旅行|Fast\s*Travel)$", timeout=5)
            if not position:
                logger.warning("未找到快速旅行")
                self._control_service.esc()
                time.sleep(0.5)
                return

            time.sleep(0.7)
            self._control_service.click(*position.random)
            time.sleep(2.5)
            self.wait_home()
            time.sleep(1.5)

            if step == 0:
                self._control_service.forward_run(4.0)

                i = 0
                while i < 14:
                    if not self._ocr_service.find_text("^吸收$", None, search_region):
                        self._control_service.forward_walk(2)
                        i += 1
                        continue
                    # 一但找到吸收，原地一直吸，因为前面设置了打几轮才触发一次吸收，声骸可能有多个
                    max_search = 5
                    while max_search > 0 and self.absorption_and_receive_rewards({}):
                        max_search -= 1
                        time.sleep(0.5)
                    break

            elif step >= 1:
                self._control_service.forward_run(0.85)

                found_restart = False
                i = 0
                while i < 9:
                    restart = self._ocr_service.find_text(r"^(重新挑战|Restart)$", None, search_region)
                    if restart:
                        found_restart = True
                        time.sleep(0.3)
                        break
                    self._control_service.forward_walk(2)
                    i += 1

                fenrico_pos = None
                # 理论上有重新挑战，若没有，可能是boss又刷出来了，再检查boss
                if not found_restart:
                    fenrico_pos = self._ocr_service.find_text(rf"^{BossNameEnum.Fenrico.value}$")
                    # boss也没有，再重试
                    if not fenrico_pos:
                        continue

                if not fenrico_pos:
                    self._control_service.scroll_mouse(-1)
                    time.sleep(0.5)
                    logger.info("重新挑战")
                    self._control_service.pick_up()
                    time.sleep(3.6)
                # 跑去打boss
                self._control_service.forward_run(3.4 - 1.5)

                self._info.status = Status.idle
                now = datetime.now()
                self._info.idleTime = now  # 重置空闲时间
                self._info.lastFightTime = now  # 重置最近检测到战斗时间
                self._info.fightTime = now  # 重置战斗时间
                # self._info.lastBossName = bossName
                self._info.waitBoss = True

                time.sleep(1)
                return

    def absorption_action_the_false_sovereign(self):

        # 单刷
        is_solo_boss = len(self._config.TargetBoss) == 1 and self._config.TargetBoss[
            0] == BossNameEnum.TheFalseSovereign.value

        search_region = self.get_dialogue_region()
        dpt = DynamicPointTransformer(self._window_service.get_client_wh())

        if not is_solo_boss:
            return

        time.sleep(1.0)
        self._control_service.map()
        time.sleep(2.5)
        map_text_pos = self._ocr_service.wait_text(r"^(彻地之.?|Earthrend\s*Wedge)$", timeout=5)
        if not map_text_pos:
            logger.warning("未找到彻地之楔")
            self._control_service.esc()
            time.sleep(2.0)
            return

        # 通过文本动态计算相对位置
        map_text_pos_1280_720 = dpt.untransform(
            ((map_text_pos.x1 + map_text_pos.x2) // 2, map_text_pos.y2), AlignEnum.CENTER)
        boss_pos_1280_720 = (
            map_text_pos_1280_720[0] - (669 - 669),
            map_text_pos_1280_720[1] + (359 - 257)
        )
        boss_pos = dpt.transform(boss_pos_1280_720, AlignEnum.CENTER)

        time.sleep(0.7)
        self._control_service.click(*boss_pos)
        time.sleep(0.7)
        position = self._ocr_service.wait_text(r"^(快速旅行|Fast\s*Travel)$", timeout=5)
        if not position:
            logger.warning("未找到快速旅行")
            self._control_service.esc()
            time.sleep(0.5)
            return

        time.sleep(0.7)
        self._control_service.click(*position.random)
        time.sleep(2.5)
        self.wait_home()
        time.sleep(1.5)

        self._control_service.forward_run(2.5)

        found_restart = False
        i = 0
        while i < 12:
            restart = self._ocr_service.find_text(r"^(重新挑战|Restart)$", None, search_region)
            if restart:
                found_restart = True
                time.sleep(0.3)
                break
            self._control_service.forward_walk(2)
            i += 1

        # 理论上有重新挑战，若没有，可能是boss又刷出来了，再检查boss
        if not found_restart:
            return

        self._control_service.scroll_mouse(-1)
        time.sleep(0.5)
        logger.info("重新挑战")
        self._control_service.pick_up()
        time.sleep(2.0)

        self._info.status = Status.idle
        now = datetime.now()
        self._info.idleTime = now  # 重置空闲时间
        self._info.lastFightTime = now  # 重置最近检测到战斗时间
        self._info.fightTime = now  # 重置战斗时间
        # self._info.lastBossName = bossName
        self._info.waitBoss = True

        time.sleep(1)
        return

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
        if self._boss_info_service.is_nightmare(self._info.lastBossName):
            logger.info("治疗次数：%s", self._info.healCount)
        elif self._boss_info_service.is_auto_pickup(self._info.lastBossName):
            logger.info("战斗次数：%s 治疗次数：%s", self._info.fightCount, self._info.healCount)
        else:
            logger.info("战斗次数：%s 吸收次数：%s 治疗次数：%s", self._info.fightCount,
                        self._info.absorptionCount, self._info.healCount)
        self._info.isCheckedHeal = False
        if self._config.CharacterHeal and self._info.needHeal:  # 检查是否需要治疗
            logger.info("有角色阵亡，开始治疗")
            time.sleep(1)

            # logger.info(f"self._info.lastBossName: {self._info.lastBossName}")
            if self._info.lastBossName == BossNameEnum.NightmareHecate.value:
                self._control_service.esc()
                time.sleep(1)
                position = self._ocr_service.find_text("^确认$")
                if position:
                    self.click_position(position)
                    time.sleep(3)
                    self.wait_home()
                    self._info.needHeal = False
                    self._info.healCount += 1
                    logger.info(f"{self._info.lastBossName}副本结束")
                    time.sleep(2)
                    position = self._ocr_service.find_text("^进入梦.?领域$")
                    if position:
                        self._control_service.pick_up()
                        logger.info("进入梦魇领域")
                        time.sleep(1.5)
                        self._control_service.pick_up()
                        time.sleep(1.5)
                        return True

                    self._info.in_dungeon = False
                    self._info.status = Status.idle
                    now = datetime.now()
                    self._info.lastFightTime = now + timedelta(seconds=self._config.MaxFightTime / 2)
                    return True

            self._info.lastBossName = "治疗"
            self._transfer_to_heal()
        elif self._context.param_config.autoCombatBeta is True and self.combat_system.resonators is None:
            time.sleep(1)
            self.team_members_ocr()

        bossName = self._config.TargetBoss[self._info.bossIndex % len(self._config.TargetBoss)]

        self._control_service.activate()
        time.sleep(0.2)

        if len(self._config.TargetBoss) == 1 and bossName == BossNameEnum.LadyOfTheSea.value:
            if self._ocr_service.find_text(r"^(进入.*最终章.*)$"):
                self._control_service.pick_up()
                self._info.in_dungeon = True

                now = datetime.now()
                self._info.idleTime = now  # 重置空闲时间
                self._info.lastFightTime = now  # 重置最近检测到战斗时间
                self._info.fightTime = now  # 重置战斗时间
                self._info.lastBossName = bossName
                self._info.waitBoss = True
                return True

        self._control_service.guidebook()
        time.sleep(1)
        if not self._ocr_service.wait_text(["日志", "活跃", "挑战", "强者", "残象", "周期", "探寻", "漂泊", "素材获取"],
                                           timeout=7):
            logger.warning("未进入索拉指南")
            self._control_service.esc()
            self._info.lastFightTime = datetime.now()
            return False
        time.sleep(1)
        self._info.bossIndex += 1
        return self.transfer_to_boss(bossName)

    def _transfer_to_heal(self, skip_map=False):
        self._control_service.activate()
        if skip_map is False:
            self._control_service.map()
        time.sleep(3)
        toggle_map = self._ocr_service.wait_text("切换地图")
        if not toggle_map:
            self._control_service.esc()
            logger.info("未找到切换地图")
            return False
        try:
            # tmp_x = int((toggle_map.x1 + toggle_map.x2) // 2)
            # tmp_y = int((toggle_map.y1 + toggle_map.y2) // 2)
            # random_click(tmp_x, tmp_y, ratio=False)
            self.click_position(toggle_map)
            huanglong_text = self._ocr_service.wait_text("瑝?珑")
            if not huanglong_text:
                self._control_service.esc()
                logger.info("未找到瑝珑")
                return False
            self.click_position(huanglong_text)
            time.sleep(0.5)
            self.click_position(huanglong_text)
            time.sleep(1.5)
            if jzc_text := self._ocr_service.wait_text("今州城"):
                self.click_position(jzc_text)
                time.sleep(0.5)
                self.click_position(jzc_text)
                time.sleep(1.5)

                jzcj_pos = self._ocr_service.wait_text("今州城界")
                if not jzcj_pos:
                    self._control_service.esc()
                    logger.info("未找到今州城界")
                    return False
                dpt = DynamicPointTransformer(self._window_service.get_client_wh())
                jzcj_pos_1280_720 = dpt.untransform((jzcj_pos.x1, jzcj_pos.y1), AlignEnum.CENTER)
                jinzhou_resonance_nexus_1280_720 = (jzcj_pos_1280_720[0] - 12, jzcj_pos_1280_720[1] - 45)
                jinzhou_resonance_nexus = dpt.transform(jinzhou_resonance_nexus_1280_720, AlignEnum.CENTER)
                self._control_service.click(*jinzhou_resonance_nexus)
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
            logger.exception(f"前往复活点过程中出现异常")
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
        search_region = self.get_dialogue_region()
        w, h = self._window_service.get_client_wh()
        need_retry = False
        max_ocr = 3
        count = 0
        while count < max_ocr or need_retry:
            img = self._img_service.screenshot()
            results = self._ocr_service.ocr(img, search_region)
            absorption = self._ocr_service.search_text(results, "^吸收$")

            # 没有吸收，再试一次
            if not absorption:
                if need_retry:
                    break
                need_retry = True
                continue

            receive_reward = self._ocr_service.search_text(results, r"^领取奖励$")
            # 部分boss可以重新挑战
            restart = self._ocr_service.search_text(results, r"^重新挑战$")
            # 有吸收和领取奖励，吸收在下则滚动到下方
            if receive_reward:
                logger.debug(f"absorption: {absorption}, receive_reward: {receive_reward}")
                if restart:
                    points = [absorption, receive_reward, restart]
                else:
                    points = [absorption, receive_reward]
                sorted_points = sorted(points, key=lambda x: x.y1)
                absorption_index = 0
                for index, point in enumerate(sorted_points):
                    if point.y1 == absorption.y1:
                        absorption_index = index
                        break
                if absorption_index > 0:
                    for _ in range(absorption_index):
                        logger.info("向下滚动")
                        self._control_service.scroll_mouse(-1)
                        time.sleep(0.5)

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
        # 自动拾取的统计不准，不打印
        if not self._boss_info_service.is_auto_pickup(self._info.lastBossName):
            logger.info("目前声骸吸收率为：%s", str(format(absorption_rate * 100, ".2f")))
        return True

    def transfer_to_boss(self, bossName):
        # 暂停自动战斗，否则会把按键打在输入框里
        if self._context.param_config.autoCombatBeta is True:
            self.combat_system.pause()
            time.sleep(0.2)

        scaler = self._window_service.scaler

        activitySidebar = scaler.as_point(self.activitySidebar)
        materialsSpotsSidebar = scaler.as_point(self.materialsSpotsSidebar)
        recurringChallengesSidebar = scaler.as_point(self.recurringChallengesSidebar)
        pathOfGrowthSidebar = scaler.as_point(self.pathOfGrowthSidebar)
        enemyTracingSidebar = [scaler.as_point(p) for p in self.enemyTracingSidebar]
        milestonesSidebar = scaler.as_point(self.milestonesSidebar)

        if bossName == BossNameEnum.SeedOfIllusoryOrigin.value:
            self._control_service.click(*materialsSpotsSidebar)
            time.sleep(0.6)
            weeklyChallenge = self._ocr_service.wait_text(r"^(战歌重奏)$")
            if weeklyChallenge:
                self._control_service.click(*weeklyChallenge.center)
                time.sleep(0.2)
                self._control_service.click(*weeklyChallenge.center)
                time.sleep(0.6)
            img = self._img_service.screenshot()
            result = self._ocr_service.query(img)
            if result:
                go_list = result.search(r"^(前往)$")
                if go_list:
                    go_list.sort(key=lambda x: x.y1)
                    self._control_service.click(*go_list[0].center)
                    time.sleep(0.3)
                    story = self._ocr_service.wait_text(r"^确认$", timeout=2)
                    if story:
                        self._control_service.click(*story.center)
                        time.sleep(0.1)
                        self._control_service.click(*story.center)
                        time.sleep(0.3)

                    now = datetime.now()
                    self._info.idleTime = now  # 重置空闲时间
                    self._info.lastFightTime = now  # 重置最近检测到战斗时间
                    self._info.fightTime = now  # 重置战斗时间
                    self._info.lastBossName = bossName
                    self._info.waitBoss = True
                    return True

            logger.warning("未找到：虚妄诞生之种（限时提前开放）")
            self._control_service.esc()
            return False
        elif bossName == BossNameEnum.NightmareAdamSmasherLimitedTime.value:
            self._control_service.click(*materialsSpotsSidebar)
            time.sleep(0.6)
            weeklyChallenge = self._ocr_service.wait_text(r"^讨伐强敌$")
            if weeklyChallenge:
                self._control_service.click(*weeklyChallenge.center)
                time.sleep(0.2)
                self._control_service.click(*weeklyChallenge.center)
                time.sleep(0.6)
            img = self._img_service.screenshot()
            result = self._ocr_service.query(img)
            if result:
                go_list = result.search(r"^(前往)$")
                if go_list:
                    go_list.sort(key=lambda x: x.y1)
                    self._control_service.click(*go_list[0].center)
                    time.sleep(0.3)
                    story = self._ocr_service.wait_text(r"^确认$", timeout=2)
                    if story:
                        self._control_service.click(*story.center)
                        time.sleep(0.1)
                        self._control_service.click(*story.center)
                        time.sleep(0.3)

                    now = datetime.now()
                    self._info.idleTime = now  # 重置空闲时间
                    self._info.lastFightTime = now  # 重置最近检测到战斗时间
                    self._info.fightTime = now  # 重置战斗时间
                    self._info.lastBossName = bossName
                    self._info.waitBoss = True
                    return True

            logger.warning("未找到：梦魇亚当·重锤（限时提前开放）")
            self._control_service.esc()
            return False



        is_enemy_tracing = False
        for enemyTracingPoint in enemyTracingSidebar:
            self._control_service.click(*enemyTracingPoint)  # 进入残像探寻

            enemy_tracing_or_path_of_growth_pos = self._ocr_service.wait_text(
                r"^(敌迹探寻|Enemy\s*Tracing|探测|Detect|强者之路|Path\s*of\s*Growth|全息战略)$")

            if not enemy_tracing_or_path_of_growth_pos:
                break

            img = self._img_service.screenshot()
            results = self._ocr_service.ocr(img)
            enemy_tracing_pos = self._ocr_service.search_texts(results, r"^(敌迹探寻|Enemy\s*Tracing|探测|Detect)$")
            if enemy_tracing_pos:
                is_enemy_tracing = True
                break

        if not is_enemy_tracing:
            logger.warning("未进入残象探寻")
            self._control_service.esc()
            return False
        logger.info(f"当前目标boss：{bossName}")
        boss_name_reg_mapping = {
            "哀声鸷": "[哀袁]声.?",
            "辉萤军势": "辉.军势",
            "赫卡忒": "赫卡.?",
            "梦魇飞廉之猩": "梦.*飞廉之猩",
            "梦魇无常凶鹭": "梦.*无常凶鹭",
            "梦魇云闪之鳞": "梦.*云闪之鳞",
            "梦魇朔雷之鳞": "梦.*朔雷之鳞",
            "梦魇无冠者": "梦.*无冠者",
            "梦魇燎照之骑": "梦.*燎照之骑",
            "梦魇哀声鸷": "梦.*[哀袁]声.?",
            "梦魇辉萤军势": "梦.*辉.军势",
            "梦魇凯尔匹": "梦.*凯尔匹",
            "梦魇赫卡忒": "梦.*赫卡.?",
            "鸣式利维亚坦": "鸣式.*利维亚坦",
        }
        find_boss_name_reg = boss_name_reg_mapping.get(bossName, bossName)
        # findBoss = None
        search_boss_name = bossName
        if self._boss_info_service.is_nightmare(bossName) or bossName in [BossNameEnum.ThrenodianLeviathan.value]:
            search_boss_name = bossName[:2] + "." + bossName[2:]

        search_tips_pos = self._ocr_service.wait_text("输入搜索内容")
        if not search_tips_pos:
            logger.warning("识别输入框失败")
            self._control_service.esc()
            return False

        self._control_service.click(*search_tips_pos.center)
        time.sleep(0.2)
        self._control_service.click(*search_tips_pos.center)
        time.sleep(0.3)
        self._control_service.input_text(search_boss_name)
        time.sleep(0.5)
        self._control_service.enter()
        time.sleep(0.8)

        findBoss = None
        img = self._img_service.screenshot()
        results = self._ocr_service.ocr(img)
        # logger.info(f"results：{results}")
        findBossList = self._ocr_service.search_texts(results, rf"^{find_boss_name_reg}")
        # logger.info(f"findBossList：{findBossList}")
        if findBossList and len(findBossList) >= 2:
            sortedFindBossList = sorted(findBossList, key=lambda x: x.y1)
            # logger.info(f"sortedFindBossList：{sortedFindBossList}")
            for index, findBossTemp in enumerate(sortedFindBossList):
                # 第一个是输入框
                # if index == 0:
                if findBossTemp.y1 < search_tips_pos.y2:
                    continue
                if re.match(find_boss_name_reg, findBossTemp.text):
                    # logger.info(f"匹配坐标：{findBossTemp}")
                    findBoss = findBossTemp
                    break

        if not findBoss:
            self._control_service.esc()
            logger.warning("未找到目标boss")
            return False

        self._control_service.click(findBoss.x1, findBoss.y1)
        time.sleep(0.2)
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

            if bossName == BossNameEnum.Lorelei.value:
                self.lorelei_clock_adjust()

            time.sleep(1.2)  # 等站稳了再动

            if self._context.param_config.autoCombatBeta is True:
                if self.combat_system.resonators is None:
                    self.team_members_ocr()
                if self.combat_system.resonators is not None:
                    # 移动前检查，如 椿退出红椿状态
                    self.combat_system.exit_special_state(ScenarioEnum.BeforeGoingToBoss)

            def route_step_action(route_step_list: list[RouteStep] | None):
                if route_step_list is None:
                    return
                for _route_step in route_step_list:
                    if _route_step.mode == MoveMode.WALK:
                        if _route_step.steps is not None and _route_step.steps > 0:
                            self._control_service.forward_walk(
                                _route_step.steps, Direction.get_key(_route_step.direction))
                        elif _route_step.duration is not None and _route_step.duration > 0:
                            pass
                    elif _route_step.mode == MoveMode.RUN:
                        if _route_step.steps is not None and _route_step.steps > 0:
                            pass
                        elif _route_step.duration is not None and _route_step.duration > 0:
                            self._control_service.forward_run(
                                _route_step.duration, Direction.get_key(_route_step.direction))

            # 1 走/跑向boss
            fast_travel_routes = self._boss_info_service.get_fast_travel_routes()
            route_step_action(fast_travel_routes.get(bossName))

            # 2 点击重新挑战
            restart_params = self._boss_info_service.get_restart_params()
            if bossName in restart_params.keys():
                is_ocr_restart = False

                restart_param = restart_params.get(bossName)
                direction_key = Direction.get_key(restart_param.direction)

                # 需要原地查找boss相关的关键字
                # 首次 无需找关键字（有些boss左侧没有关键字可找） 或 关键字（击败等）未找到
                # 标记为需要循环前移查找，否则直奔boss
                if not restart_param.check_text or not self._ocr_service.find_text(restart_param.check_text):
                    is_ocr_restart = True

                if is_ocr_restart:
                    search_region = self.get_dialogue_region()
                    i = 0
                    while i < restart_param.cycle:
                        img = self._img_service.screenshot()
                        if restart_param.check_health_bar is True and BaseResonator.is_boss_health_bar_exist(img):
                            break

                        if restart_param.restart_text:
                            restart = self._ocr_service.find_text(restart_param.restart_text, None, search_region)
                            if not restart:
                                self._control_service.forward_walk(2)
                                i += 1
                                time.sleep(0.2)
                                continue
                            break

                        # 吸收与奖励重叠时
                        results = self._ocr_service.ocr(img, search_region)
                        absorption = self._ocr_service.search_text(results, "^吸收$")
                        receive_reward = self._ocr_service.search_text(results, r"^领取奖励$")
                        # 部分boss可以重新挑战
                        restart = self._ocr_service.search_text(results, r"^重新挑战$")
                        is_pick_up_echo = False
                        # 有吸收和领取奖励，吸收在下则滚动到下方
                        if absorption and receive_reward:
                            logger.debug(f"absorption: {absorption}, receive_reward: {receive_reward}")
                            if restart:
                                points = [absorption, receive_reward, restart]
                            else:
                                points = [absorption, receive_reward]
                            sorted_points = sorted(points, key=lambda x: x.y1)
                            absorption_index = 0
                            for index, point in enumerate(sorted_points):
                                if point.y1 == absorption.y1:
                                    absorption_index = index
                                    break
                            if absorption_index > 0:
                                for _ in range(absorption_index):
                                    logger.info("向下滚动")
                                    self._control_service.scroll_mouse(-1)
                                    time.sleep(0.5)
                            is_pick_up_echo = True
                        if absorption and not receive_reward and not restart:
                            is_pick_up_echo = True
                        if is_pick_up_echo:
                            self._control_service.pick_up()
                            time.sleep(0.5)
                            # 防止误点领取奖励
                            receive_reward_tips = self._ocr_service.find_text(r"领取奖励需消耗")
                            if receive_reward_tips:
                                self._control_service.esc()
                                time.sleep(0.3)

                        if not restart:
                            self._control_service.forward_walk(2, direction_key)
                            i += 1
                            continue
                        time.sleep(0.6)
                        self._control_service.scroll_mouse(-1)
                        time.sleep(0.6)
                        logger.info("重新挑战")
                        self._control_service.pick_up()
                        time.sleep(3.0)
                        break

                # 3 走向boss刷新点
                after_restart_routes = self._boss_info_service.get_after_restart_routes()
                route_step_action(after_restart_routes.get(bossName))

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
        if not self._ocr_service.wait_text(r"^(终端|Terminal|教程百科|Tutorials)$", timeout=5):
            self._control_service.esc()
            return
        # 进入时钟
        dpt = DynamicPointTransformer(self._window_service.get_client_wh())
        terminal_clock = dpt.transform((915, 686), AlignEnum.BUTTON_RIGHT)
        self._control_service.click(*terminal_clock)
        time.sleep(2)
        tomorrow = self._ocr_service.wait_text(r"^次日$", timeout=5)
        if not tomorrow:
            logger.warning("未找到次日")
            self._control_service.esc()
            return
        self.click_position(tomorrow)
        time.sleep(1)
        # 右侧下一个时间
        w, h = self._window_service.get_client_wh()
        next_clock_16_9 = (1180, 360)  # x随宽度等比放大，y为高度一半，不固定
        next_clock = (int(w * next_clock_16_9[0] / 1280), h // 2)
        self._control_service.click(*next_clock)
        time.sleep(0.3)
        self._control_service.click(*next_clock)
        time.sleep(0.3)
        self._control_service.click(*next_clock)
        time.sleep(0.3)

        confirm_text = self._ocr_service.find_text("确定")
        self.click_position(confirm_text)
        time.sleep(2)
        self._ocr_service.wait_text("时间", timeout=10)
        time.sleep(1)
        self._control_service.esc()
        self._ocr_service.wait_text(r"^(终端|Terminal|教程百科|Tutorials)$", timeout=5)
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
            time.sleep(0.2)
        # position = Position.build(325, 190, 690, 330)
        if self._ocr_service.wait_text("选择复苏物品", timeout=2):
            logger.debug("检测到角色需要复苏")
            self._info.needHeal = True
            self._control_service.esc()
            time.sleep(1.2)

    def click_position(self, position: Position):
        self._control_service.click(*position.center)

    def _need_retry(self):
        return (len(self._config.TargetBoss) == 1 and
                self._config.TargetBoss[0] in [
                    BossNameEnum.Dreamless.value,
                    BossNameEnum.Jue.value,
                    BossNameEnum.Hecate.value,
                    BossNameEnum.Fleurdelys.value,
                    BossNameEnum.ThrenodianLeviathan.value,
                    BossNameEnum.Sigillum.value,
                    BossNameEnum.SeedOfIllusoryOrigin.value,
                    BossNameEnum.Denia.value,
                    BossNameEnum.NightmareAdamSmasherLimitedTime.value,
                    BossNameEnum.NightmareAdamSmasher.value,
                ]
                )

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
            text_result = self._ocr_service.search_text(results, r"特征码|^特征.+\d{5,}")
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
        return True

    def _od_search(self, img, search_type: str):
        if search_type == "boss":
            return self._od_service.search_echo(img)
        elif search_type == "reward":
            return self._od_service.search_reward(img)
        else:
            raise NotImplemented("未实现的搜索方式")

    def search_echo(self):
        # img = self._img_service.screenshot()
        # search_region = DynamicPosition(
        #     rate=(
        #         788 / 1280,
        #         300 / 720,
        #         1100 / 1280,
        #         560 / 720,
        #     ),
        # )
        # absorb = self._ocr_service.find_text("^吸收$", img, search_region)
        # if absorb:
        #     self._control_service.pick_up()
        #     return

        start_time = time.monotonic()
        max_search_seconds = 4.0
        min_search_seconds = 2.0
        last_echo_box = None
        max_tolerance = 1
        tolerance = max_tolerance
        while time.monotonic() - start_time < max_search_seconds:
            self._control_service.pick_up()
            img = self._img_service.screenshot()
            echo_box = self._od_service.search_echo(img)
            if echo_box:
                last_echo_box = echo_box
                tolerance = min(max_tolerance, tolerance + 1)
            elif last_echo_box is not None and tolerance > 0:
                echo_box = last_echo_box
                tolerance -= 1

            if echo_box is None:
                if time.monotonic() - start_time > min_search_seconds:
                    logger.info("未发现声骸")
                    return
                time.sleep(0.3)
                continue

            # 前往声骸
            window_width = self._window_service.get_client_wh()[0]
            # role_width = int(window_width * 50 / 1280)
            echo_x1, echo_y1, echo_width, echo_height = echo_box
            echo_x2 = echo_x1 + echo_width
            # echo_y2 = echo_y1 + echo_height
            half_window_width = window_width // 2
            # half_role_width = role_width // 2

            # echo_search_config_mapping = {"角": (8, 4, 4, 7)}

            if echo_x1 * 0.9 > half_window_width:  # 声骸中在角色右侧
                logger.info("发现声骸 向右移动")
                self._control_service.right(0.1)
                time.sleep(0.05)
            elif echo_x2 * 1.1 < half_window_width:  # 声骸中在角色左侧
                logger.info("发现声骸 向左移动")
                self._control_service.left(0.1)
                time.sleep(0.05)
            else:
                logger.info("发现声骸 向前移动")
                # self._control_service.up(0.1)
                # time.sleep(0.01)
                for _ in range(5):
                    self._control_service.up(0.1)
                    self._control_service.pick_up(0.001)
                    time.sleep(0.05)
                time.sleep(0.5)
            self._control_service.pick_up()

    def team_members_ocr(self, team_pos=None):
        if team_pos is None:
            self._control_service.esc()
            time.sleep(1.5)
            self._ocr_service.wait_text(["^确认离开", "^确认$", "^编队$", "^终端$", "^活动$"])
            time.sleep(0.8)
            img = self._img_service.screenshot()
            ocr_results = self._ocr_service.ocr(img)
            confirm_leave_pos = self._ocr_service.search_text(ocr_results, "^确认离开")
            confirm_pos = self._ocr_service.search_text(ocr_results, "^确认$")
            if confirm_leave_pos and confirm_pos:
                self._control_service.click(*confirm_pos.center)
                time.sleep(3)
                self.wait_home()
                time.sleep(2)
                self._info.in_dungeon = False
                self._info.status = Status.idle
                now = datetime.now()
                self._info.lastFightTime = now + timedelta(seconds=self._config.MaxFightTime / 2)

                self._control_service.esc()
                time.sleep(1.5)

        team_pos = self._ocr_service.wait_text("^编队$")
        if team_pos:
            logger.info("识别编队")
            time.sleep(0.6)
            self._control_service.click(*team_pos.center)
            time.sleep(1)
            quick_setup_pos = self._ocr_service.wait_text("^快速编队$")
            if quick_setup_pos:
                img = self._img_service.screenshot()
                # ocr_results = self._ocr_service.ocr(img)
                ocr_results = self._ocr_service.query(img, resize=False)

                # 识别编队
                members_info: list[list] = [
                    # name text is_exist
                    [None, None, None], [None, None, None], [None, None, None]
                ]
                team_members = [ResonatorNameEnum.none.value for _ in range(3)]

                # 编队角色名右侧一点黑色背景上取点
                member_points = [
                    AnchorPoint(433, 569, Align.Center | Align.Middle),
                    AnchorPoint(810, 569, Align.Center | Align.Middle),
                    AnchorPoint(1187, 569, Align.Center | Align.Middle),
                ]
                member_boxes = [
                    AnchorBBox(
                        AnchorPoint(200, 550, Align.Center | Align.Middle),
                        AnchorPoint(510, 590, Align.Center | Align.Middle),
                    ),
                    AnchorBBox(
                        AnchorPoint(576, 550, Align.Center | Align.Middle),
                        AnchorPoint(888, 590, Align.Center | Align.Middle),
                    ),
                    AnchorBBox(
                        AnchorPoint(954, 550, Align.Center | Align.Middle),
                        AnchorPoint(1280, 590, Align.Center | Align.Middle),
                    ),
                ]
                scaler = self._window_service.scaler
                member_points = [scaler.as_point(p) for p in member_points]
                member_boxes = [scaler.as_bbox(box) for box in member_boxes]

                color_matches = []
                for p in member_points:
                    rule = ColorRule().points(p).colors(Color.bgr(22, 18, 13), 30)
                    color_matches.append(ColorMatch(scaler).rules(rule))

                for i, match in enumerate(color_matches):
                    if match.match(img):
                        members_info[i][2] = True

                for text_box in ocr_results.results:
                    if text_box.x2 < member_boxes[0].x1:
                        continue
                    if text_box.y2 < member_boxes[0].y1 or text_box.y2 > member_boxes[0].y2:
                        continue
                    for i, member_bbox in enumerate(member_boxes):
                        if not member_bbox.contains_bbox(text_box):
                            continue
                        if not members_info[i][2]:
                            continue
                        members_info[i][1] = text_box
                        # 通过名称匹配这个位置的角色名
                        enum_obj = ResonatorNameEnum.get_enum_by_ocr_text(text_box.text)
                        # 角色名都对不上，默认为主角
                        members_info[i][0] = enum_obj.value if enum_obj else ResonatorNameEnum.rover.value
                        team_members[i] = members_info[i][0]
                        # logger.debug(f"team_members[{i}]: {team_members[i]}")

                # logger.debug(f"members_info: {members_info}")
                # logger.debug(f"team_members: {team_members}")

                self.combat_system.set_resonators(team_members)
                self._control_service.esc()
                time.sleep(3)
            else:
                logger.info("编队已锁定")
                w, h = self._window_service.get_client_wh()

                def _find_pos(pos_list):
                    if not pos_list:
                        return None
                    # logger.info(f"pos_list: {pos_list}")
                    if isinstance(pos_list, Position):
                        pos_list = [pos_list]
                    for pos in pos_list:
                        # logger.info(f"pos: {pos}")
                        if pos.x1 > w * 580 // 1600:
                            return pos
                    return None

                img = self._img_service.screenshot()
                results = self._ocr_service.ocr(img)
                map_pos_list = self._ocr_service.search_texts(results, "^(地图|Map)$")
                map_pos = _find_pos(map_pos_list)
                if not map_pos:
                    next_pos = (1197, 350)
                    dpt = DynamicPointTransformer(img)
                    next_pos = dpt.transform(next_pos, AlignEnum.CENTER_RIGHT)
                    self._control_service.click(*next_pos)
                    time.sleep(0.5)
                    map_pos_list = self._ocr_service.wait_text("^(地图|Map)$")
                    map_pos = _find_pos(map_pos_list)

                if map_pos:
                    time.sleep(0.3)
                    self._control_service.click(*map_pos.center)
                    self._transfer_to_heal(skip_map=True)
                    return
                else:
                    logger.info("未找到地图")

    def get_dialogue_region(self) -> Position:
        dpt = DynamicPointTransformer(self._window_service.get_client_wh())
        search_region = [
            *dpt.transform((788, 280), AlignEnum.CENTER),
            *dpt.transform((1100, 560), AlignEnum.CENTER),
        ]
        return Position.build(*search_region)
