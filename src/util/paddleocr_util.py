import logging

import numpy as np
import paddle
from paddleocr import PaddleOCR, draw_ocr

logger = logging.getLogger(__name__)


# https://paddlepaddle.github.io/PaddleOCR/latest/ppocr/model_list.html

# # Det（文本检测）识别文字、Rec（文本识别）识别文本框的位置 和 Cls（文本分类）
# PADDLE_DET_MODEL_DIR = str(file_util.get_assets_model_paddleocr().joinpath("ch_PP-OCRv4_det_infer"))
# PADDLE_REC_MODEL_DIR = str(file_util.get_assets_model_paddleocr().joinpath("ch_PP-OCRv4_rec_infer"))
#
# PADDLE_DET_MODEL_FILES = ["inference.pdiparams", "inference.pdiparams.info", "inference.pdmodel"]
# PADDLE_REC_MODEL_FILES = ["inference.pdiparams", "inference.pdiparams.info", "inference.pdmodel"]


###########################################################################


def check_paddleocr_gpu_available() -> bool:
    return paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0


def create_paddleocr(
        use_angle_cls: bool = False,
        lang: str = "ch",
        use_gpu: bool = False,
        precision: str = "fp16",  # "int8", "fp16"
        show_log: bool = False,
        enable_mkldnn=False,
) -> PaddleOCR:
    if use_gpu:
        return create_paddleocr_gpu(
            use_angle_cls=use_angle_cls,
            lang=lang,
            precision=precision,
            show_log=show_log,
        )
    else:
        return create_paddleocr_cpu(
            use_angle_cls=use_angle_cls,
            lang=lang,
            precision=precision,
            show_log=show_log,
            enable_mkldnn=enable_mkldnn,
        )


def create_paddleocr_gpu(
        use_angle_cls: bool = False,
        lang: str = "ch",
        # use_gpu: bool = True,
        precision: str = "fp16",  # "int8", "fp16"
        show_log: bool = False,
        # enable_mkldnn=True,
) -> PaddleOCR:
    if check_paddleocr_gpu_available():
        raise Exception("paddleocr没有配置GPU环境但开启GPU模式")
    # logger.info("PaddleOCR is running on the %s", "GPU" if use_gpu else "CPU")
    ocr = PaddleOCR(
        use_angle_cls=use_angle_cls,
        lang=lang,  # `ch`, `en`, `fr`, `german`, `korean`, `japan`
        use_gpu=True,
        precision=precision,
        show_log=show_log,
        # enable_mkldnn=enable_mkldnn,
    )  # need to run only once to download and load model into memory
    return ocr


def create_paddleocr_cpu(
        use_angle_cls: bool = False,
        lang: str = "ch",
        # use_gpu: bool = True,
        precision: str = "fp16",  # "int8", "fp16"
        show_log: bool = True,
        enable_mkldnn=False,  # intel加速
) -> PaddleOCR:
    # logger.info("PaddleOCR is running on the %s", "GPU" if use_gpu else "CPU")
    ocr = PaddleOCR(
        use_angle_cls=use_angle_cls,
        lang=lang,  # `ch`, `en`, `fr`, `german`, `korean`, `japan`
        use_gpu=False,
        precision=precision,
        show_log=show_log,
        enable_mkldnn=enable_mkldnn,
    )  # need to run only once to download and load model into memory
    return ocr


def execute_paddleocr(ocr: PaddleOCR, img: np.ndarray, det=True, rec=True, cls=False):
    """
    没搜到返回: [None]
    搜到返回: [
        [[[335.0, 67.0], [483.0, 68.0], [483.0, 86.0], [335.0, 85.0]], ('KUROGAMES', 0.9672181010246277)]
    ]
    :param ocr:
    :param img:
    :param det:
    :param rec:
    :param cls:
    :return: list[None | list[list] | list] | list
    """
    return ocr.ocr(img, det=det, rec=rec, cls=cls)


def print_paddleocr_result(result):
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            logger.debug(line)


def draw_paddleocr_result(result, img: np.ndarray) -> np.ndarray:
    result = result[0]
    boxes = [line[0] for line in result]
    texts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    img_draw = draw_ocr(img, boxes, texts, scores)
    return img_draw
