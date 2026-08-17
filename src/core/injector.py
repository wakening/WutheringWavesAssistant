import importlib.util
import logging

from dependency_injector import containers, providers

logger = logging.getLogger(__name__)


def select_ocr_engine_impl():
    ocr_engine_impl = None
    try:
        # 若安装paddleocr则是用paddleocr作为ocr引擎
        if importlib.util.find_spec("paddleocr"):
            from paddleocr import PaddleOCR  # type: ignore
            from src.service.ocr_service import PaddleOcrServiceImpl
            ocr_engine_impl = PaddleOcrServiceImpl
            logger.info("paddleocr detected")
    except Exception:
        logger.exception("Failed to import PaddleOCR")
    # 默认ocr引擎
    if ocr_engine_impl is None:
        from src.service.ocr_service import RapidOcrServiceImpl
        ocr_engine_impl = RapidOcrServiceImpl
        logger.debug("rapidocr detected")
    return ocr_engine_impl


class Container(containers.DeclarativeContainer):
    from src.core.message import MessageBus, ProcessBridge
    from src.service.auto_boss_service import AutoBossServiceImpl
    from src.service.auto_pickup_service import AutoPickupServiceImpl
    from src.service.auto_story_service import AutoStoryServiceImpl
    from src.service.boss_info_service import BossInfoServiceImpl
    from src.service.combat_service import CombatServiceImpl
    from src.service.control_service import Win32ControlServiceImpl
    from src.service.img_service import ImgServiceImpl
    # from src.service.ocr_service import PaddleOcrServiceImpl
    # from src.service.ocr_service import RapidOcrServiceImpl
    from src.service.od_service import YoloServiceImpl
    from src.service.window_service import HwndServiceImpl

    context = providers.Dependency()  # 占位，后续覆盖成真实ctx
    ocr_engine_impl = select_ocr_engine_impl()
    keyboard_mapping = providers.Object({})
    msg_bus = providers.Singleton(MessageBus)
    proc_bridge = providers.Singleton(
        ProcessBridge,
        bus=msg_bus
    )
    window_service = providers.Singleton(
        HwndServiceImpl,
        context=context
    )
    img_service = providers.Singleton(
        ImgServiceImpl,
        context=context,
        window_service=window_service
    )
    ocr_service = providers.Singleton(
        ocr_engine_impl,
        context=context,
        window_service=window_service,
        img_service=img_service
    )
    od_service = providers.Singleton(
        YoloServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service
    )
    control_service = providers.Singleton(
        Win32ControlServiceImpl,
        context=context,
        window_service=window_service
    )
    boss_info_service = providers.Singleton(
        BossInfoServiceImpl
    )
    combat_service = providers.Singleton(
        CombatServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service,
        control_service=control_service,
        boss_info_service=boss_info_service,
    )
    auto_boss_service = providers.Singleton(
        AutoBossServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service,
        ocr_service=ocr_service,
        control_service=control_service,
        od_service=od_service,
        boss_info_service=boss_info_service,
    )
    auto_pickup_service = providers.Singleton(
        AutoPickupServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service,
        ocr_service=ocr_service,
        control_service=control_service,
        od_service=None,
        boss_info_service=boss_info_service,
    )
    auto_story_service = providers.Singleton(
        AutoStoryServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service,
        ocr_service=ocr_service,
        control_service=control_service,
        od_service=None,
        boss_info_service=boss_info_service,
    )

    def __init__(self, **kwargs):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__(**kwargs)

    @staticmethod
    def build(context) -> "Container":
        container = Container()
        container.context.override(providers.Object(context))
        context._container = container
        container.init_resources()
        return container
