import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any
from zoneinfo import ZoneInfo

from packaging.version import Version

logger = logging.getLogger(__name__)


class ActivityStatus(Enum):
    """
    活动状态
    """

    DISABLED = auto()

    UPCOMING = auto()

    RUNNING = auto()

    ENDED = auto()


@dataclass(slots=True, frozen=True)
class ActivityTime:
    """
    活动时间配置
    """

    start_time: datetime

    end_time: datetime

    timezone: str = "Asia/Shanghai"

    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    def normalize(self) -> tuple[datetime, datetime]:
        """
        统一转为带时区时间
        """

        tz = self.tzinfo()

        start = self.start_time
        end = self.end_time

        if start.tzinfo is None:
            start = start.replace(tzinfo=tz)

        if end.tzinfo is None:
            end = end.replace(tzinfo=tz)

        return start, end

    def get_status(
            self,
            now: datetime | None = None,
    ) -> ActivityStatus:

        start, end = self.normalize()

        if now is None:
            now = datetime.now(tz=start.tzinfo)

        elif now.tzinfo is None:
            now = now.replace(tzinfo=start.tzinfo)

        if now < start:
            return ActivityStatus.UPCOMING

        if now > end:
            return ActivityStatus.ENDED

        return ActivityStatus.RUNNING

    def contains(
            self,
            now: datetime | None = None,
    ) -> bool:

        return self.get_status(now) == ActivityStatus.RUNNING


@dataclass(slots=True)
class Activity:
    """
    活动定义
    """

    # 唯一ID
    id: str

    # 显示名称
    name: str

    # 是否启用
    enabled: bool = True

    # 区服活动时间
    #
    # 示例:
    # {
    #     "cn": ActivityTime(...),
    #     "global": ActivityTime(...),
    # }
    #
    server_times: dict[str, ActivityTime] = field(default_factory=dict)

    # 最低支持版本
    min_game_version: str | None = None

    # 最高支持版本
    max_game_version: str | None = None

    # 扩展字段
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_time(
            self,
            server: str,
    ) -> ActivityTime | None:

        return self.server_times.get(server)

    def is_supported_version(
            self,
            version: str | Version,
    ) -> bool:

        if not isinstance(version, Version):
            version = Version(version)

        if self.min_game_version:
            if version < Version(self.min_game_version):
                return False

        if self.max_game_version:
            if version > Version(self.max_game_version):
                return False

        return True

    def get_status(
            self,
            server: str,
            now: datetime | None = None,
            game_version: str | Version | None = None,
    ) -> ActivityStatus:

        if not self.enabled:
            return ActivityStatus.DISABLED

        if game_version is not None:
            if not self.is_supported_version(game_version):
                return ActivityStatus.DISABLED

        activity_time = self.get_time(server)

        if activity_time is None:
            return ActivityStatus.DISABLED

        return activity_time.get_status(now)

    def is_available(
            self,
            server: str,
            now: datetime | None = None,
            game_version: str | Version | None = None,
    ) -> bool:

        return (
                self.get_status(
                    server=server,
                    now=now,
                    game_version=game_version,
                )
                == ActivityStatus.RUNNING
        )


class ActivityManager:
    """
    活动管理器
    """

    def __init__(self):

        self._activities: dict[str, Activity] = {}

    # =========================================================
    # register
    # =========================================================

    def register(
            self,
            activity: Activity,
    ) -> None:

        if activity.id in self._activities:
            raise ValueError(
                f"activity already registered: {activity.id}"
            )

        self._activities[activity.id] = activity

    def register_many(
            self,
            activities: Iterable[Activity],
    ) -> None:

        for activity in activities:
            self.register(activity)

    # =========================================================
    # remove
    # =========================================================

    def unregister(
            self,
            activity_id: str,
    ) -> None:

        self._activities.pop(activity_id, None)

    def clear(self) -> None:
        self._activities.clear()

    # =========================================================
    # get
    # =========================================================

    def get(
            self,
            activity_id: str,
    ) -> Activity:

        return self._activities[activity_id]

    def get_or_none(
            self,
            activity_id: str,
    ) -> Activity | None:

        return self._activities.get(activity_id)

    def exists(
            self,
            activity_id: str,
    ) -> bool:

        return activity_id in self._activities

    # =========================================================
    # status
    # =========================================================

    def get_status(
            self,
            activity_id: str,
            server: str,
            now: datetime | None = None,
            game_version: str | Version | None = None,
    ) -> ActivityStatus:

        activity = self.get(activity_id)

        return activity.get_status(
            server=server,
            now=now,
            game_version=game_version,
        )

    def is_available(
            self,
            activity_id: str,
            server: str,
            now: datetime | None = None,
            game_version: str | Version | None = None,
    ) -> bool:

        return (
                self.get_status(
                    activity_id=activity_id,
                    server=server,
                    now=now,
                    game_version=game_version,
                )
                == ActivityStatus.RUNNING
        )

    # =========================================================
    # query
    # =========================================================

    def get_available_activities(
            self,
            server: str,
            now: datetime | None = None,
            game_version: str | Version | None = None,
    ) -> list[Activity]:

        result: list[Activity] = []

        for activity in self._activities.values():

            if activity.is_available(
                    server=server,
                    now=now,
                    game_version=game_version,
            ):
                result.append(activity)

        return result

    def get_activities_by_status(
            self,
            status: ActivityStatus,
            server: str,
            now: datetime | None = None,
            game_version: str | Version | None = None,
    ) -> list[Activity]:

        result: list[Activity] = []

        for activity in self._activities.values():

            current_status = activity.get_status(
                server=server,
                now=now,
                game_version=game_version,
            )

            if current_status == status:
                result.append(activity)

        return result

    # =========================================================
    # iter
    # =========================================================

    def values(self) -> Iterator[Activity]:
        return iter(self._activities.values())

    def items(self):
        return self._activities.items()

    def ids(self):
        return self._activities.keys()

    def __iter__(self) -> Iterator[Activity]:
        return self.values()

    def __len__(self) -> int:
        return len(self._activities)

    def __contains__(self, activity_id: str) -> bool:
        return activity_id in self._activities


def demo():
    from datetime import datetime

    activity_manager = ActivityManager()

    activity_manager.register(
        Activity(
            id="summer_2026",
            name="夏日活动",
            min_game_version="2.4.0",
            max_game_version="2.4.99",
            server_times={
                "cn": ActivityTime(
                    start_time=datetime(2026, 6, 1, 4, 0, 0),
                    end_time=datetime(2026, 6, 28, 3, 59, 59),
                    timezone="Asia/Shanghai",
                ),
                "global": ActivityTime(
                    start_time=datetime(2026, 6, 3, 10, 0, 0),
                    end_time=datetime(2026, 6, 30, 9, 59, 59),
                    timezone="UTC",
                ),
            }
        )
    )

    status = activity_manager.get_status(
        activity_id="summer_2026",
        server="cn",
        game_version="2.4.3",
    )

    print(status)

    print(
        activity_manager.is_available(
            activity_id="summer_2026",
            server="cn",
            game_version="2.4.3",
        )
    )
