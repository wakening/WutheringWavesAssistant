import logging

import cv2

from src.core.geometry import Scaler, AnchorBBox, AnchorPoint, Align, BBox
from src.util import img_util, file_util, screenshot_util, hwnd_util, img_template_util

logger = logging.getLogger(__name__)


def test_find_icon_in_roi():
    atlas = img_util.read_img(
        file_util.get_assets_template("Guidebook_Sidebar.png"))
    icon = atlas[BBox(252, 28, 321, 105).as_slice()]

    # cv2.imshow(
    #     "alpha",
    #     icon[:, :, 3]
    # )
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    hwnd = hwnd_util.get_hwnd()
    img = screenshot_util.screenshot(hwnd)

    anchor_roi = AnchorBBox(
        AnchorPoint(0, 85, Align.Left | Align.Top),
        AnchorPoint(99, 720, Align.Left | Align.Top),
    )
    scale_table = {
        (1024, 768): 0.45,
        (1280, 720): 0.56,
        (1600, 900): 0.69,
        (1920, 1080): 0.83,
        (2560, 1440): 1.10,
    }

    rs_img, scale = img_template_util.resize_ui_img(img)
    h, w = rs_img.shape[:2]
    cur_roi = Scaler(cur_wh=(w, h)).as_bbox(anchor_roi)
    print(f"cur_roi: {cur_roi}, scale: {scale}, scale_roi: {cur_roi.scale(scale)}")

    result = img_template_util.find_icon_in_roi(
        # img,
        rs_img,
        icon,

        roi=cur_roi.as_tuple(),

        scale_min=0.4,
        scale_max=2.0,
        scale_step=0.03,
    )

    if result:
        preview = img.copy()

        x = result["x"]
        y = result["y"]
        w = result["w"]
        h = result["h"]

        # cv2.rectangle(
        #     preview,
        #     (x, y),
        #     (x + w, y + h),
        #     (0, 0, 255),
        #     2,
        # )

        cv2.rectangle(
            preview,
            (int(x / scale), int(y / scale)),
            (int((x + w) / scale), int((y + h) / scale)),
            (0, 0, 255),
            2,
        )

        cv2.imshow(
            "result",
            preview
        )

        cv2.waitKey(0)
        cv2.destroyAllWindows()


def test_find_icon_in_roi_accelerated():
    atlas = img_util.read_img(
        file_util.get_assets_template("Guidebook_Sidebar.png"))
    icon = atlas[BBox(252, 28, 321, 105).as_slice()]

    # cv2.imshow(
    #     "alpha",
    #     icon[:, :, 3]
    # )
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    hwnd = hwnd_util.get_hwnd()
    img = screenshot_util.screenshot(hwnd)

    anchor_roi = AnchorBBox(
        AnchorPoint(0, 85, Align.Left | Align.Top),
        AnchorPoint(99, 720, Align.Left | Align.Top),
    )

    h, w = img.shape[:2]
    cur_roi = Scaler(cur_wh=(w, h)).as_bbox(anchor_roi)
    print(f"cur_roi: {cur_roi}")

    result = img_template_util.find_icon_in_roi_accelerated(
        img,
        icon,

        roi=cur_roi.as_tuple(),

        scale_min=0.4,
        scale_max=2.0,
        scale_step=0.03,
    )

    if result:
        preview = img.copy()

        x1, y1, x2, y2 = result.as_tuple()

        cv2.rectangle(
            preview,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            2,
        )

        cv2.imshow(
            "result",
            preview
        )

        cv2.waitKey(0)
        cv2.destroyAllWindows()
