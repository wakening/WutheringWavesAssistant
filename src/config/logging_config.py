import logging.config
import os
import pprint
import re

from colorlog import ColoredFormatter

from src.util import file_util

logger = logging.getLogger(__name__)

RE_CUSTOM_LINENO = re.compile(r'%\(customLineno\)-(\d+)s')


def _custom_logging_format(formatter: logging.Formatter, record: logging.LogRecord):
    """
    动态添加 customLineno 字段，由三个变量（filename:funcName:lineno）拼接而成，函数名过长会截短用省略号表示
    :param formatter:
    :param record:
    :return:
    """
    # noinspection PyProtectedMember
    match = RE_CUSTOM_LINENO.search(formatter._style._fmt)  # 提取占位符中的数字
    # TODO filename再短些，将中间一段字符缩减为三个点表示
    custom_filename = os.path.splitext(record.filename)[0]
    custom_func_name = record.funcName
    if match:
        width = int(match.group(1))
        max_fun_name_len = width - 2 - len(str(custom_filename)) - len(str(record.lineno))
        if 4 < max_fun_name_len < len(record.funcName):
            custom_func_name = f"{record.funcName[:max_fun_name_len - 4]}...{record.funcName[-1]}"
    record.customLineno = f"{custom_filename}.{custom_func_name}:{record.lineno}"
    return record


class CustomFormatter(logging.Formatter):
    def format(self, record):
        return super().format(_custom_logging_format(self, record))


class CustomColoredFormatter(ColoredFormatter):
    def format(self, record):
        return super().format(_custom_logging_format(self, record))


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,  # 保留已有 logger
    'formatters': {
        'colored': {
            '()': CustomColoredFormatter,  # 使用自定义 colorlog.ColoredFormatter
            'format': '%(log_color)s%(asctime)s - %(levelname)-5s - %(customLineno)-30s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'log_colors': {
                'DEBUG': 'green',
                'INFO': 'white',
                'WARNING': 'yellow',
                'WARN': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            },
        },
        'standard': {
            '()': CustomFormatter,  # 使用自定义 Formatter
            'format': '%(asctime)s - %(levelname)-5s - %(customLineno)-30s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored',  # 使用彩色 formatter
            'level': 'DEBUG'
        },
        # 'file': {
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'formatter': 'standard',  # 文件输出使用标准 formatter
        #     'filename': file_util.get_log_file(),
        #     'maxBytes': 10 * 1024 * 1024,  # 10MB
        #     'backupCount': 5,  # 这里不做自动备份，由压缩等其他方式处理
        #     'encoding': 'utf-8',
        #     'level': 'DEBUG'
        # },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'standard',
            'filename': file_util.get_log_file(),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 5,
            'encoding': 'utf-8',
            'level': 'INFO'
        },
    },
    'loggers': {  # module 的日志级别
        'src': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'src.config.logging_config': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'src.util.img_util': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'src.util.file_util': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'src.util.yolo_util': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'tests': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {  # 根 logger 配置
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

LOGGING_CONFIG_TEST = {
    'version': 1,
    'disable_existing_loggers': False,  # 保留已有 logger
    'formatters': {
        'colored': {
            '()': CustomColoredFormatter,  # 使用自定义 colorlog.ColoredFormatter
            'format': '%(log_color)s%(asctime)s - %(levelname)-5s - %(customLineno)-30s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'log_colors': {
                'DEBUG': 'green',
                'INFO': 'white',
                'WARNING': 'yellow',
                'WARN': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            },
        },
        'standard': {
            '()': CustomFormatter,  # 使用自定义 Formatter
            'format': '%(asctime)s - %(levelname)-5s - %(customLineno)-30s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored',  # 使用彩色 formatter
            'level': 'DEBUG'
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'standard',
            'filename': file_util.get_test_log_file(),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 5,
            'encoding': 'utf-8',
            'level': 'DEBUG'
        },
    },
    'loggers': {  # module 的日志级别
        'src': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'src.config.logging_config': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'tests': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {  # 根 logger 配置
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}


def setup_logging():
    logging.addLevelName(logging.WARNING, "WARN")
    file_util.get_logs().mkdir(exist_ok=True, parents=True)
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.debug(f"LOGGING_CONFIG: {pprint.pformat(LOGGING_CONFIG, indent=4)}")


def setup_logging_test():
    logging.addLevelName(logging.WARNING, "WARN")
    file_util.get_logs().mkdir(exist_ok=True, parents=True)
    logging.config.dictConfig(LOGGING_CONFIG_TEST)
    logger.debug(f"LOGGING_CONFIG_TEST: {pprint.pformat(LOGGING_CONFIG_TEST, indent=4)}")
