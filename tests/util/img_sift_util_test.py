import logging
import time

import cv2

from src.core.geometry import AnchorBBox, AnchorPoint, Align, Scaler
from src.util import hwnd_util, file_util, screenshot_util, img_util
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
    SCREENSHOT_PATH = file_util.get_temp_screenshot("screenshot_1782024620_19912247.png")
    MAP_PATH_0_0 = file_util.get_assets_map("Roya Frostlands/Frostlands Surface/8_0_8.png")
    MAP_PATH_1_0 = file_util.get_assets_map("Roya Frostlands/Frostlands Surface/8_1_8.png")
    MAP_PATH_0_1 = file_util.get_assets_map("Roya Frostlands/Frostlands Surface/8_0_7.png")
    MAP_PATH_1_1 = file_util.get_assets_map("Roya Frostlands/Frostlands Surface/8_1_7.png")

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
        cv2.imread(MAP_PATH_0_0),
    )

    grid.add_tile(
        1,
        0,
        # cv2.imread("tile_1_0.png"),
        cv2.imread(MAP_PATH_1_0),
    )

    grid.add_tile(
        0,
        1,
        # cv2.imread("tile_0_1.png"),
        cv2.imread(MAP_PATH_0_1),
    )

    grid.add_tile(
        1,
        1,
        # cv2.imread("tile_1_1.png"),
        cv2.imread(MAP_PATH_1_1),
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


def test_identify_rolesV1():
    hwnd = hwnd_util.get_hwnd()
    img = screenshot_util.screenshot(hwnd)

    h, w = img.shape[:2]
    anchor_roi = AnchorBBox(
        AnchorPoint(1128, 0, Align.Left | Align.Top),
        AnchorPoint(1280, 720, Align.Left | Align.Top),
    )
    cur_roi = Scaler(cur_wh=(w, h)).as_bbox(anchor_roi)
    scene_image = img[cur_roi.as_slice()]

    matcher = SIFTFeatureMatcher(ransac_threshold=20)

    start_time = time.monotonic()
    role_features = []
    path = file_util.get_assets_avatar()
    for p in path.glob("*.png"):
        logger.debug(p.absolute())
        feature_image = img_util.read_img(p.absolute())
        feature_data = matcher.build_feature_data_masked(feature_id=p.name, image=feature_image)
        role_features.append(feature_data)

    use_time = time.monotonic() - start_time
    logger.debug("耗时: %s 秒", use_time)

    start_time = time.monotonic()
    results = matcher.identify_rolesV1(scene_image, role_features, top_k=8, min_good_matches=4, min_inliers=4)
    # results = matcher.identify_roles(scene_image, role_features, top_k=1, min_good_matches=4, min_inliers=4)
    use_time = time.monotonic() - start_time
    logger.debug("耗时: %s 秒", use_time)

    if not results:
        logger.debug("未识别到任何角色")
        cv2.imshow("window_name", scene_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    logger.debug(f"识别到 {len(results)} 个角色：")
    for i, result in enumerate(results):
        logger.debug(f"  - 角色ID: {result.feature_id}")
        logger.debug(f"    得分: {result.score:.2f}")
        logger.debug(f"    中心位置: {result.center}")
        logger.debug(f"    内点数: {result.inliers}")
        # 如果需要画框，使用 res.corners

        scene_xy = (466, 309)

        feature_xy = (
            matcher.scene_to_feature(
                result,
                scene_xy,
            )
        )

        logger.debug(
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

        logger.debug(
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


def test_identify_rolesV2():
    hwnd = hwnd_util.get_hwnd()
    img = screenshot_util.screenshot(hwnd)

    member_boxes = [
        AnchorBBox(
            AnchorPoint(1140, 116, Align.Top | Align.Right),
            AnchorPoint(1280, 210, Align.Top | Align.Right),
        ),
        AnchorBBox(
            AnchorPoint(1140, 210, Align.Top | Align.Right),
            AnchorPoint(1280, 300, Align.Top | Align.Right),
        ),
        AnchorBBox(
            AnchorPoint(1130, 300, Align.Top | Align.Right),
            AnchorPoint(1280, 400, Align.Top | Align.Right),
        ),
    ]

    for i, anchor_roi in enumerate(member_boxes):
        h, w = img.shape[:2]
        cur_roi = Scaler(cur_wh=(w, h)).as_bbox(anchor_roi)
        scene_image = img[cur_roi.as_slice()]

        matcher = SIFTFeatureMatcher()

        start_time = time.monotonic()
        role_features = []
        path = file_util.get_assets_avatar()
        for p in path.glob("*.png"):
            logger.debug(p.absolute())
            feature_image = img_util.read_img(p.absolute())
            feature_data = matcher.build_feature_data_masked(feature_id=p.name, image=feature_image)
            role_features.append(feature_data)

        use_time = time.monotonic() - start_time
        logger.debug("耗时: %s 秒", use_time)

        start_time = time.monotonic()
        results = matcher.identify_roles(scene_image, role_features)
        use_time = time.monotonic() - start_time
        logger.debug("耗时: %s 秒", use_time)

        if not results:
            logger.debug("未识别到任何角色")
            return

        logger.debug(f"识别到 {len(results)} 个角色：")
        for i, feature_id in enumerate(results):
            logger.debug(f"  - 角色ID: {feature_id}")
            # logger.debug(f"  - 角色ID: {result.feature_id}")
            # logger.debug(f"    得分: {result.score:.2f}")
            # logger.debug(f"    中心位置: {result.center}")
            # logger.debug(f"    内点数: {result.inliers}")

            cv2.imshow(str(feature_id), scene_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


