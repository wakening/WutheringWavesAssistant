import logging
import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# =========================================================
# Feature Data
# =========================================================

@dataclass(slots=True)
class FeatureData:
    """
    通用特征数据
    """

    feature_id: str

    image: np.ndarray

    keypoints: list

    descriptors: np.ndarray


# =========================================================
# Match Result
# =========================================================

@dataclass(slots=True)
class FeatureMatchResult:
    """
    特征匹配结果
    """

    feature_id: str

    matrix: np.ndarray

    inverse_matrix: np.ndarray

    good_matches: list

    scene_keypoints: list

    scene_descriptors: np.ndarray

    scale_x: float

    scale_y: float

    inliers: int

    inlier_ratio: float

    score: float

    center: tuple[int, int]

    corners: np.ndarray


# =========================================================
# SIFT Feature Matcher
# =========================================================

class SIFTFeatureMatcher:
    """
    通用 SIFT 特征匹配器

    支持：

    - 特征提取
    - 特征缓存
    - 特征导入导出
    - 特征匹配
    - Homography
    - 坐标映射
    - 调试显示
    """

    def __init__(
            self,
            ratio_test: float = 0.7,
            min_match_count: int = 15,
            ransac_threshold: float = 5.0,
    ):
        self.ratio_test = ratio_test
        self.min_match_count = min_match_count
        self.ransac_threshold = ransac_threshold

        self.sift = cv2.SIFT_create()

        # =================================================
        # FLANN
        # =================================================

        index_params = dict(
            algorithm=1,  # FLANN_INDEX_KDTREE
            trees=5,
        )

        search_params = dict(
            checks=50,
        )

        self.matcher = cv2.FlannBasedMatcher(
            index_params,
            search_params,
        )

    # =====================================================
    # Extract
    # =====================================================

    def extract_features(self, image: np.ndarray):
        """
        提取 SIFT 特征
        """

        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        keypoints, descriptors = self.sift.detectAndCompute(gray, None)

        logger.debug("extract features: kp=%s", len(keypoints))

        return keypoints, descriptors

    # =====================================================
    # Build Feature Data
    # =====================================================

    def build_feature_data(self, feature_id: str, image: np.ndarray) -> FeatureData:
        """
        构建特征数据
        """

        keypoints, descriptors = self.extract_features(image)

        return FeatureData(
            feature_id=feature_id,
            image=image,
            keypoints=keypoints,
            descriptors=descriptors,
        )

    # =====================================================
    # Export
    # =====================================================

    @staticmethod
    def export_features(path, feature_data: FeatureData):
        """
        导出特征数据
        """

        path = Path(path)

        kp_data = np.array([
            (
                kp.pt[0],
                kp.pt[1],
                kp.size,
                kp.angle,
                kp.response,
                kp.octave,
                kp.class_id,
            )
            for kp in feature_data.keypoints
        ], dtype=np.float32)

        np.savez_compressed(
            path,

            feature_id=feature_data.feature_id,

            keypoints=kp_data,

            descriptors=feature_data.descriptors,
        )

        logger.debug("export features: %s", path)

    # =====================================================
    # Import
    # =====================================================

    @staticmethod
    def import_features(path, image: np.ndarray) -> FeatureData:
        """
        导入特征数据
        """

        path = Path(path)

        data = np.load(path, allow_pickle=True)

        feature_id = str(data["feature_id"])

        keypoints_data = data["keypoints"]

        descriptors = data["descriptors"]

        keypoints = []

        for p in keypoints_data:
            kp = cv2.KeyPoint(
                x=float(p[0]),
                y=float(p[1]),
                size=float(p[2]),
                angle=float(p[3]),
                response=float(p[4]),
                octave=int(p[5]),
                class_id=int(p[6]),
            )

            keypoints.append(kp)

        logger.debug("import features: %s kp=%s", path, len(keypoints))

        return FeatureData(
            feature_id=feature_id,
            image=image,
            keypoints=keypoints,
            descriptors=descriptors,
        )

    # =====================================================
    # Match
    # =====================================================

    def match(
            self,
            scene_image: np.ndarray,
            feature_data: FeatureData,
    ) -> FeatureMatchResult | None:
        """
        特征匹配
        """

        scene_keypoints, scene_descriptors = self.extract_features(scene_image)

        if scene_descriptors is None:
            logger.warning("scene descriptors is None")

            return None

        # =================================================
        # Match
        # =================================================

        matches = self.matcher.knnMatch(
            feature_data.descriptors,
            scene_descriptors,
            k=2,
        )

        # =================================================
        # Ratio Test
        # =================================================

        good_matches = []

        for m, n in matches:

            if (
                    m.distance <
                    self.ratio_test * n.distance
            ):
                good_matches.append(m)

        logger.debug("good matches: %s", len(good_matches))

        if len(good_matches) < self.min_match_count:
            logger.warning("not enough matches")

            return None

        # =================================================
        # Point Mapping
        # =================================================

        src_pts = np.float32([
            feature_data.keypoints[m.queryIdx].pt
            for m in good_matches
        ]).reshape(-1, 1, 2)

        dst_pts = np.float32([
            scene_keypoints[m.trainIdx].pt
            for m in good_matches
        ]).reshape(-1, 1, 2)

        # =================================================
        # Homography
        # =================================================

        matrix, mask = cv2.findHomography(
            src_pts,
            dst_pts,
            cv2.RANSAC,
            self.ransac_threshold,
        )

        if matrix is None:
            logger.warning("homography failed")

            return None

        success, inverse_matrix = cv2.invert(matrix)

        if success == 0:
            logger.warning("invert homography failed")
            return None

        # =================================================
        # Inliers
        # =================================================

        inliers_mask = mask.ravel().tolist()

        inliers = sum(inliers_mask)

        inlier_ratio = inliers / len(inliers_mask)

        logger.debug("inliers: %s / %s", inliers, len(inliers_mask))

        # =================================================
        # Scale
        # =================================================

        scale_x = math.sqrt(
            matrix[0, 0] ** 2 +
            matrix[1, 0] ** 2
        )

        scale_y = math.sqrt(
            matrix[0, 1] ** 2 +
            matrix[1, 1] ** 2
        )

        logger.debug("scale_x=%.4f scale_y=%.4f", scale_x, scale_y)

        # =================================================
        # Corners
        # =================================================

        h, w = feature_data.image.shape[:2]

        feature_corners = np.float32([
            [0, 0],
            [0, h - 1],
            [w - 1, h - 1],
            [w - 1, 0],
        ]).reshape(-1, 1, 2)

        scene_corners = cv2.perspectiveTransform(feature_corners, matrix)

        # =================================================
        # Center
        # =================================================

        center_x = int(np.mean(scene_corners[:, 0, 0]))

        center_y = int(np.mean(scene_corners[:, 0, 1]))

        logger.debug("center=(%s, %s)", center_x, center_y)

        # =================================================
        # Score
        # =================================================

        score = inlier_ratio * math.log(inliers + 1)

        logger.debug("score=%.4f", score)

        return FeatureMatchResult(
            feature_id=feature_data.feature_id,

            matrix=matrix,

            inverse_matrix=inverse_matrix,

            good_matches=good_matches,

            scene_keypoints=scene_keypoints,

            scene_descriptors=scene_descriptors,

            scale_x=scale_x,

            scale_y=scale_y,

            inliers=inliers,

            inlier_ratio=inlier_ratio,

            score=score,

            center=(
                center_x,
                center_y,
            ),

            corners=scene_corners,
        )

    # =====================================================
    # Coord Mapping
    # =====================================================

    @staticmethod
    def scene_to_feature(
            match_result: FeatureMatchResult,
            scene_xy: tuple[float, float],
    ) -> tuple[float, float]:
        """
        场景坐标 -> 特征坐标
        """

        pt = np.array([[[scene_xy[0], scene_xy[1]]]], dtype=np.float32)

        result = cv2.perspectiveTransform(pt, match_result.inverse_matrix)

        x, y = result[0, 0]

        return float(x), float(y)

    @staticmethod
    def feature_to_scene(
            match_result: FeatureMatchResult,
            feature_xy: tuple[float, float],
    ) -> tuple[float, float]:
        """
        特征坐标 -> 场景坐标
        """

        pt = np.array(
            [[[feature_xy[0], feature_xy[1]]]],
            dtype=np.float32,
        )

        result = cv2.perspectiveTransform(
            pt,
            match_result.matrix,
        )

        x, y = result[0, 0]

        return float(x), float(y)

    # =====================================================
    # Debug Show
    # =====================================================

    def debug_show(
            self,
            scene_image: np.ndarray,
            match_result: FeatureMatchResult,
            window_name="result",
    ):
        """
        调试显示
        """

        scene = scene_image.copy()

        # =====================================================
        # 1. Draw composite corners
        # =====================================================

        corners = np.int32(match_result.corners)

        cv2.polylines(
            scene,
            [corners],
            True,
            (0, 255, 0),
            2,
        )

        # =====================================================
        # 2. Draw match ROI
        # =====================================================

        dst_pts = np.float32([
            match_result.scene_keypoints[
                m.trainIdx
            ].pt
            for m in match_result.good_matches
        ])

        x, y, w, h = cv2.boundingRect(dst_pts)

        cv2.rectangle(
            scene,
            (x, y),
            (x + w, y + h),
            (0, 255, 255),
            2,
        )

        # =====================================================
        # 3. Draw center
        # =====================================================

        center_x, center_y = match_result.center

        cv2.circle(
            scene,
            (center_x, center_y),
            8,
            (0, 0, 255),
            -1,
        )

        # =====================================================
        # 4. Draw text
        # =====================================================

        text = (
            f"{match_result.feature_id} | "
            f"inliers={match_result.inliers} | "
            f"score={match_result.score:.2f}"
        )

        cv2.putText(
            scene,
            text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        # =====================================================
        # Show
        # =====================================================

        cv2.imshow(window_name, scene)

        cv2.waitKey(0)

        cv2.destroyAllWindows()
