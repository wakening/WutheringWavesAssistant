import logging
import time

import dxcam
import numpy as np
from dxcam import DXCamera

from src.util import img_util, hwnd_util

logger = logging.getLogger(__name__)


def create_camera(
        device_idx: int = 0,
        output_idx: int = None,
        region: tuple[int, int, int, int] | None = None,
        output_color: str = "BGR",
        max_buffer_len: int = 64) -> DXCamera:
    camera = dxcam.create(
        device_idx=device_idx,
        output_idx=output_idx,
        region=region,
        output_color=output_color,
        max_buffer_len=max_buffer_len,
    )
    return camera


def screenshot(camera: DXCamera, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
    return camera.grab(region=region)


if __name__ == '__main__':
    hwnd = hwnd_util.get_hwnd()
    test_camera = create_camera()
    while True:
        test_region = hwnd_util.get_client_rect_on_screen(hwnd)
        frame = test_camera.grab(region=test_region)
        print(frame is None)
        if frame is not None:
            img_util.save_img_in_temp(frame)
        time.sleep(1)
