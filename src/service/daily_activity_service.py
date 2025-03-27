import logging
import re
import time
from abc import ABC
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field

from src.core.contexts import Context, Status
from src.core.interface import ControlService, OCRService, ImgService, WindowService, ODService
from src.core.pages import Page, ConditionalAction
from src.core.regions import Position, TextPosition
from src.service.page_event_service import PageEventAbstractService

logger = logging.getLogger(__name__)


class InstanceTypeEnum(Enum):
    Boss = "Boss",
    ForgeryChallenge = "ForgeryChallenge"  # 凝素领域
    EchoMaterials = "EchoMaterials"  # 无音清剿


class DailyActivityContext(BaseModel):
    first_action: bool = Field(True)
    # job
    job_stop: bool = Field(False)
    ## 每日活跃度任务
    job_daily_activity: bool = Field(True, title="是否需要做每日活跃度任务")
    job_daily_activity_finished: bool = Field(False, title="每日活跃度任务是否完成")
    job_daily_activity_finished_success: bool = Field(False, title="每日活跃度任务是成功完成还是失败完成")
    ## 刷体力
    job_consume_waveplate: bool = Field(True, title="是否需要刷体力")
    job_consume_waveplate_finished: bool = Field(False, title="刷体力任务是否完成")
    job_consume_waveplate_finished_success: bool = Field(False, title="刷体力任务是成功完成还是失败完成")
    double_drop_chances_remaining: int = Field(-1, title="是否有双倍材料活动")

    # runtime param, 从游戏中识别获得
    waveplate: int = Field(-1, title="体力值|waveplate")

    double_Weapon_and_SkillMaterials: bool = Field(False, title="是否有双倍武器技能材料")
    double_Weapon_and_SkillMaterials_times: bool = Field(-1, title="双倍武器技能材料剩余次数")

    # config param，由页面配置
    select_Weapon_and_SkillMaterials: bool = Field(True, title="是否勾选刷武器及技能材料")
    # sub_select_Weapon_and_SkillMaterials: str | None = Field("Broadblade", title="刷哪种武器及技能材料")
    sub_select_Weapon_and_SkillMaterials: str | None = Field("Sword", title="刷哪种武器及技能材料")

    select_EchoMaterials: bool = Field(False, title="是否勾选刷声骸材料")
    sub_select_EchoMaterials: str | None = Field(None, title="刷哪种声骸材料")

    # fight param
    ## 两个战斗时间参数由战斗连招函数赋值
    fight_start_time: datetime = Field(default_factory=datetime.now, title="战斗开始时间")
    fight_last_time: datetime = Field(default_factory=datetime.now, title="最近检测到战斗时间")
    ## 连招函数赋值：战斗中
    fight_status: Status = Field(Status.idle, title="是否在战斗中")
    ## 进副本时赋值
    fight_instance_type: InstanceTypeEnum = Field(
        InstanceTypeEnum.Boss, title="是否在副本里战斗", description="独立副本离开方式不同于大世界")
    fight_count: int = Field(0)
    fight_in_instance: bool = Field(False)
    # fight_need_search_reward: bool = Field(False)


class BoxEnum(Enum):
    DESC = "desc"
    WEAPON = "weapon"
    PROCEED = "Proceed"


class DailyActivityServiceImpl(PageEventAbstractService, ABC):
    """每日活动"""

    def __init__(self, context: Context, window_service: WindowService, img_service: ImgService,
                 ocr_service: OCRService, control_service: ControlService, od_service: ODService):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__(context, window_service, img_service, ocr_service, control_service, od_service)
        self._where_am_i_esc_check_pages: list[Page] = [
            self._UI_ESC_Terminal,
            self._UI_ESC_LeaveInstance,
        ]

        self._boss_pages: list[Page] = []
        self._general_pages: list[Page] = []
        self._dreamless_pages: list[Page] = []

        self._daily_activity_pages: list[Page] = []
        self._build_daily_activity_pages()

        self._daily_activity_pages = self._daily_activity_pages + self._general_pages + self._boss_pages + self._dreamless_pages

        self._conditional_actions: list[ConditionalAction] = []

        self._ctx = DailyActivityContext()

    def execute(self, **kwargs):
        start_time = datetime.now()
        logger.debug("任务开始: %s", start_time)

        while True:
            if datetime.now() - start_time > timedelta(seconds=3):
                self._control_service.activate()

            src_img = self._img_service.screenshot()
            img = self._img_service.resize(src_img)
            ocr_results = self._ocr_service.ocr(img)
            # self._ocr_service.print_ocr_result(ocr_results)
            actioned = False
            for page in self.get_pages():
                if not page.is_match(src_img, img, ocr_results):
                    continue
                logger.info("当前页面：%s", page.name)
                page.action(page.matchPositions)
                actioned = True
                break
            if not actioned:
                self._run_conditional_actions()

            if self._ctx.job_stop:
                logger.info("任务终止")
                break
            finished = []
            if self._ctx.job_daily_activity:
                logger.debug("每日活跃度任务%s", "已完成" if self._ctx.job_daily_activity_finished else "未完成")
                finished.append(self._ctx.job_daily_activity_finished)
            if self._ctx.job_consume_waveplate:
                logger.debug("刷体力任务%s", "已完成" if self._ctx.job_consume_waveplate_finished else "未完成")
                finished.append(self._ctx.job_consume_waveplate_finished)
            if finished and all(finished):
                end_time = datetime.now()
                logger.info("任务已全部结束, %s, 耗时: %ss", end_time, (end_time - start_time).total_seconds)
                break

        return True

    # def _run(self, pages, conditional_actions, src_img=None, img=None, ocr_results=None):
    #     if src_img is None:
    #         src_img = self._img_service.screenshot()
    #         img = self._img_service.resize(src_img)
    #         ocr_results = self._ocr_service.ocr(img)
    #     self._ocr_service.print_ocr_result(ocr_results)
    #     for page in pages:
    #         if not page.is_match(src_img, img, ocr_results):
    #             continue
    #         logger.info("当前页面：%s", page.name)
    #         page.action(page.matchPositions)
    #     for conditionalAction in conditional_actions:
    #         if not conditionalAction():
    #             continue
    #         logger.info("当前条件操作: %s", conditionalAction.name)
    #         conditionalAction.action()

    def get_pages(self) -> list[Page]:
        return self._daily_activity_pages

    def get_conditional_actions(self) -> list[ConditionalAction]:
        return self._conditional_actions

    def _get_ocr_results(self):
        src_img = self._img_service.screenshot()
        img = self._img_service.resize(src_img)
        ocr_results = self._ocr_service.ocr(img)
        return src_img, img, ocr_results

    def _build_UI_F2_Guidebook_RecurringChallenges_action(self):

        def action(positions: dict[str, Position]):
            if self._ctx.job_consume_waveplate_finished:
                src_img = self._img_service.screenshot()
                img = self._img_service.resize(src_img)
                position = self._img_service.match_template(img, "UI_F2_Guidebook_Activity.png")
                logger.debug("match template: %s", position)
                if not position:
                    logger.warning("活跃度")
                    self._control_service.esc()
                    time.sleep(1)
                    return True
                self._control_service.click(*position.center)
                time.sleep(1)
                return True

            if self._ctx.select_Weapon_and_SkillMaterials:
                logger.info("刷武器技能材料")
                position = positions.get("凝素领域|Forgery Challenge")
                self._control_service.click(*position.center)
                time.sleep(0.2)

                position = TextPosition.get(positions, "今日剩余双倍奖励次数|Double Drop Chances Remaining")
                if position:
                    logger.debug(position.text)
                    self._ctx.double_Weapon_and_SkillMaterials = True
                    match = re.search(r"(\d)/\d", position.text.strip())
                    remaining = match.group(1)  # "2/3"
                    logger.debug("剩余双倍次数: %s", remaining)
                    self._ctx.double_drop_chances_remaining = remaining

                position = TextPosition.get(positions, "体力值|waveplate")
                if position: # 可能是 88/240 或 88
                    logger.debug(position.text)
                    match = re.search(r"(\d{1,3})/\d{2}0", position.text.strip())
                    waveplate = match.group(1)  # "100/240"
                    logger.debug("剩余体力: %s", waveplate)
                    self._ctx.waveplate = waveplate

                src_img = self._img_service.screenshot()
                img = self._img_service.resize(src_img)
                ocr_results = self._ocr_service.ocr(img)
                self._ocr_service.print_ocr_result(ocr_results)

                desc_regex = r"^(?:武器及技能材料|Weapon\s*and\s*Skill\s*Materials:)"
                weapon_position_list = self._ocr_service.search_texts(ocr_results, desc_regex)
                logger.debug("weapon_position_list: %s", weapon_position_list)
                x, y = weapon_position_list[1].random

                weapons = {
                    "Sword": r"迅刀$|^Sword$",
                    "Rectifier": r"音感仪$|^Rectifier$",
                    "Broadblade": r"长刃$|^Broadblade$",
                    "Gauntlets": r"臂铠$|^Gauntlets$",
                    "Pistols": r"佩枪$|^Pistols$",
                }
                weapon_regex = "|".join(weapons.values())
                proceed_regex = r"^(前往|Proceed)$"
                select_weapon_regex = weapons[self._ctx.sub_select_Weapon_and_SkillMaterials]
                w, h = self._window_service.get_client_wh()

                find_proceed = False
                for i_scroll in range(5):
                    if find_proceed:
                        break
                    self._control_service.click(x, y)
                    time.sleep(0.2)
                    if i_scroll == 0:  # 翻到最底下，查找
                        self._control_service.scroll_mouse(-100, x, y)
                        time.sleep(3)
                    else:  # 向上翻，查找
                        self._control_service.scroll_mouse(30, x, y)
                        time.sleep(2)
                    src_img = self._img_service.screenshot()
                    img = self._img_service.resize(src_img)
                    ocr_results = self._ocr_service.ocr(img)
                    self._ocr_service.print_ocr_result(ocr_results)

                    filter_list = []
                    for ocr_result in ocr_results:
                        logger.debug("re match ocr result: %s", ocr_result)
                        if re.search(proceed_regex, ocr_result.text) and ocr_result.x1 > w // 3:
                            filter_list.append((ocr_result, BoxEnum.PROCEED, ""))
                        else:
                            if re.search(desc_regex, ocr_result.text):
                                filter_list.append((ocr_result, BoxEnum.DESC, ""))
                            if weapon_match := re.search(weapon_regex, ocr_result.text):
                                logger.debug("append: %s", ocr_result.text)
                                filter_list.append((ocr_result, BoxEnum.WEAPON, weapon_match.group(0)))
                    logger.debug("filter_list: %s", filter_list)
                    sorted_filter_list = sorted(filter_list, key=lambda p: p[0].y2)
                    count_desc = 0
                    for i in range(len(sorted_filter_list)):
                        element = sorted_filter_list[i]
                        # 跳过第二个DESC之前的元素
                        if count_desc < 1:
                            if element[1] == BoxEnum.DESC:
                                count_desc += 1
                            continue
                        elif count_desc == 1:
                            if element[1] != BoxEnum.DESC:
                                continue
                            count_desc += 1
                        # 从第二个武器开始
                        if element[1] != BoxEnum.WEAPON:
                            continue
                        # 找到选择刷取的武器
                        if not re.match(select_weapon_regex, element[2]):
                            logger.debug("select: %s, cur: %s, match: False", select_weapon_regex, element[2])
                            continue
                        else:
                            logger.debug("select: %s, cur: %s, match: True", select_weapon_regex, element[2])
                        # 找到前往
                        for k in range(2):  # 中文/英文 前往/Proceed 在武器的前一个或两个位置
                            proceed_element = sorted_filter_list[i - 1 - k]
                            if proceed_element[1] != BoxEnum.PROCEED:
                                logger.debug("不是前往的坐标: %s", proceed_element[0])
                                continue
                            logger.debug("找到前往的坐标: %s", proceed_element[0])
                            self._control_service.click(*proceed_element[0].center)
                            time.sleep(2)
                            position = self._ocr_service.wait_text(r"^(快速旅行|Fast\s*Travel)$")
                            time.sleep(1)
                            self._control_service.click(*position.center)
                            time.sleep(2.5)
                            self.wait_home()
                            time.sleep(1.5)
                            self._control_service.forward_run(0.8)
                            time.sleep(1)

                            # TODO 先硬编码有空再搞
                            self._control_service.pick_up()
                            time.sleep(5)
                            position = self._ocr_service.wait_text(
                                r"^(单人挑战|Solo\s*Challenge)$", timeout=10, wait_time=1.0)
                            time.sleep(0.5)
                            self._control_service.click(*position.center)
                            time.sleep(1)
                            position = self._ocr_service.wait_text(r"^(开启挑战|StartChallenge|结晶波片不足.*)$", wait_time=1.0)
                            time.sleep(0.5)
                            if re.match(r"^(结晶波片不足.*)$", position.text):
                                self._control_service.esc()
                                time.sleep(2.5)
                                self._control_service.esc()
                                time.sleep(2)

                                if self._ctx.job_consume_waveplate_finished:
                                    self._ctx.job_stop = True
                                self._ctx.job_consume_waveplate_finished = True
                                return True
                            self._control_service.click(*position.center)
                            time.sleep(3)
                            self._ocr_service.wait_text("开启挑战", timeout=10, wait_time=1.0)
                            time.sleep(2)
                            self._control_service.camera_reset()
                            time.sleep(0.5)
                            self._control_service.forward_run(1)
                            i = 0
                            while i < 8 and not self._ocr_service.find_text("^启动$"):
                                self._control_service.forward_walk(3)
                                i += 1
                            self._control_service.pick_up()
                            time.sleep(3)

                            self._ctx.fight_instance_type = InstanceTypeEnum.ForgeryChallenge
                            self._ctx.fight_in_instance = True
                            self._ctx.fight_start_time = datetime.now()
                            self._ctx.fight_last_time = datetime.now()

                            find_proceed = True
                            break
            elif self._ctx.select_EchoMaterials:
                logger.info("刷声骸材料")
                raise NotImplementedError("未实现的刷取")
                pass
            else:
                raise NotImplementedError("未实现的刷取")

        return action

    def _build_daily_activity_pages(self):

        def _UI_F2_Guidebook_to_RecurringChallenges_action(positions: dict[str, Position]):
            """ 前往周期挑战(刷体力) """
            src_img = self._img_service.screenshot()
            img = self._img_service.resize(src_img)
            position = self._img_service.match_template(img, "UI_F2_Guidebook_RecurringChallenges.png")
            logger.debug("match template: %s", position)
            if not position:
                logger.warning("未找到周期挑战")
                self._control_service.esc()
                time.sleep(1)
                return False
            self._control_service.click(*position.center)
            time.sleep(0.5)
            return True

        def _UI_F2_Guidebook_Activity_action(positions: dict[str, Position]):
            """ 领取每日活跃度奖励 """

            if not self._ctx.job_daily_activity_finished:
                # 领取活跃度
                claim_match_name = "领取|Claim"
                if positions.get(claim_match_name):
                    text_match = self._UI_F2_Guidebook_Activity.get_text_match_by_name(claim_match_name)
                    for _ in range(20):
                        src_img, img, ocr_results = self._get_ocr_results()
                        if ocr_results is None:
                            time.sleep(0.5)
                            continue
                        self._ocr_service.print_ocr_result(ocr_results)
                        position = self._UI_F2_Guidebook_Activity.text_match(text_match, src_img, img, ocr_results)
                        logger.debug("%s position: %s", claim_match_name, position)
                        if not position:
                            break
                        self._control_service.click(*position.random)
                        time.sleep(0.5)

                # 领取活跃度100奖励
                src_img, img, ocr_results = self._get_ocr_results()
                activity_pts = self._ocr_service.search_texts(ocr_results, r"^1\d0$")
                logger.debug("activity pts: %s", activity_pts)
                w, h = self._window_service.get_client_wh()
                if len(activity_pts) >= 2:
                    activity_pts_sorted = sorted(activity_pts, key=lambda p: p.x1, reverse=True)
                    position = activity_pts_sorted[0]
                    if not (position.text == "100" and position.x1 > 0.6 * w):
                        raise Exception(f"活跃度包含未知的100: {activity_pts_sorted}")
                    pts100 = (position.x1 + position.x2) // 2, position.y1 - (position.x2 - position.x1)
                    self._control_service.click(*pts100)
                    self._ctx.job_daily_activity_finished = True  # 每日活跃度任务完成了
                    # self._ctx.job_daily_activity_finished_success = True
                    time.sleep(1)
                    self._ocr_service.wait_text(
                        r"^(600|点击空白区域关闭|Tap\s*the\s*blank\s*area\s*to\s*close)$", wait_time=0.5)
                    # self._control_service.click(*position.center)
                    time.sleep(1)
                    self._control_service.click(*pts100)
                    time.sleep(1)

            # 前往周期挑战(刷体力)
            if self._ctx.job_consume_waveplate and not self._ctx.job_consume_waveplate_finished:
                _UI_F2_Guidebook_to_RecurringChallenges_action({})
            else:
                self._control_service.esc()
                time.sleep(1.5)
                # self._ctx.fight_status = Status.idle
                # self._ctx.fight_start_time = datetime.now()
                self._info.status = Status.idle
                self._info.fightTime = datetime.now()
                self.transfer()

            return True

        # src_img, img, ocr_results = self._get_ocr_results()
        # # pages
        # ## implement/override action
        # page = self._UI_F2_Guidebook_Activity
        # if page.is_match(src_img, img, ocr_results):
        #     _UI_F2_Guidebook_Activity_action(page.matchPositions)

        self._daily_activity_pages.append(self.build_UI_F2_Guidebook_Activity(_UI_F2_Guidebook_Activity_action))
        self._daily_activity_pages.append(self.build_UI_F2_Guidebook_RecurringChallenges(
            self._build_UI_F2_Guidebook_RecurringChallenges_action()))  # 太长了，单独放到外面写
        self._daily_activity_pages.append(self.build_UI_F2_Guidebook_PathOfGrowth(
            _UI_F2_Guidebook_to_RecurringChallenges_action))
        self._daily_activity_pages.append(self.build_UI_F2_Guidebook_EchoHunting(
            _UI_F2_Guidebook_to_RecurringChallenges_action))
        self._daily_activity_pages.append(self.build_UI_F2_Guidebook_Milestones(
            _UI_F2_Guidebook_to_RecurringChallenges_action))
        ## default action
        self._daily_activity_pages.append(self._UI_ESC_Terminal)
        self._daily_activity_pages.append(self._Reward_LuniteSubscriptionReward)
        self._daily_activity_pages.append(self._F_EnterForgeryChallenge)
        self._daily_activity_pages.append(self._Challenge_EnterSoloChallenge)

        def _Reward_ClaimRewards_action(positions: dict[str, Position]):
            logger.debug("领取奖励")
            position = positions.get("确认|Confirm", positions.get("单倍领取|Claim"))
            self._control_service.click(*position.center)
            time.sleep(2)
            position = self._ocr_service.wait_text("退出副本", wait_time=0.39)
            time.sleep(0.5)
            self._control_service.click(*position.center)
            time.sleep(3)

            self._ctx.fight_status = Status.idle
            self._ctx.fight_start_time = datetime.now()
            self._ctx.fight_last_time = datetime.now()
            self._ctx.fight_count += 1
            self._ctx.fight_in_instance = False
            return True

        self._daily_activity_pages.append(self.build_Reward_ClaimRewards_ForgeryChallenge(
            _Reward_ClaimRewards_action
        ))
        self._daily_activity_pages.append(self.build_Reward_ClaimRewards_TacetSuppression(
            _Reward_ClaimRewards_action
        ))

        # def _build_pages(self):

        unconscious_action_page = self.build_Fight_Unconscious()
        self._boss_pages.append(unconscious_action_page)

        voice_string_interaction_page = self.build_Boss_Crownless_ResonanceCord()
        self._boss_pages.append(voice_string_interaction_page)

        # def _build_general_pages(self):

        driver_version_is_too_old_page = self.build_Confirm_DriverVersion()
        self._general_pages.append(driver_version_is_too_old_page)

        absorption_page = self.build_Fight_Absorption()
        self._general_pages.append(absorption_page)

        select_recovery_items_page = self.build_Fight_select_recovery_items()
        self._general_pages.append(select_recovery_items_page)

        # terminal_page = self.build_UI_ESC_Terminal()
        # self._general_pages.append(terminal_page)

        def fight_action(positions: dict[str, Position]):
            if self._ctx.fight_status == Status.idle:  # 空闲进入战斗，即为新一轮战斗
                self._ctx.fight_start_time = datetime.now()
                # self._info.fightCount += 1
                # self._info.needAbsorption = True
            self.release_skills()
            self._ctx.fight_status = Status.fight
            self._ctx.fight_last_time = datetime.now()
            return True

        fight_page = self.build_Fight(fight_action)
        self._general_pages.append(fight_page)

        # _Reward_LuniteSubscriptionReward = self.build_Reward_LuniteSubscriptionReward()
        # self._general_pages.append(_Reward_LuniteSubscriptionReward)

        supplement_crystal_wave_page = self.build_Replenish_Waveplate()
        self._general_pages.append(supplement_crystal_wave_page)

        # receive_rewards_page = self.build_receive_rewards()
        # self._general_pages.append(receive_rewards_page)

        blank_area_page = self.build_blank_area()
        self._general_pages.append(blank_area_page)

        # def _build_dreamless_pages(self):
        enter_page_dreamless = self.build_Boss_Dreamless_Enter()
        self._dreamless_pages.append(enter_page_dreamless)

        enter_page_jue = self.build_Boss_Jue_Enter()
        self._dreamless_pages.append(enter_page_jue)

        enter_page_hecate = self.build_Boss_Hecate_Enter()
        self._dreamless_pages.append(enter_page_hecate)

        recommended_level_page = self.build_Boss_RecommendedLevel()
        self._dreamless_pages.append(recommended_level_page)

        start_challenge_page = self.build_UI_Boss_StartChallenge()
        self._dreamless_pages.append(start_challenge_page)

        crystal_wave_page = self.build_Waveplate_NotEnough()
        self._dreamless_pages.append(crystal_wave_page)

    def _run_conditional_actions(self):
        if self._ctx.first_action:
            self._ctx.first_action = False
            self._control_service.guide_book()
            time.sleep(2)

        if (
                # self._info.needAbsorption  # 未吸收
                # # 空闲时间未超过最大空闲时间 且 空闲时间超过最大空闲时间的一半
                # and
                self._config.MaxIdleTime / 2 < (
                datetime.now() - self._ctx.fight_last_time).seconds < self._config.MaxIdleTime

                and self._ctx.fight_status == Status.fight

        ):
            logger.debug("战斗结束后5-10s-搜索声骸/奖励")
            self.search_reward_action()
            self._check_heal()
            return True

        if (
                # not self._info.in_dungeon and
                not self._ctx.fight_in_instance and
                (datetime.now() - self._ctx.fight_last_time).seconds > self._config.MaxIdleTime
        ):
            logger.debug("大世界-战斗结束后10s-传送去往下一个boss")
            self._ctx.fight_status = Status.idle
            # return self.transfer()
            self._control_service.guide_book()
            time.sleep(2)
            return True

        if (
                # not self._info.in_dungeon and
                not self._ctx.fight_in_instance and
                (datetime.now() - self._ctx.fight_start_time).seconds > self._config.MaxFightTime
        ):
            logger.debug("大世界-战斗开始后超过120s-不打了，传送去往下一个boss")
            self._ctx.fight_status = Status.idle
            self._ctx.fight_start_time = datetime.now()  # 重置开始战斗时间
            # return self.transfer()
            self._control_service.guide_book()
            time.sleep(2)
            return True

        if (
                # self._info.in_dungeon and
                self._ctx.fight_in_instance and
                (datetime.now() - self._ctx.fight_last_time).seconds > self._config.MaxIdleTime
        ):
            logger.debug("副本内-战斗结束后10s-搜索声骸/奖励，ESC离开/重新挑战")
            self.search_reward_action()
            self._check_heal()
            self._control_service.esc()
            time.sleep(1)
            self._ctx.fight_last_time = datetime.now() # 重置最后战斗时间
            return True
        time.sleep(0.1)
        return True
