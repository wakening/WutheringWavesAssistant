import logging

import numpy as np
from rapidocr import RapidOCR, VisRes
from rapidocr.utils import RapidOCROutput
from tqdm import tqdm

from src.util import file_util, img_util

logger = logging.getLogger(__name__)

# https://github.com/RapidAI/RapidOCR
# https://paddlepaddle.github.io/PaddleOCR/latest/model/index.html

_COMMON_PARAMS = {
    "Global.use_cls": False,
    "Global.width_height_ratio": -1,
    "Det.limit_type": "min",
    "Det.limit_side_len": 0,
}
_CPU_PARAMS = {
    **_COMMON_PARAMS,
}
_DML_PARAMS = {
    **_COMMON_PARAMS,
    "Global.with_onnx": True,
    "EngineConfig.onnxruntime.use_dml": True,
}
# _GPU_ONNXRUNTIME_PARAMS = {
#     **_COMMON_PARAMS,
#     "Global.with_onnx": True,
#     "EngineConfig.onnxruntime.use_cuda": True,
# }
_GPU_PADDLEPADDLE_PARAMS = {
    **_COMMON_PARAMS,
    "Global.with_paddle": True,
    "EngineConfig.paddlepaddle.use_cuda": True,
}


def create_ocr(*, use_gpu: bool = False, use_dml=False) -> RapidOCR:
    # https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/API/RapidOCR/#_1
    if use_gpu:
        params = _GPU_PADDLEPADDLE_PARAMS
    elif use_dml:
        params = _DML_PARAMS
    else:
        params = _CPU_PARAMS
    engine = RapidOCR(
        params=params
    )  # 输入BGR
    # logger.debug(engine.text_det.session.session.get_provider_options())
    # sss = engine.text_det.session.session
    # logger.debug(engine.text_det.session.session.get_session_options())
    return engine


# https://github.com/microsoft/onnxruntime/issues/13198#issuecomment-1554180044
def model_warmup(engine: RapidOCR, batch_size: int = 1, min_size: int = 10, max_size: int = 20):
    """
    onnxruntime-gpu
    Recognition model have input size: [-1, 3, 48, -1]
    ONNXRuntime with CUDA support is not performing well with arbitrary input size
    So we need to warmup the model with arbitrary input size
    """
    logger.info("Warming up model...")
    img_names = ["Dialogue_001.png", "Login_001.png", "Revival_001.png"]
    imgs = [img_util.read_img(file_util.get_assets_screenshot(img_name)) for img_name in img_names]
    index = 0
    for i in tqdm(range(min_size, max_size), desc="Warming up model"):
        engine(imgs[index % 3], use_det=True, use_rec=True, use_cls=False)
        index += 1
    logger.info("Model warmup completed")


def print_ocr_result(output: RapidOCROutput):
    for i in range(output.boxes.shape[0]):
        logger.debug("score: %s,\ttext: '%s',\tbox: %s", output.scores[i], output.txts[i], list(output.boxes[i]))


def draw_ocr_result(output: RapidOCROutput) -> np.ndarray:
    if output.boxes is None:
        return output.img
    vis = VisRes()
    if output.word_results and any(output.word_results):
        words, words_scores, words_boxes = zip(*output.word_results)
        vis_img = vis(output.img, words_boxes, words, words_scores)
    else:
        vis_img = vis(output.img, output.boxes, output.txts, output.scores)
    return vis_img

# def draw_detections(img: np.ndarray, boxes: Sequence, scores: Sequence, classes: Sequence):
#     # Generate a color palette for the classes
#     color_palette = np.random.uniform(0, 255, size=(len(classes), 3))
#     for i in range(len(boxes)):
#         box, score, class_id = boxes[i], scores[i], classes[i]
#         # Extract the coordinates of the bounding box
#         x1, y1, x2, y2 = int(box[0][0]), int(box[0][1]), int(box[2][0]), int(box[2][1])
#         # Retrieve the color for the class ID
#         color = color_palette[i]
#         # Draw the bounding box on the image
#         cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
#         # cv2.rectangle(img, (int(box[0][0]), int(box[0][1])), (int(box[2][0]), int(box[2][1])), color, 2)
#         # Create the label text with class name and score
#         label = f"{class_id}: {score:.2f}"
#         # Calculate the dimensions of the label text
#         (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
#         # Calculate the position of the label text
#         label_x = x1
#         label_y = y1 - 10 if y1 - 10 > label_height else y1 + 10
#         # Draw a filled rectangle as the background for the label text
#         logger.debug(label_x)
#         logger.debug((label_x, label_y - label_height))
#         logger.debug((label_x + label_width, label_y + label_height))
#         cv2.rectangle(img, (label_x, label_y - label_height), (label_x + label_width, label_y + label_height), color, cv2.FILLED)
#         # Draw the label text on the image
#         cv2.putText(img, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
