import logging

from src.config import logging_config
from src.core import environs
from src.util import hwnd_util

logger = logging.getLogger(__name__)


# hook
def pytest_configure(config):
    # option = config.option
    environs.load_env()
    logging_config.setup_logging_test()
    hwnd_util.enable_dpi_awareness()

#
# @pytest.hookimpl(tryfirst=True)
# def pytest_sessionstart(session):
#     pass
#
#
#
# # scope
# # function: 每个测试函数前都执行，适合每个测试独立初始化工作。
# # class: 每个测试类前执行一次，适用于类级别的共享状态。
# # module: 每个模块执行一次，适用于模块级别的资源初始化。
# # session: 整个测试会话只执行一次，适用于全局初始化。
# @pytest.fixture(scope='function', autouse=True)
# def setup_logging():
#     print("\n", flush=True)
#     pass
#
#
# def pytest_runtest_setup(item):
#     pass
#
#
# def pytest_runtest_teardown(item):
#     pass
