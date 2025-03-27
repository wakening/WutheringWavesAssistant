import ctypes
import logging

import numpy as np
import win32con
import win32gui
import win32ui

logger = logging.getLogger(__name__)


def screenshot(hwnd, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
    """ 截图，返回只读BGR图片 """
    if region is None:
        region = win32gui.GetClientRect(hwnd)
    left, top, right, bottom = region
    width = right - left
    height = bottom - top

    # 获取窗口设备上下文
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    # 创建兼容位图
    save_bitmap = win32ui.CreateBitmap()
    save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(save_bitmap)

    # 尝试使用PrintWindow截图
    ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
    # result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
    # result: 1
    # logger.debug("result: %d", result)
    # if not result:
    #     # 回退到BitBlt
    #     save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

    # 获取位图数据
    bmp_info = save_bitmap.GetInfo()
    bmp_str = save_bitmap.GetBitmapBits(True)
    # bmp_mutable = bytearray(bmp_str)  # 可读写，加载到Python层面处理

    # 转换为NumPy数组
    img = np.frombuffer(bmp_str, dtype=np.uint8)

    # 处理位图参数
    bits_pixel = bmp_info['bmBitsPixel']
    bytes_per_pixel = bits_pixel // 8
    bm_width = bmp_info['bmWidth']
    bm_height = bmp_info['bmHeight']
    bm_width_bytes = bmp_info['bmWidthBytes']

    # 处理每行的填充字节
    bytes_per_row = bm_width * bytes_per_pixel
    pad_bytes = bm_width_bytes - bytes_per_row

    if pad_bytes > 0:
        img = img.reshape((bm_height, bm_width_bytes))
        img = img[:, :bytes_per_row].reshape(-1)

    # 调整数组形状并处理颜色通道
    img = img.reshape((bm_height, bm_width, bytes_per_pixel))

    if bytes_per_pixel == 4:
        img = img[..., :3]  # 去除Alpha通道
    elif bytes_per_pixel != 3:
        raise NotImplementedError(f"不支持的颜色深度: {bits_pixel}位/像素")

    # 清理资源
    win32gui.DeleteObject(save_bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    return img


def screenshot_bitblt(hwnd, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
    """
    截取指定窗口的指定区域，并返回 BGR 格式的 `numpy.ndarray`

    :param hwnd: 窗口句柄（int）
    :param region: (left, top, right, bottom) 截图区域
    :return: 截取的 BGR 格式图像，`numpy.ndarray`
    """
    if region is None:
        region = win32gui.GetClientRect(hwnd)
    left, top, right, bottom = region
    width, height = right - left, bottom - top

    # 获取窗口 DC（设备上下文）
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    # 创建兼容位图（仅分配指定区域大小的内存）
    save_bitmap = win32ui.CreateBitmap()
    save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(save_bitmap)

    # 直接拷贝指定区域到位图
    save_dc.BitBlt((0, 0), (width, height), mfc_dc, (left, top), win32con.SRCCOPY)

    # 提取位图数据（BGRA 格式）
    bmpinfo = save_bitmap.GetInfo()
    bmpstr = save_bitmap.GetBitmapBits(True)

    # 转换为 numpy 数组
    img = np.frombuffer(bmpstr, dtype=np.uint8)
    img = img.reshape((bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4))  # BGRA 格式（4通道）

    # 释放资源
    win32gui.DeleteObject(save_bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    # 去掉未使用的 Alpha 通道（BGRA → BGR）
    img = img[:, :, :3]

    return img
