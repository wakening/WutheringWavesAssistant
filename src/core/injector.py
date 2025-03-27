import logging

from dependency_injector import containers, providers

logger = logging.getLogger(__name__)


class Container(containers.DeclarativeContainer):
    from src.core.contexts import Context
    from src.service.auto_boss_service import AutoBossServiceImpl
    from src.service.auto_pickup_service import AutoPickupServiceImpl
    from src.service.auto_story_service import AutoStoryServiceImpl
    from src.service.control_service import Win32ControlServiceImpl
    from src.service.daily_activity_service import DailyActivityServiceImpl
    from src.service.img_service import ImgServiceImpl
    # from src.service.ocr_service import PaddleOcrServiceImpl
    from src.service.ocr_service import RapidOcrServiceImpl
    from src.service.od_service import YoloServiceImpl
    from src.service.window_service import HwndServiceImpl

    context = providers.Dependency()
    keyboard_mapping = providers.Object({})
    window_service = providers.Singleton(HwndServiceImpl, context=context)
    img_service = providers.Singleton(
        ImgServiceImpl,
        context=context,
        window_service=window_service
    )
    ocr_service = providers.Singleton(
        RapidOcrServiceImpl,
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
    auto_boss_service = providers.Singleton(
        AutoBossServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service,
        ocr_service=ocr_service,
        control_service=control_service,
        od_service=od_service,
    )
    auto_pickup_service = providers.Singleton(
        AutoPickupServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service,
        ocr_service=ocr_service,
        control_service=control_service,
        od_service=None,
    )
    auto_story_service = providers.Singleton(
        AutoStoryServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service,
        ocr_service=ocr_service,
        control_service=control_service,
        od_service=None,
    )
    daily_activity_service = providers.Singleton(
        DailyActivityServiceImpl,
        context=context,
        window_service=window_service,
        img_service=img_service,
        ocr_service=ocr_service,
        control_service=control_service,
        od_service=od_service,
    )

    def __init__(self, **kwargs):
        logger.debug("Initializing %s", self.__class__.__name__)
        super().__init__(**kwargs)

    @staticmethod
    def build(context: Context) -> "Container":
        container = Container()
        container.context.override(providers.Object(context))
        context._container = container
        container.init_resources()
        return container
