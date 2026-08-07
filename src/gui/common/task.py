import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any

from PySide6.QtCore import QObject, Signal

from src.gui.common.globals import globalSignal
from src.gui.common.signal_bus import signalBus

logger = logging.getLogger(__name__)


class TaskId(str, Enum):
    DailyTask = "DailyTask"
    AutoBossProcessTask = "AutoBossProcessTask"
    AutoPickupProcessTask = "AutoPickupProcessTask"
    ExploreTask = "ExploreTask"
    AutoStorySkipProcessTask = "AutoStorySkipProcessTask"
    AutoStoryEnjoyProcessTask = "AutoStoryEnjoyProcessTask"
    DailyActivityProcessTask = "DailyActivityProcessTask"
    EchoMergeProcessTask = "EchoMergeProcessTask"
    SoarToTheBeatMacroReplayTask = "SoarToTheBeatMacroReplayTask"
    SoarToTheBeatMacroRecordTask = "SoarToTheBeatMacroRecordTask"


@dataclass
class ValidationResult:
    success: bool
    message: str = ""
    code: Optional[str] = None
    detail: Optional[Any] = None


class BaseTask(QObject):
    taskSignal = Signal(object)

    def __init__(self, id: str, name: str):
        super().__init__()
        self.id: str = id
        self.name: str = name
        self.create_time: datetime = datetime.now()
        self.start_time = None

    def validate(self, **kwargs) -> ValidationResult:
        raise NotImplementedError()

    def submit(self, start: bool):
        logger.debug(f"Submitting {self.id}")
        if start:
            self.start_time = datetime.now()
            # json_string = json.dumps(self.config, ensure_ascii=False, indent=4)
            signalBus.homeMessageSignal.emit(f"{self.tr("Start")} {self.name}")
            globalSignal.executeTaskSignal.emit(self.id, "START")
            return

        globalSignal.executeTaskSignal.emit(self.id, "STOP")
        elapsed = ""
        if self.start_time:
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
            hours, remainder = divmod(elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed = f", {int(hours)}h {int(minutes)}m {seconds:.2f}s"
        signalBus.homeMessageSignal.emit(f"{self.tr("Stop")} {self.name}{elapsed}")
