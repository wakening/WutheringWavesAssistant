import base64
import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def read_img(img_path: str | Path, alpha: bool | None = True) -> np.ndarray:
    """
    读取图片，返回BGR或BGRA
    :param img_path:
    :param alpha: 默认保留原图Alpha通道
    :return: BGR/BGRA ndarray，有没有Alpha通道取决于原图是否有
    """
    if isinstance(img_path, Path):
        img_path = str(img_path)
    logger.debug("Read image: %s", img_path)
    # # OpenCV 默认 BGR，丢弃 Alpha 通道，不支持中文路径
    # img = cv2.imread(img_path)
    # img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED) # 不丢弃Alpha通道
    # PIL Image.open() 读取图片时，默认模式 不改变图片原始格式，颜色为RGB，有Alpha通道就是RGBA
    img_pil = Image.open(img_path)
    img = np.array(img_pil)
    if img_pil.mode == "RGB":
        logger.debug("img.shape: %s, %s -> BGR", img.shape, img_pil.mode)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif img_pil.mode == "RGBA":
        if alpha:
            logger.debug("img.shape: %s, %s -> BGRA", img.shape, img_pil.mode)
            return cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)
        else:
            logger.debug("img.shape: %s, %s -> BGR", img.shape, img_pil.mode)
            return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        return img  # 灰度图或其他格式


def save_img(img_bgr: np.ndarray, img_path: str):
    """
    保存BGR图片
    :param img_bgr: 图片格式必需为BGR/BGRA
    :param img_path:
    :return:
    """
    logger.debug("Save image: %s", img_path)
    if img_bgr.shape[-1] == 4:  # BGRA 图像
        img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2BGR)
    cv2.imwrite(img_path, img_bgr)


def save_img_in_temp(img_bgr: np.ndarray):
    """
    保存BGR图片
    :param img_bgr: 图片格式必需为BGR/BGRA
    :return:
    """
    from src.util import file_util
    img_path = file_util.create_img_path()
    logger.info(f"img_path: %s", img_path)
    save_img(img_bgr, img_path)


# def save_rgb_img(img_rgb: np.ndarray, img_path: str):
#     """
#     保存RGB图片
#     :param img_rgb: 图片格式必需为RGB/RGBA
#     :param img_path:
#     :return:
#     """
#     logger.debug("Save image: %s", img_path)
#     if img_rgb.shape[-1] == 4:  # BGRA 图像
#         img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGBA2BGR)
#     else:
#         img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
#     cv2.imwrite(img_path, img_bgr)



def img_to_base64(img: np.ndarray):
    """
    np图片转base64
    :param img: 图片格式必需为BGR/BGRA
    :return:
    """
    _, encoded = cv2.imencode('.png', img)
    b64 = base64.b64encode(encoded.tobytes()).decode()
    logger.debug(f"b64: {b64}")
    return b64


def base64_to_img(b64: str):
    """
    np图片转base64
    :param b64: 图片格式必需为BGR/BGRA
    :return:
    """
    img_bytes = base64.b64decode(b64)
    nparr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)


def show_img_plt(img: np.ndarray):
    from matplotlib import pyplot as plt
    # 使用 matplotlib 展示 numpy 数组图像
    plt.imshow(img)
    plt.axis('off')  # 关闭坐标轴
    plt.show()


def show_img(img: np.ndarray):
    logger.debug(f"img.shape: {img.shape}")
    if img.shape[-1] == 4:
        img = img[:, :, 3]
    cv2.imshow('Image Window', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def bgr2rgb(img_bgr: np.ndarray):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def rgb2bgr(img_rgb: np.ndarray):
    return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)


def rgb2gray(img_rgb: np.ndarray):
    """ RGB/RGBA彩色图像转GRAY灰度图 """
    if len(img_rgb.shape) == 3:
        if img_rgb.shape[2] == 3:
            return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)  # 3通道 RGB -> 灰度
        elif img_rgb.shape[2] == 4:
            return cv2.cvtColor(img_rgb, cv2.COLOR_RGBA2GRAY)  # 4通道 RGBA -> 灰度
    raise ValueError(f"Unsupported image format: {img_rgb.shape}")


def bgr2gray(img_bgr: np.ndarray):
    """ BGR/BGRA彩色图像转GRAY灰度图 """
    if len(img_bgr.shape) == 3:
        if img_bgr.shape[2] == 3:
            return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)  # 3通道 BGR -> 灰度
        elif img_bgr.shape[2] == 4:
            return cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2GRAY)  # 4通道 BGRA -> 灰度
    raise ValueError(f"Unsupported image format: {img_bgr.shape}")


def create_dummy() -> np.ndarray:
    dummy = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.putText(dummy, "123456", (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    return dummy


def resize(img: np.ndarray, dsize: tuple[int, int]) -> np.ndarray:
    img_new = cv2.resize(img, dsize, interpolation=cv2.INTER_AREA)
    logger.debug("img resize: %s -> %s", img.shape, img_new.shape)
    return img_new


def resize_by_weight(img: np.ndarray, target_weight: int = 1280) -> np.ndarray:
    """
    图片等比缩放，将宽度缩小到期望宽度（1280px），不会拉伸图片
    :param img:
    :param target_weight: 期望宽度px
    :return:
    """
    h, w = img.shape[:2]
    if w == target_weight:
        return img
    # 计算等比例缩放后的宽度
    new_w = target_weight
    new_h = int(h * new_w / w)
    img_new = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    logger.debug("img resize: %s -> %s", img.shape, img_new.shape)
    return img_new


def resize_by_ratio(img: np.ndarray, ratio: float) -> np.ndarray:
    """
    图片等比缩小，将宽度缩小到期望宽度（1280px），不会拉伸图片
    :param img:
    :param ratio: 缩放比例
    :return:
    """
    if ratio <= 0.0:
        raise ValueError(f"ratio must be greater than zero, got {ratio}")
    if ratio == 1.0:
        return img
    h, w = img.shape[:2]
    # 计算等比例缩放后的宽度
    new_w = int(w * ratio)
    new_h = int(h * ratio)
    img_new = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    logger.debug("img resize: %s -> %s", img.shape, img_new.shape)
    return img_new


def match_template(img: np.ndarray,
                   template_img: np.ndarray) -> tuple[float, tuple[int, int, int, int]]:
    """
    模板匹配（灰度）
    :param img:
    :param alpha: 若模板图片带Alpha通道，默认使用Alpha掩码匹配
    :param template_img:
    :return: (confidence, (x1, y1, x2, y2))
    """
    # save_img_in_temp(img)
    # save_img_in_temp(template_img)
    # 转为灰度图
    img_gray = bgr2gray(img)
    template_img_gray = bgr2gray(template_img)
    # 常见的模板匹配方法：
    # cv2.TM_CCOEFF: 相关系数匹配法。
    # cv2.TM_CCOEFF_NORMED: 归一化的相关系数匹配法（常用）。
    # cv2.TM_SQDIFF: 均方差匹配法。
    # cv2.TM_SQDIFF_NORMED: 归一化的均方差匹配法。
    result = cv2.matchTemplate(img_gray, template_img_gray, cv2.TM_CCOEFF_NORMED)
    # logger.debug("matchTemplate: %s", result)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    logger.debug("max_val: %s, max_loc: %s", max_val, max_loc)
    h, w = template_img.shape[:2]
    confidence_max_position = max_val, (max_loc[0], max_loc[1], max_loc[0] + w, max_loc[1] + h)
    logger.debug("match template: %s", confidence_max_position)
    return confidence_max_position


def draw_match_template_result(img: np.ndarray, position: tuple[float, tuple[int, int, int, int]]) -> np.ndarray:
    """在图片上绘制匹配区域方框和匹配得分"""
    max_val, (x1, y1, x2, y2) = position
    # 画出匹配区域
    img = cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # 在矩形区域旁边绘制匹配得分
    text = f"{max_val:.4f}"
    # 默认文字位置：在匹配区域上方
    x, y = x1, y1 - 5
    if y < 10:
        y = y2 + 20
    # 绘制文本
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
    return img


def hide_uid(img: np.ndarray, x_ratio=0.88, y_ratio=0.975):
    return hide_uid_blended(img, x_ratio, y_ratio)


def hide_uid_cover(img: np.ndarray, x_ratio=0.88, y_ratio=0.975, color=(114, 114, 114)):
    """固定颜色填充"""
    h, w, _ = img.shape
    x_start, y_start = int(w * x_ratio), int(h * y_ratio)
    # img.setflags(write=True)
    # img = np.array(img, copy=True)
    img[y_start:, x_start:] = color
    return img


def hide_uid_blended(img: np.ndarray, x_ratio=0.88, y_ratio=0.975):
    """双边混合向下渐变"""
    h, w, _ = img.shape
    x_start = int(w * x_ratio)
    y_start = int(h * y_ratio)
    # 自动计算全高度过渡
    transition_height = h - y_start  # 从起始到底部的全部行数
    # 预记录关键颜色数据
    left_col = img[y_start:, x_start - 1, :].copy()  # 纵向颜色带 (T,3)
    top_row = img[y_start, x_start:w, :].copy()  # 横向颜色带 (W,3)
    # 生成渐变系数矩阵
    if transition_height > 1:
        alpha = np.linspace(0, 0.5, transition_height)[:, np.newaxis, np.newaxis]  # (T,1,1)
    else:
        alpha = np.zeros((1, 1, 1))  # 单行特例
    # 维度对齐
    top_exp = top_row[np.newaxis, :, :]  # (1,W,3)
    left_exp = left_col[:, np.newaxis, :]  # (T,1,3)
    # 全区域渐变计算
    blended = (top_exp * (1 - alpha) + left_exp * alpha).astype(np.uint8)
    img[y_start:, x_start:w] = blended
    return img


def detect_hp_bar0(
    img: np.ndarray,
    roi: tuple[int, int, int, int] | None = None
):
    """
    检测血条

    参数:
        img:
            BGR np.ndarray

        roi:
            (x1, y1, x2, y2)
            只检测该区域

    返回:
        boxes:
            [(x, y, w, h)]

        mask:
            二值图
    """

    # ---------------------------
    # ROI 裁剪
    # ---------------------------
    if roi is not None:
        x1, y1, x2, y2 = roi
        detect_img = img[y1:y2, x1:x2]
    else:
        x1 = y1 = 0
        detect_img = img

    # ---------------------------
    # BGR -> HSV
    # ---------------------------
    hsv = cv2.cvtColor(detect_img, cv2.COLOR_BGR2HSV)

    # 红色范围
    # BGR(60, 75, 207) 大约对应 HSV(3, 181, 207)
    lower1 = np.array([0, 120, 120])
    upper1 = np.array([10, 255, 255])

    lower2 = np.array([170, 120, 120])
    upper2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)

    mask = mask1 | mask2

    # ---------------------------
    # morphology
    # ---------------------------
    kernel_open = np.ones((3, 3), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel_open
    )

    kernel_close = np.ones((1, 7), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel_close
    )

    # ---------------------------
    # 连通域
    # ---------------------------
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)

    boxes = []

    for i in range(1, num_labels):

        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        ratio = w / max(h, 1)

        if (
            w >= 40 and
            3 <= h <= 12 and
            ratio >= 4 and
            area >= 150
        ):
            # 转回原图坐标
            boxes.append((
                x + x1,
                y + y1,
                w,
                h
            ))

    return boxes


def detect_hp_bar(
    img: np.ndarray,
    roi: tuple[int, int, int, int] | None = None
):
    """
    检测血条（强化版：加入颜色一致性 + 横向稳定性）

    返回:
        [(x, y, w, h)]
    """

    # =================================================
    # ROI
    # =================================================
    if roi is not None:
        x1, y1, x2, y2 = roi
        detect_img = img[y1:y2, x1:x2]
    else:
        x1 = y1 = 0
        detect_img = img

    hsv = cv2.cvtColor(detect_img, cv2.COLOR_BGR2HSV)

    # =================================================
    # 红色 mask
    # =================================================
    lower1 = np.array([0, 120, 120])
    upper1 = np.array([10, 255, 255])

    lower2 = np.array([170, 120, 120])
    upper2 = np.array([180, 255, 255])

    mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)

    # =================================================
    # morphology（去噪 + 连通）
    # =================================================
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((1, 7), np.uint8))

    # =================================================
    # 连通域
    # =================================================
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)

    boxes = []

    for i in range(1, num_labels):

        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        # =================================================
        # 基础几何过滤
        # =================================================
        if w < 40:
            continue

        if not (3 <= h <= 12):
            continue

        if w / max(h, 1) < 4:
            continue

        if area < 150:
            continue

        # =================================================
        # 提取区域
        # =================================================
        roi_hsv = hsv[y:y+h, x:x+w]
        roi_mask = labels[y:y+h, x:x+w] == i

        pixels = roi_hsv[roi_mask]

        if len(pixels) < 30:
            continue

        # =================================================
        # 1. 颜色一致性（防特效/渐变）
        # =================================================
        h_std = pixels[:, 0].std()
        s_std = pixels[:, 1].std()
        v_std = pixels[:, 2].std()

        if h_std > 3:
            continue

        if s_std > 25:
            continue

        if v_std > 25:
            continue

        # =================================================
        # 2. 横向稳定性（核心增强）
        # =================================================
        xs = np.where(roi_mask)[1]
        hue = roi_hsv[:, :, 0][roi_mask]

        unique_x = np.unique(xs)

        col_means = np.array([
            hue[xs == x].mean()
            for x in unique_x
        ])

        if len(col_means) < 5:
            continue

        # 横向波动（关键）
        if col_means.std() > 2.5:
            continue

        # 防止“锯齿/闪烁条”
        if np.abs(np.diff(col_means)).mean() > 1.5:
            continue

        # =================================================
        # 3. 红色中心验证（防UI杂色）
        # =================================================
        mean_h = pixels[:, 0].mean()

        if not (mean_h <= 10 or mean_h >= 170):
            continue

        # =================================================
        # 输出
        # =================================================
        boxes.append((
            x + x1,
            y + y1,
            w,
            h
        ))

    return boxes


def draw_detect_hp_bar(img, boxes):
    draw = img.copy()

    # 绘制检测框
    for x, y, w, h in boxes:
        cv2.rectangle(
            draw,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            draw,
            f"{w}x{h}",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )
    return draw