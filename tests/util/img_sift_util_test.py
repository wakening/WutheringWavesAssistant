import logging

import cv2

from src.util import hwnd_util, file_util, screenshot_util
from src.util.img_sift_util import SIFTFeatureMatcher
from src.util.img_tile_util import TileGrid

logger = logging.getLogger(__name__)

hwnd_util.enable_dpi_awareness()


def test_SIFT():
    hwnd = hwnd_util.get_hwnd()
    img = screenshot_util.screenshot(hwnd)

    # 今州城
    MAP_PATH = file_util.get_assets_map("Huanglong/8_0_-1.png")

    matcher = SIFTFeatureMatcher()

    # =====================================================
    # Feature Image
    # =====================================================

    feature_image = cv2.imread(
        # "feature.png"
        MAP_PATH
    )

    if feature_image is None:
        raise FileNotFoundError(
            "feature.png"
        )

    # =====================================================
    # Build
    # =====================================================

    feature_data = (
        matcher.build_feature_data(
            feature_id="demo_feature",
            image=feature_image,
        )
    )

    # =====================================================
    # Export
    # =====================================================

    matcher.export_features(
        "demo_feature.npz",
        feature_data,
    )

    # =====================================================
    # Import
    # =====================================================

    feature_data = matcher.import_features(
        "demo_feature.npz",
        image=feature_image,
    )

    # =====================================================
    # Scene
    # =====================================================

    # scene_image = cv2.imread(
    #     # "scene.png"
    #     SCREENSHOT_PATH
    # )
    scene_image = img

    if scene_image is None:
        raise FileNotFoundError(
            "scene.png"
        )

    # =====================================================
    # Match
    # =====================================================

    result = matcher.match(
        scene_image=scene_image,
        feature_data=feature_data,
    )

    if result is None:
        logger.warning(
            "match failed"
        )

        raise SystemExit(1)

    # =====================================================
    # Coord Test
    # =====================================================

    scene_xy = (466, 309)

    feature_xy = (
        matcher.scene_to_feature(
            result,
            scene_xy,
        )
    )

    logger.info(
        "scene -> feature: %s -> %s",
        scene_xy,
        feature_xy,
    )

    reverse_scene_xy = (
        matcher.feature_to_scene(
            result,
            feature_xy,
        )
    )

    logger.info(
        "feature -> scene: %s -> %s",
        feature_xy,
        reverse_scene_xy,
    )

    # =====================================================
    # Debug Show
    # =====================================================

    matcher.debug_show(
        scene_image=scene_image,
        match_result=result,
    )


def test_tile():
    SCREENSHOT_PATH = file_util.get_temp_screenshot("screenshot_1778428516_74228928.png")
    MAP_PATH_909_2_0 = file_util.get_assets_map("Roya Frostlands/Dimmr Plains/909_2_0.png")
    MAP_PATH_909_3_0 = file_util.get_assets_map("Roya Frostlands/Dimmr Plains/909_3_0.png")
    MAP_PATH_909_2__1 = file_util.get_assets_map("Roya Frostlands/Dimmr Plains/909_2_-1.png")
    MAP_PATH_909_3__1 = file_util.get_assets_map("Roya Frostlands/Dimmr Plains/909_3_-1.png")

    # =========================================================
    # 1. 创建 TileGrid
    # =========================================================

    grid = TileGrid()

    # =========================================================
    # 2. 加载地图瓦片
    # =========================================================

    grid.add_tile(
        0,
        0,
        # cv2.imread("tile_0_0.png"),
        cv2.imread(MAP_PATH_909_2_0),
    )

    grid.add_tile(
        1,
        0,
        # cv2.imread("tile_1_0.png"),
        cv2.imread(MAP_PATH_909_3_0),
    )

    grid.add_tile(
        0,
        1,
        # cv2.imread("tile_0_1.png"),
        cv2.imread(MAP_PATH_909_2__1),
    )

    grid.add_tile(
        1,
        1,
        # cv2.imread("tile_1_1.png"),
        cv2.imread(MAP_PATH_909_3__1),
    )

    # =========================================================
    # 3. 拼接区域
    # =========================================================

    composite = grid.composite_region(
        min_x=0,
        min_y=0,

        max_x=1,
        max_y=1,
    )

    print(
        composite.image.shape
    )


    # cv2.imshow(
    #     "composite.image",
    #     composite.image,
    # )
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()



    # 现在：
    # 得到一张 2048x2048 大图

    # =========================================================
    # 4. 创建 Matcher
    # =========================================================

    matcher = SIFTFeatureMatcher()

    # =========================================================
    # 5. 构建 FeatureData
    # =========================================================

    feature_data = (
        matcher.build_feature_data(
            feature_id="region_0_0",

            image=composite.image,
        )
    )

    # =========================================================
    # 6. 读取游戏截图
    # =========================================================

    scene_image = cv2.imread(
        # "screenshot.png"
        SCREENSHOT_PATH
    )

    # =========================================================
    # 7. 匹配
    # =========================================================

    result = matcher.match(
        scene_image=scene_image,

        feature_data=feature_data,
    )

    if result is None:
        print("match failed")

        raise SystemExit

    # =========================================================
    # 8. 输出结果
    # =========================================================

    print(
        "center:",
        result.center
    )

    print(
        "scale:",
        result.scale_x,
        result.scale_y,
    )

    print(
        "score:",
        result.score
    )

    # =========================================================
    # 9. 显示结果
    # =========================================================

    matcher.debug_show(
        scene_image,
        result,
    )

def test_format():
    from PIL import Image
    MAP_PATH_909_2_0 = file_util.get_assets_map("Roya Frostlands/Dimmr Plains/909_2_0.png")
    img = Image.open(MAP_PATH_909_2_0)
    print(img.format)