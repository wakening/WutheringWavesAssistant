import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def read_img(img_path: str, alpha: bool | None = True) -> np.ndarray:
    """
    读取图片，返回BGR或BGRA
    :param img_path:
    :param alpha: 默认保留原图Alpha通道
    :return: BGR/BGRA ndarray，有没有Alpha通道取决于原图是否有
    """
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
    save_img(img_bgr, img_path)


def save_rgb_img(img_rgb: np.ndarray, img_path: str):
    """
    保存RGB图片
    :param img_rgb: 图片格式必需为RGB/RGBA
    :param img_path:
    :return:
    """
    logger.debug("Save image: %s", img_path)
    if img_rgb.shape[-1] == 4:  # BGRA 图像
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGBA2BGR)
    else:
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(img_path, img_bgr)


def show_img_plt(img: np.ndarray):
    from matplotlib import pyplot as plt
    # 使用 matplotlib 展示 numpy 数组图像
    plt.imshow(img)
    plt.axis('off')  # 关闭坐标轴
    plt.show()


def show_img(img: np.ndarray):
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
