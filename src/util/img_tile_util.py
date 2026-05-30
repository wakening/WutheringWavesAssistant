import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# =========================================================
# Tile
# =========================================================

@dataclass(slots=True)
class Tile:
    """
    空间瓦片
    """

    x: int

    y: int

    image: np.ndarray


# =========================================================
# Composite Result
# =========================================================

@dataclass(slots=True)
class CompositeImage:
    """
    拼接结果
    """

    image: np.ndarray

    offset_x: int

    offset_y: int

    width: int

    height: int

    tiles: list[Tile]


# =========================================================
# Tile Grid
# =========================================================

class TileGrid:
    """
    通用瓦片网格系统

    支持：

    - tile 注册
    - 空间索引
    - 邻居查询
    - ROI 拼接
    - 区域合成
    """

    def __init__(self):

        self.tiles: dict[
            tuple[int, int],
            Tile
        ] = {}

    # =====================================================
    # Add
    # =====================================================

    def add_tile(
            self,
            x: int,
            y: int,
            image: np.ndarray,
    ):
        """
        注册瓦片
        """

        self.tiles[(x, y)] = Tile(
            x=x,
            y=y,
            image=image,
        )

        logger.debug(
            "add tile (%s, %s)",
            x,
            y,
        )

    # =====================================================
    # Get
    # =====================================================

    def get_tile(
            self,
            x: int,
            y: int,
    ) -> Tile | None:
        """
        获取瓦片
        """

        return self.tiles.get(
            (x, y)
        )

    # =====================================================
    # Neighbors
    # =====================================================

    def get_neighbors(
            self,
            x: int,
            y: int,
    ) -> list[Tile]:
        """
        获取8邻居
        """

        result = []

        for dy in (-1, 0, 1):

            for dx in (-1, 0, 1):

                if dx == 0 and dy == 0:
                    continue

                tile = self.get_tile(
                    x + dx,
                    y + dy,
                )

                if tile is not None:
                    result.append(tile)

        return result

    # =====================================================
    # Composite Region
    # =====================================================

    def composite_region(
            self,
            min_x: int,
            min_y: int,
            max_x: int,
            max_y: int,
    ) -> CompositeImage:
        """
        拼接区域
        """

        region_tiles = []

        # =================================================
        # Collect
        # =================================================

        for ty in range(
                min_y,
                max_y + 1,
        ):

            for tx in range(
                    min_x,
                    max_x + 1,
            ):

                tile = self.get_tile(
                    tx,
                    ty,
                )

                if tile is None:
                    raise ValueError(
                        f"missing tile: "
                        f"({tx}, {ty})"
                    )

                region_tiles.append(tile)

        # =================================================
        # Tile Size
        # =================================================

        first_tile = region_tiles[0]

        tile_h, tile_w = (
            first_tile.image.shape[:2]
        )

        # =================================================
        # Composite Size
        # =================================================

        cols = (
                max_x -
                min_x +
                1
        )

        rows = (
                max_y -
                min_y +
                1
        )

        composite_w = cols * tile_w

        composite_h = rows * tile_h

        # =================================================
        # Create Canvas
        # =================================================

        composite = np.zeros(
            (
                composite_h,
                composite_w,
                3,
            ),
            dtype=np.uint8,
        )

        # =================================================
        # Paste
        # =================================================

        for tile in region_tiles:
            px = (
                         tile.x -
                         min_x
                 ) * tile_w

            py = (
                         tile.y -
                         min_y
                 ) * tile_h

            composite[
                py:py + tile_h,
                px:px + tile_w,
            ] = tile.image

        logger.debug(
            "composite region: "
            "(%s,%s)-(%s,%s)",
            min_x,
            min_y,
            max_x,
            max_y,
        )

        return CompositeImage(
            image=composite,

            offset_x=min_x * tile_w,

            offset_y=min_y * tile_h,

            width=composite_w,

            height=composite_h,

            tiles=region_tiles,
        )

    # =====================================================
    # Composite Around
    # =====================================================

    def composite_around(
            self,
            center_x: int,
            center_y: int,
            radius: int = 1,
    ) -> CompositeImage:
        """
        以中心 tile 拼接周围区域

        radius=1:

            3x3

        radius=2:

            5x5
        """

        return self.composite_region(
            min_x=center_x - radius,
            min_y=center_y - radius,

            max_x=center_x + radius,
            max_y=center_y + radius,
        )

    # =====================================================
    # Debug Show
    # =====================================================

    @staticmethod
    def debug_show(
            composite_image: CompositeImage,
            window_name="composite",
    ):
        """
        调试显示
        """

        image = composite_image.image.copy()

        cv2.imshow(
            window_name,
            image,
        )

        cv2.waitKey(0)

        cv2.destroyAllWindows()


# =========================================================
# Demo
# =========================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(message)s"
        )
    )

    grid = TileGrid()

    # =====================================================
    # Load Tiles
    # =====================================================

    tile_0_0 = cv2.imread(
        "tile_0_0.png"
    )

    tile_1_0 = cv2.imread(
        "tile_1_0.png"
    )

    tile_0_1 = cv2.imread(
        "tile_0_1.png"
    )

    tile_1_1 = cv2.imread(
        "tile_1_1.png"
    )

    # =====================================================
    # Register
    # =====================================================

    grid.add_tile(
        0,
        0,
        tile_0_0,
    )

    grid.add_tile(
        1,
        0,
        tile_1_0,
    )

    grid.add_tile(
        0,
        1,
        tile_0_1,
    )

    grid.add_tile(
        1,
        1,
        tile_1_1,
    )

    # =====================================================
    # Composite
    # =====================================================

    composite = grid.composite_region(
        min_x=0,
        min_y=0,

        max_x=1,
        max_y=1,
    )

    logger.debug(
        "composite size: %sx%s",
        composite.width,
        composite.height,
    )

    # =====================================================
    # Show
    # =====================================================

    grid.debug_show(
        composite
    )
