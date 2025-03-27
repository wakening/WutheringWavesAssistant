import logging
from abc import ABC, abstractmethod
from multiprocessing import Process

logger = logging.getLogger(__name__)


class ProcessController(ABC):
    PROCESS_DICT: dict[str, Process] = {}

    # def __init__(self):
    #     pass

    @abstractmethod
    def execute(self):
        pass

    # @abstractmethod
    # def stop(self):
    #     pass
    #

    def exist(self, process_name: str):
        return process_name in self.PROCESS_DICT and self.PROCESS_DICT[process_name] is not None

    def cache_process(self, process_name: str, process: Process) -> bool:
        if self.exist(process_name):
            logger.warning("任务进程已存在: %s", process_name)
            return False
        self.PROCESS_DICT[process_name] = process
        return True
