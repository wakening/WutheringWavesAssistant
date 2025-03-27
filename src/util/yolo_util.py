import logging
from typing import Any

import cv2
import numpy as np
import onnxruntime
from onnxruntime import InferenceSession, SessionOptions

from src.util import file_util, img_util

logger = logging.getLogger(__name__)


class Model:
    def __init__(self, name: str, path: str, confidence_thres: float, iou_thres: float, classes: dict[int, str],
                 boss: list[str]):
        self.name = name
        self.path = path
        self.confidence_thres = confidence_thres
        self.iou_thres = iou_thres
        self.classes = classes
        self.boss = boss

    def __eq__(self, other: "Model"):
        return self.path == other.path


MODEL_BOSS_V10 = Model(
    name="boss_v10.onnx",
    path=file_util.get_assets_model_boss("boss_v10.onnx"),
    confidence_thres=0.5,
    iou_thres=0.5,
    classes={0: "echo"},
    boss=[
        "无妄者", "鸣钟之龟", "无冠者", "朔雷之鳞", "云闪之鳞", "燎照之骑", "飞廉之猩", "哀声鸷", "无常凶鹭",
        "辉萤军势", "聚械机偶", "无归的谬误"
    ]
)

MODEL_BOSS_V20 = Model(
    name="boss_v20.onnx",
    path=file_util.get_assets_model_boss("boss_v20.onnx"),
    confidence_thres=0.75,
    iou_thres=0.5,
    classes={0: "echo"},
    boss=[
        "无妄者", "角",
        "异构武装", "赫卡忒", "罗蕾莱", "叹息古龙", "梦魇飞廉之猩", "梦魇无常凶鹭",
        "梦魇云闪之鳞", "梦魇朔雷之鳞", "梦魇无冠者", "梦魇燎照之骑", "梦魇哀声鸷",
    ]
)

MODEL_REWARD = Model(
    name="reward.onnx",
    path=file_util.get_assets_model_reward("reward.onnx"),
    confidence_thres=0.65,
    iou_thres=0.5,
    classes={0: "reward"},
    boss=[]
)

# 启动时默认加载的模型
MODEL_BOSS_DEFAULT = MODEL_BOSS_V20
# 未知boss默认使用的模型
MODEL_BOSS_UNKNOWN = MODEL_BOSS_V20
# 所有boss模型，元素位置代表优先级，新模型优先
MODEL_BOSS_ALL = [MODEL_BOSS_V20, MODEL_BOSS_V10]


###########################################################################


def create_ort_session_options() -> onnxruntime.SessionOptions:
    session_options = onnxruntime.SessionOptions()
    # session_options.log_severity_level = 1 # 打开日志，排查为何有警告日志时使用，打印详细ort日志
    session_options.log_severity_level = 3  # 日志级别3，只显示异常日志
    return session_options


def get_ort_providers() -> list[str]:
    # ort.get_device() == "GPU"
    providers = onnxruntime.get_available_providers()
    logger.debug("ONNX Runtime available providers: %s", providers)
    if "CUDAExecutionProvider" in providers:
        ort_providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    elif "DmlExecutionProvider" in providers:
        ort_providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
    else:
        ort_providers = ["CPUExecutionProvider"]
    return ort_providers


def create_ort_session(model_path: str, providers: list[str] | None = None,
                       sess_options: SessionOptions | None = None) -> InferenceSession:
    session = InferenceSession(
        model_path,
        providers=providers,
        sess_options=sess_options
    )
    logger.debug("Create ONNX Runtime session")
    return session


def run_ort_session(session: InferenceSession, img: np.ndarray):
    # img需为RGB
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    logger.debug("Input name: %s, Output name: %s", input_name, output_name)
    outputs = session.run([output_name], {input_name: img})
    # logger.debug("outputs: %s", outputs)
    return outputs


def search_echo(session: InferenceSession, img: np.ndarray, confidence_thres=0.5, iou_thres=0.5):
    """YOLO RGB"""
    # img = img_util.bgr2rgb(img)
    input_shape = session.get_inputs()[0].shape
    logger.debug("Input shape: %s", input_shape)  # [1, 3, 640, 640] NCHW
    logger.debug("Image shape: %s", img.shape)  # (720, 1280, 3) HWC
    img_preprocess, _, _ = preprocess(img)
    outputs = run_ort_session(session, img_preprocess)
    logger.debug("Image shape: %s", img_preprocess.shape)  # (640, 640, 3) HWC
    boxes, scores, class_ids = postprocess(input_shape, img.shape, outputs, confidence_thres, iou_thres)
    # dump_search_result(img, boxes, scores, class_ids)
    if len(boxes) == 0:
        logger.debug("Echo not found")
        return None
    max_index = 0
    if len(boxes) > 1:
        max_index = np.argmax(scores)
    logger.debug("max scores: %s", scores[max_index])
    return boxes[max_index], scores[max_index], class_ids[max_index]


def dump_search_result(img, boxes, scores, class_ids):
    """本地调试用，保存声骸搜索结果图片"""
    from src.util import img_util
    img = img.copy()
    img = img_util.hide_uid(img)
    img_util.save_img_in_temp(img)
    draw_detections(img, boxes, scores, class_ids, {0: "echo"})
    img_util.save_img_in_temp(img)


def preprocess(img: np.ndarray, new_shape: tuple = (640, 640)):
    """
    Pre-processes the input image.

    Returns:
        img_process (Numpy.ndarray): image preprocessed for inference.
        ratio (tuple): width, height ratios in letterbox.
        pad_w (float): width padding in letterbox.
        pad_h (float): height padding in letterbox.

        :param img: (Numpy.ndarray): image about to be processed.
        :param new_shape: (640, 640)
    """
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Resize and pad input image using letterbox() (Borrowed from Ultralytics)
    shape = img.shape[:2]  # original image shape
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    ratio = r, r
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    pad_w, pad_h = (new_shape[1] - new_unpad[0]) / 2, (new_shape[0] - new_unpad[1]) / 2  # wh padding
    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(pad_h - 0.1)), int(round(pad_h + 0.1))
    left, right = int(round(pad_w - 0.1)), int(round(pad_w + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
    # Transforms: HWC to CHW -> div(255) -> contiguous -> add axis(optional)
    # H：高度（Height）, W：宽度（Width）, C：通道数（Channel），例如：3 通道：RGB / BGR 彩色图片, 1 通道：灰度图片
    img = np.ascontiguousarray(np.einsum("HWC->CHW", img), dtype=np.single) / 255.0
    # 大多数深度学习模型要求输入数据为(N, C, H, W)，其中 N 表示批次大小（batch_size）。即使只推理一张图片，也需要有这个 batch 维度。
    # img[None] 相当于在第 0 维添加了一个新的维度, 是 NumPy 中的一种简洁写法。它等价于 np.expand_dims(img, axis=0)
    img_process = img[None] if len(img.shape) == 3 else img
    pad = (pad_w, pad_h)
    logger.debug("ratio: %s, pad: %s", ratio, pad)
    return img_process, ratio, pad


def postprocess(input_shape, img_shape, output, confidence_thres, iou_thres) -> tuple[list[Any], list[Any], list[Any]]:
    # Transpose and squeeze the output to match the expected shape
    outputs = np.transpose(np.squeeze(output[0]))

    # Get the number of rows in the outputs array
    rows = outputs.shape[0]

    # Lists to store the bounding boxes, scores, and class IDs of the detections
    boxes = []
    scores = []
    class_ids = []

    # Store the shape of the input for later use
    input_width = input_shape[2]
    input_height = input_shape[3]
    # Get the height and width of the input image
    img_height, img_width = img_shape[:2]

    # Calculate the scaling factors for the bounding box coordinates
    x_factor = img_width / input_width
    y_factor = img_height / input_height

    # Iterate over each row in the outputs array
    for i in range(rows):
        # Extract the class scores from the current row
        classes_scores = outputs[i][4:]

        # Find the maximum score among the class scores
        max_score = np.amax(classes_scores)

        # If the maximum score is above the confidence threshold
        if max_score >= confidence_thres:
            # Get the class ID with the highest score
            class_id = np.argmax(classes_scores)

            # Extract the bounding box coordinates from the current row
            x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]

            # Calculate the scaled coordinates of the bounding box
            left = int((x - w / 2) * x_factor)
            top = int((y - h / 2) * y_factor)
            width = int(w * x_factor)
            height = int(h * y_factor)

            # Add the class ID, score, and box coordinates to the respective lists
            class_ids.append(class_id)
            scores.append(max_score)
            boxes.append([left, top, width, height])

    if len(boxes) == 0:
        return [], [], []

    # Apply non-maximum suppression to filter out overlapping bounding boxes
    # boxes：检测框列表，格式为 [[x, y, w, h], ...]（左上角坐标和宽高）。
    # scores：每个检测框对应的置信度分数（confidence scores）。
    # confidence_thres：过滤掉低于该值的检测框（通常不影响最终 NMS）。
    # iou_thres：IOU（交并比）阈值，用于控制 NMS 剔除重叠框的严格程度。
    indices = cv2.dnn.NMSBoxes(boxes, scores, confidence_thres, iou_thres)
    logger.debug("indices: %s", indices)

    filtered_boxes = [boxes[i] for i in indices]
    filtered_scores = [scores[i] for i in indices]
    filtered_class_ids = [class_ids[i] for i in indices]
    logger.debug("boxes: %s", boxes)
    logger.debug("scores: %s", scores)
    logger.debug("class_ids: %s", class_ids)
    return filtered_boxes, filtered_scores, filtered_class_ids


def draw_detections(img: np.ndarray, boxes: list, scores: list, class_ids: list, classes: dict):
    # Generate a color palette for the classes
    color_palette = np.random.uniform(0, 255, size=(len(classes), 3))
    for i in range(len(boxes)):
        box, score, class_id = boxes[i], scores[i], class_ids[i]
        # Extract the coordinates of the bounding box
        x1, y1, w, h = box
        # Retrieve the color for the class ID
        color = color_palette[class_id]
        # Draw the bounding box on the image
        cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color, 2)
        # Create the label text with class name and score
        label = f"{classes[class_id]}: {score:.2f}"
        # Calculate the dimensions of the label text
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        # Calculate the position of the label text
        label_x = x1
        label_y = y1 - 10 if y1 - 10 > label_height else y1 + 10
        # Draw a filled rectangle as the background for the label text
        cv2.rectangle(img, (label_x, label_y - label_height), (label_x + label_width, label_y + label_height), color,
                      cv2.FILLED)
        # Draw the label text on the image
        cv2.putText(img, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
