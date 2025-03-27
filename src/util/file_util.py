import datetime
import logging
import os
import random
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# 环境变量
ENV_PROJECT_ROOT = "PROJECT_ROOT"  # 值为项目根目录

# 文件名
LOG_FILE_NAME = "wwa.log"
LOG_TEST_FILE_NAME = "wwa_test-%s.log"  # 测试日志


###### Dir or File abspath ######

def get_project_root() -> Path:
    project_root = os.environ.get(ENV_PROJECT_ROOT, None)
    if project_root is not None:
        return Path(project_root)
    project_root_path = Path(__file__).parent.parent.parent
    os.environ[ENV_PROJECT_ROOT] = str(project_root_path)
    return project_root_path


def get_path(dir_name: str, file_name: str | None = None) -> Path | str:
    """
    获取目录或文件名
    :param dir_name: 相对路径，如: "logs"
    :param file_name: 文件名
    :return: 目录返回 Path，文件返回 str
    """
    dir_path = get_project_root().joinpath(dir_name)
    if file_name:
        file_path = str(dir_path.joinpath(file_name))
        logger.debug("Get path: %s", file_path)
        return file_path
    return dir_path


def get_logs(file_name: str | None = None):
    return get_path("logs", file_name)


def get_scripts(file_name: str | None = None):
    return get_path("scripts", file_name)


def get_temp(file_name: str | None = None):
    return get_path("temp", file_name)


def get_temp_screenshot(file_name: str | None = None):
    """ 测试用，返回临时截图目录内图片的绝对路径，用于读取图片 """
    return get_path("temp/screenshot", file_name)


def get_assets(file_name: str | None = None):
    return get_path("assets", file_name)


def get_assets_model(file_name: str | None = None):
    return get_path("assets/model", file_name)


def get_assets_model_boss(file_name: str | None = None):
    return get_path("assets/model/boss", file_name)


def get_assets_model_paddleocr(file_name: str | None = None):
    return get_path("assets/model/paddleocr", file_name)


def get_assets_model_reward(file_name: str | None = None):
    return get_path("assets/model/reward", file_name)


def get_assets_screenshot(file_name: str | None = None):
    return get_path("assets/screenshot", file_name)


def get_assets_template(file_name: str | None = None):
    return get_path("assets/template", file_name)


###### File abspath ######

def get_log_file() -> str:
    """日志文件的绝对路径"""
    return get_logs(LOG_FILE_NAME)


def get_test_log_file() -> str:
    """日志(测试)文件的绝对路径，自动添加当天的日期"""
    datetime_str = datetime.datetime.now().strftime("%Y-%m-%d")
    file_name = LOG_TEST_FILE_NAME % datetime_str
    return get_logs(file_name)


def create_img_path(prefix="screenshot") -> str:
    """
    生成不重复的图片路径，支持并发，绝对路径，png格式，自动创建目录，图片名称带当前时间戳和随机数，用于保存图片
    :param prefix: 图片名称前缀
    :return: e.g. X:\{project_dir}\temp\screenshot\screenshot_1740480141_66666666.png
    """
    temp_screenshot = get_temp_screenshot()
    temp_screenshot.mkdir(exist_ok=True, parents=True)
    tst = time.time()
    tst_int = int(tst)
    filename = f"{prefix}_{tst_int}_{int((tst - tst_int) * 10000):04d}{random.randint(1000, 9999)}.png"
    img_abspath = str(temp_screenshot.joinpath(filename))
    logger.debug("Generate image path: %s", img_abspath)
    return img_abspath
