import logging

import cv2
import numpy as np

from src.core.geometry import IconBox

logger = logging.getLogger(__name__)


def find_icon_in_roi(
        img: np.ndarray,
        icon: np.ndarray,
        roi: tuple[int, int, int, int] | None = None,
        scale_min: float = 0.3,
        scale_max: float = 2.0,
        scale_step: float = 0.02,
):
    """
    Args:
        img:
            BGR截图

        icon:
            BGRA图标
            Alpha通道是真正图标

        roi:
            (x1, y1, x2, y2)

    Returns:
        {
            score,
            scale,
            x,
            y,
            w,
            h
        }
    """

    logger.debug("\n" + "=" * 80)
    logger.debug("Template Match Start")

    logger.debug(f"img.shape  = {img.shape}")
    logger.debug(f"icon.shape = {icon.shape}")

    if icon.shape[2] != 4:
        raise ValueError("icon必须是BGRA")

    # -------------------------------------------------
    # Alpha作为模板
    # -------------------------------------------------

    alpha = icon[:, :, 3]

    ys, xs = np.where(alpha > 0)

    if len(xs) == 0:
        raise ValueError("alpha为空")

    x1 = xs.min()
    x2 = xs.max() + 1

    y1 = ys.min()
    y2 = ys.max() + 1

    template = alpha[y1:y2, x1:x2]

    logger.debug(
        f"template bbox = "
        f"({x1},{y1}) -> ({x2},{y2})"
    )

    logger.debug(
        f"template size = "
        f"{template.shape[1]}x{template.shape[0]}"
    )

    # -------------------------------------------------
    # ROI
    # -------------------------------------------------

    if roi is None:
        roi_x1 = 0
        roi_y1 = 0

        roi_img = img
    else:
        roi_x1, roi_y1, roi_x2, roi_y2 = roi

        roi_img = img[
            roi_y1:roi_y2,
            roi_x1:roi_x2
        ]

    logger.debug()

    logger.debug(f"roi = ({roi_x1},{roi_y1})")

    logger.debug(f"roi_img.shape = {roi_img.shape}")

    # -------------------------------------------------
    # Gray
    # -------------------------------------------------

    roi_gray = cv2.cvtColor(
        roi_img,
        cv2.COLOR_BGR2GRAY
    )

    best_score = -1
    best_scale = None
    best_pos = None
    best_size = None

    results = []

    count = 0

    for scale in np.arange(
            scale_min,
            scale_max + scale_step,
            scale_step,
    ):

        w = int(template.shape[1] * scale)

        h = int(template.shape[0] * scale)

        if w < 8 or h < 8:
            continue

        if w >= roi_gray.shape[1]:
            continue

        if h >= roi_gray.shape[0]:
            continue

        resized = cv2.resize(
            template,
            (w, h),
            interpolation=cv2.INTER_LINEAR
        )

        result = cv2.matchTemplate(
            roi_gray,
            resized,
            cv2.TM_CCOEFF_NORMED
        )

        _, score, _, pos = cv2.minMaxLoc(result)

        results.append(
            (
                score,
                scale,
                pos,
                w,
                h,
            )
        )

        if score > best_score:
            best_score = score
            best_scale = scale
            best_pos = pos
            best_size = (w, h)

        count += 1

    logger.debug()
    logger.debug(f"scale scan count = {count}")

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    logger.debug()
    logger.debug("Top 10")
    logger.debug("-" * 80)

    for i, item in enumerate(results[:10]):
        score, scale, pos, w, h = item

        logger.debug(
            f"{i + 1:02d} "
            f"score={score:.4f} "
            f"scale={scale:.3f} "
            f"pos={pos} "
            f"size={w}x{h}"
        )

    logger.debug("-" * 80)

    if best_pos is None:
        return None

    x = best_pos[0] + roi_x1
    y = best_pos[1] + roi_y1

    logger.debug()
    logger.debug("Best")
    logger.debug(f"score = {best_score:.4f}")
    logger.debug(f"scale = {best_scale:.3f}")
    logger.debug(f"pos   = ({x}, {y})")
    logger.debug(f"size  = {best_size[0]}x{best_size[1]}")

    return {
        "score": best_score,
        "scale": best_scale,
        "x": x,
        "y": y,
        "w": best_size[0],
        "h": best_size[1],
    }


def _resize_img(
        img: np.ndarray,
        size_threshold: float = 1.15,
        ratio_threshold: float = 0.03,
        debug: bool = False,
) -> tuple[np.ndarray, float]:
    """
    模板匹配专用压缩图片函数，
    按 1280x720 基准缩放 UI 图，
    模板匹配的前置处理

    规则:
        - 小于基准 -> 不缩放
        - 稍微大一点 -> 不缩放
        - 明显大很多:
            超宽      -> 高缩放到720
            偏窄      -> 宽缩放到1280
            接近16:9 -> 高缩放到720
    """
    BASE_W = 1280
    BASE_H = 720
    BASE_RATIO = BASE_W / BASE_H

    h, w = img.shape[:2]

    if debug:
        logger.debug(f'Input: {w}x{h}')

    # -------------------------
    # 小于基准直接返回
    # -------------------------

    if w <= BASE_W and h <= BASE_H:
        if debug:
            logger.debug('Skip: smaller than base')
        return img, 1.0

    # -------------------------
    # 稍微大一点不处理
    # -------------------------

    if w <= BASE_W * size_threshold and h <= BASE_H * size_threshold:
        if debug:
            logger.debug('Skip: slightly larger than base')
        return img, 1.0

    # -------------------------
    # 计算比例
    # -------------------------

    ratio = w / h
    ratio_diff = abs(ratio - BASE_RATIO) / BASE_RATIO

    # 接近16:9
    if ratio_diff < ratio_threshold:

        scale = BASE_H / h
        reason = 'near 16:9 -> fit height'

    # 超宽
    elif ratio > BASE_RATIO:

        scale = BASE_H / h
        reason = 'ultra wide -> fit height'

    # 偏窄
    else:

        scale = BASE_W / w
        reason = 'narrow -> fit width'

    new_w = round(w * scale)
    new_h = round(h * scale)

    if debug:
        logger.debug(
            f'{reason}\n'
            f'Scale={scale:.4f}\n'
            f'Resize: {w}x{h} -> {new_w}x{new_h}'
        )

    new_img = cv2.resize(
        img,
        (new_w, new_h),
        interpolation=cv2.INTER_LINEAR,
    )
    return new_img, scale


def find_icon_in_roi_accelerated(
        img: np.ndarray,
        icon: np.ndarray,
        roi: tuple[int, int, int, int] | None = None,
        scale_min: float = 0.3,
        scale_max: float = 2.0,
        scale_step: float = 0.02,
        early_score: float = 0.9,
):
    if icon.shape[2] != 4:
        raise ValueError("icon必须是BGRA")

    # 缩放原图
    img_resized, resize_scale = _resize_img(img)
    logger.debug(f"[resize] scale={resize_scale:.3f}, shape={img_resized.shape}")

    # 提取 alpha 模板
    alpha = icon[:, :, 3]
    ys, xs = np.where(alpha > 0)
    if len(xs) == 0:
        raise ValueError("alpha为空")

    x1, x2 = xs.min(), xs.max() + 1
    y1, y2 = ys.min(), ys.max() + 1
    template = alpha[y1:y2, x1:x2]

    # ROI（同样缩放）
    if roi is None:
        roi_x1, roi_y1 = 0, 0
        roi_img = img_resized
    else:
        rx1, ry1, rx2, ry2 = roi

        roi_x1 = int(rx1 * resize_scale)
        roi_y1 = int(ry1 * resize_scale)
        roi_x2 = int(rx2 * resize_scale)
        roi_y2 = int(ry2 * resize_scale)

        roi_img = img_resized[roi_y1:roi_y2, roi_x1:roi_x2]

    roi_gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)

    # matching
    best_score = -1
    best_scale = None
    best_pos = None
    best_size = None

    for scale in np.arange(scale_min, scale_max + scale_step, scale_step):

        w = int(template.shape[1] * scale)
        h = int(template.shape[0] * scale)

        if w < 8 or h < 8:
            continue
        if w >= roi_gray.shape[1] or h >= roi_gray.shape[0]:
            continue

        resized = cv2.resize(template, (w, h), interpolation=cv2.INTER_LINEAR)
        result = cv2.matchTemplate(roi_gray, resized, cv2.TM_CCOEFF_NORMED)

        _, score, _, pos = cv2.minMaxLoc(result)

        # 当前结果
        cur_pos = pos
        cur_size = (w, h)

        # 更新 best
        if score > best_score:
            best_score = score
            best_scale = scale
            best_pos = cur_pos
            best_size = cur_size

        # early stop
        if score >= early_score:
            x1_r = int((cur_pos[0] + roi_x1) / resize_scale)
            y1_r = int((cur_pos[1] + roi_y1) / resize_scale)

            x2_r = int((cur_pos[0] + cur_size[0] + roi_x1) / resize_scale)
            y2_r = int((cur_pos[1] + cur_size[1] + roi_y1) / resize_scale)

            logger.debug(
                f"[early stop] score={score:.4f}, scale={scale:.3f}, "
                f"box=({x1_r},{y1_r},{x2_r},{y2_r})"
            )
            return IconBox(x1_r, y1_r, x2_r, y2_r, scale=scale, score=score)

    # 没命中 early stop，返回 best
    if best_pos is None:
        return None

    x1_r = int((best_pos[0] + roi_x1) / resize_scale)
    y1_r = int((best_pos[1] + roi_y1) / resize_scale)

    x2_r = int((best_pos[0] + best_size[0] + roi_x1) / resize_scale)
    y2_r = int((best_pos[1] + best_size[1] + roi_y1) / resize_scale)

    logger.debug(
        f"[best] score={best_score:.4f}, scale={best_scale:.3f}, "
        f"box=({x1_r},{y1_r},{x2_r},{y2_r})"
    )
    return IconBox(x1_r, y1_r, x2_r, y2_r, scale=best_scale, score=best_score)
