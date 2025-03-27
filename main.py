import logging

from src.config import logging_config

logging_config.setup_logging()

from src import application

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("https://github.com/wakening/WutheringWavesAssistant")
    logger.warning("当前版本为测试版，仅供测试，非最终效果")
    application.run()
    logger.info("https://github.com/wakening/WutheringWavesAssistant")
    logger.info("结束")
