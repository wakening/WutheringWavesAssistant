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

    def build_feature_data_masked(self, feature_id: str, image: np.ndarray) -> FeatureData:
        """
        构建特征数据
        """

        keypoints, descriptors = self._extract_features_masked(image)

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
            center=(center_x, center_y),
            corners=scene_corners,
        )

    def _extract_features_masked(self, image: np.ndarray):
        """
        带 Mask 的特征提取（用于透明图）
        :param image:
        :return:
        """
        if image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            mask = (image[:, :, 3] > 10).astype(np.uint8) * 255
            return self.sift.detectAndCompute(gray, mask)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return self.sift.detectAndCompute(gray, None)

    def identify_rolesV1(
            self,
            scene_image: np.ndarray,
            role_features_list: list[FeatureData],
            top_k: int = 5,  # 只对匹配点最多的前 K 个角色跑 RANSAC
            min_good_matches: int | None = None,  # 初筛阈值，默认等于 self.min_match_count
            min_inliers: int | None = None,  # 阈值，默认等于 self.min_match_count
    ) -> list[FeatureMatchResult]:
        """
        批量识别角色（优化版）
        - 场景 FLANN 索引只构建一次
        - 先快速初筛，只对候选跑 RANSAC
        """
        if min_good_matches is None:
            min_good_matches = self.min_match_count
        min_good_matches = max(min_good_matches, 4)
        if min_inliers is None:
            min_inliers = self.min_match_count  # 默认与原阈值一致
        min_inliers = max(min_inliers, 4)

        # =========================================================
        # 1. 提取场景特征（支持透明图 Mask）
        # =========================================================
        scene_kp, scene_desc = self._extract_features_masked(scene_image)
        if scene_desc is None or len(scene_kp) < min_good_matches:
            return []

        # =========================================================
        # 2. 构建场景 FLANN 索引（只构建一次！）
        # =========================================================
        # 注意：这里使用独立的 matcher 实例，避免污染 self.matcher 的默认状态
        scene_matcher = cv2.FlannBasedMatcher(
            dict(algorithm=1, trees=5),
            dict(checks=50)
        )
        scene_matcher.add([scene_desc])
        scene_matcher.train()

        # =========================================================
        # 3. 全量匹配 + Ratio Test（不截断！）
        # =========================================================
        candidates = []  # (good_count, feature_data, good_matches, src_pts, dst_pts)

        for fd in role_features_list:
            if fd.descriptors is None or len(fd.descriptors) < min_good_matches:
                continue

            # 利用预构建的索引进行快速查询（只传查询描述符，不传场景）
            matches = scene_matcher.knnMatch(fd.descriptors, k=2)

            good_matches = []
            for m, n in matches:
                if m.distance < self.ratio_test * n.distance:
                    good_matches.append(m)

            logger.debug(f"{fd.feature_id}, len: {len(good_matches)}, good_matches: {good_matches}")

            # 只有当匹配数达标时，才构建坐标点集（节省内存）
            if len(good_matches) >= min_good_matches:
                src_pts = np.float32([
                    fd.keypoints[m.queryIdx].pt for m in good_matches
                ]).reshape(-1, 1, 2)
                dst_pts = np.float32([
                    scene_kp[m.trainIdx].pt for m in good_matches
                ]).reshape(-1, 1, 2)

                candidates.append((len(good_matches), fd, good_matches, src_pts, dst_pts))

        if not candidates:
            return []

        # =========================================================
        # 4. 按匹配数排序，仅取 Top-K 进行 RANSAC（几何验证）
        # =========================================================
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = candidates[:top_k]

        results = []

        for _, fd, good_matches, src_pts, dst_pts in top_candidates:
            # 4.1 计算单应性矩阵
            matrix, mask = cv2.findHomography(
                src_pts, dst_pts, cv2.RANSAC, self.ransac_threshold
            )
            if matrix is None:
                continue

            success, inv_matrix = cv2.invert(matrix)
            if not success:
                continue

            # 4.2 统计内点
            inliers_mask = mask.ravel().tolist()
            inliers = sum(inliers_mask)
            if inliers < min_inliers:  # 内点不足则丢弃
                continue

            inlier_ratio = inliers / len(inliers_mask)

            # 4.3 计算缩放
            scale_x = math.sqrt(matrix[0, 0] ** 2 + matrix[1, 0] ** 2)
            scale_y = math.sqrt(matrix[0, 1] ** 2 + matrix[1, 1] ** 2)

            # 4.4 计算映射后的角点和中心
            h, w = fd.image.shape[:2]
            corners = np.float32([
                [0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]
            ]).reshape(-1, 1, 2)
            scene_corners = cv2.perspectiveTransform(corners, matrix)

            center_x = int(np.mean(scene_corners[:, 0, 0]))
            center_y = int(np.mean(scene_corners[:, 0, 1]))

            # 4.5 计算综合评分（内点率 * log(内点数)，兼顾质量与数量）
            score = inlier_ratio * math.log(inliers + 1)

            results.append(
                FeatureMatchResult(
                    feature_id=fd.feature_id,
                    matrix=matrix,
                    inverse_matrix=inv_matrix,
                    good_matches=good_matches,  # 这里保留了全部 good_matches，便于调试可视化
                    scene_keypoints=scene_kp,
                    scene_descriptors=scene_desc,
                    scale_x=scale_x,
                    scale_y=scale_y,
                    inliers=inliers,
                    inlier_ratio=inlier_ratio,
                    score=score,
                    center=(center_x, center_y),
                    corners=scene_corners,
                )
            )

        # =========================================================
        # 5. 按置信度得分降序返回
        # =========================================================
        results.sort(key=lambda x: x.score, reverse=True)
        return results


    def identify_roles(
            self,
            scene_image: np.ndarray,
            role_features_list: list[FeatureData],
            min_good_matches: int = 1,
    ) -> list[str]:
        top_k = 1
        if min_good_matches < 1:
            min_good_matches = 1

        # =========================================================
        # 1. 提取场景特征（支持透明图 Mask）
        # =========================================================
        scene_kp, scene_desc = self._extract_features_masked(scene_image)
        if scene_desc is None or len(scene_kp) < min_good_matches:
            return []

        # =========================================================
        # 2. 构建场景 FLANN 索引（只构建一次！）
        # =========================================================
        # 注意：这里使用独立的 matcher 实例，避免污染 self.matcher 的默认状态
        scene_matcher = cv2.FlannBasedMatcher(
            dict(algorithm=1, trees=5),
            dict(checks=50)
        )
        scene_matcher.add([scene_desc])
        scene_matcher.train()

        # =========================================================
        # 3. 全量匹配 + Ratio Test（不截断！）
        # =========================================================
        candidates = []  # (good_count, feature_data, good_matches, src_pts, dst_pts)

        for fd in role_features_list:
            if fd.descriptors is None or len(fd.descriptors) < min_good_matches:
                continue

            # 利用预构建的索引进行快速查询（只传查询描述符，不传场景）
            matches = scene_matcher.knnMatch(fd.descriptors, k=2)

            good_matches = []
            for m, n in matches:
                if m.distance < self.ratio_test * n.distance:
                    good_matches.append(m)

            logger.debug(f"{fd.feature_id}, len: {len(good_matches)}, good_matches: {good_matches}")
            candidates.append((len(good_matches), fd, good_matches))

        if not candidates:
            return []

        # =========================================================
        # 4. 按匹配数排序，仅取 Top-K 进行 RANSAC（几何验证）
        # =========================================================
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = candidates[:top_k]

        results = []

        for _, fd, good_matches in top_candidates:
            results.append(fd.feature_id)

        return results


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
