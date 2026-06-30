import logging
import os
import time

import cv2
import numpy as np
import onnxruntime
from rapidocr import RapidOCR

from src.util import file_util, img_util, hwnd_util, rapidocr_util, screenshot_util, yolo_util
from src.util.wrap_util import timeit

logger = logging.getLogger(__name__)

hwnd_util.enable_dpi_awareness()

# def test_warm():
#     engine: RapidOCR = rapidocr_util.create_ocr()
#     rapidocr_util.model_warmup(engine)


def test_ocr_from_game():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    img = screenshot_util.screenshot(hwnd)
    engine: RapidOCR = rapidocr_util.create_ocr()
    output = engine(img, use_det=True, use_rec=True, use_cls=False)
    rapidocr_util.print_ocr_result(output)
    img = img.copy()
    img = img_util.hide_uid(img)
    img_util.save_img_in_temp(img)
    img = rapidocr_util.draw_ocr_result(output)
    img_util.show_img(img)
    img_util.save_img_in_temp(img)


def test_ocr_rec_only_from_game():
    logger.debug("\n")
    hwnd = hwnd_util.get_hwnd()
    img = screenshot_util.screenshot(hwnd)
    img_util.save_img_in_temp(img)
    engine: RapidOCR = rapidocr_util.create_ocr()
    output = engine(img, use_det=True, use_rec=True, use_cls=False)
    logger.debug(output.__class__)
    # logger.debug(output)
    # rapidocr_util.print_ocr_result(output)
    # img = rapidocr_util.draw_ocr_result(output)
    # img_util.show_img(img)
    # img_util.save_img_in_temp(img)

    output = engine(img, use_det=False, use_rec=True, use_cls=False)
    logger.debug(output.__class__)
    from src.core.geometry import RapidocrRecTextBox
    result = RapidocrRecTextBox.format(output)
    logger.debug(f"result: {result}")
    # logger.debug(output)
    # rapidocr_util.print_ocr_result(output)
    # img = rapidocr_util.draw_ocr_result(output)
    # img_util.show_img(img)
    # img_util.save_img_in_temp(img)

    output = engine(img, use_det=True, use_rec=True, use_cls=True)
    logger.debug(output.__class__)
    # logger.debug(output)

    output = engine(img, use_det=False, use_rec=True, use_cls=True)
    logger.debug(output.__class__)
    # logger.debug(output)


def test_login_hwnd():
    logger.debug("\n")
    # hwnd_list_all, hwnd_list_visible = hwnd_util.get_login_hwnd_official()
    hwnd_list_all = hwnd_util.get_login_hwnd_official()
    #2026-06-24 11:00:07.949 - DEBUG - hwnd_util.get_login_hw...l:202 - window: 22022722, window class: #32770, title:
    #2026-06-24 11:00:07.949 - DEBUG - hwnd_util.get_login_hw...l:202 - window: 26347344, window class: KuroProtocolBgWin, title: Client

    # logger.debug("遍历所有登录窗口")
    # if hwnd_list_all is not None and len(hwnd_list_all) > 0:
    #     for login_hwnd in hwnd_list_all:
    #         get_window_info(login_hwnd)
    #         screenshot_util.screenshot(login_hwnd)

    engine: RapidOCR = rapidocr_util.create_ocr()
    if hwnd_list_all:
        logger.debug("遍历所有登录可见窗口")
        for login_hwnd in hwnd_list_all:
            logger.debug(f"login_hwnd: {login_hwnd}")
            try:
                img = screenshot_util.screenshot(login_hwnd)
                img_util.save_img_in_temp(img)
                output = engine(img, use_det=True, use_rec=True, use_cls=False)
                rapidocr_util.print_ocr_result(output)
                img = rapidocr_util.draw_ocr_result(output)
                img_util.show_img(img)
                img_util.save_img_in_temp(img)
            except Exception as e:
                logger.error(e)
    else:
        logger.debug("未找到登录窗口")


def test_ocr_from_dir():
    logger.debug("\n")
    img_path = file_util.get_temp_screenshot("screenshot_1778351945_69672602.png")
    # img_path = file_util.get_assets_screenshot("UI_F2_Guidebook_RecurringChallenges_001_EN.png")
    img = img_util.read_img(img_path)
    logger.debug(img.shape)
    engine: RapidOCR = rapidocr_util.create_ocr(use_dml=True)
    output = engine(img, use_det=True, use_rec=True, use_cls=False)
    rapidocr_util.print_ocr_result(output)
    img = rapidocr_util.draw_ocr_result(output)
    # img_util.show_img(img)
    img_util.save_img_in_temp(img)
    device = onnxruntime.get_device()
    logger.debug(f"Using device: {device}")
    logger.debug(f"Using device: {device}")
    logger.debug(f"Using device: {device}")


def test_ocr_from_dir_test_use_time():
    logger.debug("\n")
    engine: RapidOCR = rapidocr_util.create_ocr(use_gpu=True)
    img_name = "screenshot_1775218466_22742467.png" # 2560 1440
    # img_name = "screenshot_1778266376_85276790.png" # 1280 720
    img_path = file_util.get_temp_screenshot(img_name)
    img = img_util.read_img(img_path)
    logger.debug(img.shape)
    start_time = time.monotonic()
    warm_start_time = time.monotonic()
    # warm_img = img_util.read_img(file_util.get_assets_screenshot("Error_001.png"))
    warm_img = img_util.read_img(img_path)
    # img_util.resize(warm_img, 200)
    engine(warm_img, use_det=True, use_rec=True, use_cls=False)
    warm_use_time = time.monotonic() - warm_start_time
    logger.debug("预热耗时: %s 秒", warm_use_time)
    for i in range(100):
        h, w = img.shape[:2]
        new_img = img_util.resize_by_ratio(img, 540 / h)
        _time_use_test_rapidocr(engine, new_img)
    use_time = time.monotonic() - start_time
    # gpu pp   耗时: 0.041363 秒, 100次平均耗时: 0.043891 秒，总耗时: 5.687000000001717，耗时:  1.060301 秒 (第1次不计入平均值)
    # gpu onnx 耗时: 0.226402 秒, 100次平均耗时: 0.222805 秒，总耗时: 63.21899999999732，耗时: 41.112181 秒 (第1次不计入平均值)
    # cpu      耗时: 0.096748 秒, 100次平均耗时: 0.101701 秒，总耗时: 11.68700000000171，耗时:  1.375 秒 (第1次不计入平均值)
    # cpu dml  耗时: 0.069367 秒, 100次平均耗时: 0.076213 秒，总耗时: 9.296999999998661，耗时:  1.625 秒 (第1次不计入平均值)
    logger.debug("总耗时: %s 秒", use_time)
    logger.debug("总耗时: %s 秒", use_time)
    logger.debug("总耗时: %s 秒", use_time)


def test_ocr_from_dir_test_use_time2():
    logger.debug("\n")
    engine: RapidOCR = rapidocr_util.create_ocr()
    # img_path = file_util.get_temp_screenshot("screenshot_1742048600_50748456.png")
    # img = img_util.read_img(img_path)
    # logger.debug(img.shape)
    start_time = time.monotonic()
    warm_start_time = time.monotonic()
    warm_img = img_util.read_img(file_util.get_assets_screenshot("Error_001.png"))
    # img_util.resize(warm_img, 200)
    engine(warm_img, use_det=True, use_rec=True, use_cls=False)
    warm_use_time = time.monotonic() - warm_start_time
    logger.debug("预热耗时: %s 秒", warm_use_time)

    for root, dirs, files in os.walk(r"D:\Game\WutheringWavesAssistant\temp\screenshot\002"):
        for file in files:
            # 判断文件是否为 .png 格式
            if file.lower().endswith(".png"):
                logger.debug(file)
                _time_use_test_rapidocr(engine, img_util.read_img(os.path.abspath(os.path.join(root, file))))


    use_time = time.monotonic() - start_time
    # gpu pp   耗时: 0.248191 秒, 100次平均耗时: 0.255488 秒，总耗时: 26.38999999999941，耗时:  1.060301 秒 (第1次不计入平均值)
    # gpu onnx 耗时: 0.226402 秒, 100次平均耗时: 0.222805 秒，总耗时: 63.21899999999732，耗时: 41.112181 秒 (第1次不计入平均值)
    # cpu      耗时: 0.605177 秒, 100次平均耗时: 0.605542 秒，总耗时: 61.73500000000058，耗时:  1.763791 秒 (第1次不计入平均值)
    logger.debug("总耗时: %s 秒", use_time)
    logger.debug("总耗时: %s 秒", use_time)
    logger.debug("总耗时: %s 秒", use_time)



def pad_image(img, target_size=(640, 640), pad_color=(255, 0, 255)):
    """
    将 img 等比缩放到 target_size 的宽或高，
    原图位于上方，填充颜色为 pad_color。

    :param img: 输入的 np.ndarray 图片
    :param target_size: 目标尺寸 (宽, 高)
    :param pad_color: 填充颜色 (R, G, B)
    :return: 填充后的图片
    """
    h, w, c = img.shape

    # 计算缩放比例
    scale = target_size[1] / h if h > w else target_size[0] / w
    new_w, new_h = int(w * scale), int(h * scale)

    # 等比缩放图片
    resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # 创建目标图像并填充颜色
    canvas = np.full((target_size[1], target_size[0], c), pad_color, dtype=np.uint8)

    # 计算粘贴位置（居上）
    top = 0
    left = (target_size[0] - new_w) // 2

    # 将缩放后的图像粘贴到目标图像上
    canvas[top:top + new_h, left:left + new_w, :] = resized_img

    return canvas


def test_tianchogn():
    logger.debug("\n")
    engine: RapidOCR = rapidocr_util.create_ocr()
    # img_path = file_util.get_temp_screenshot("screenshot_1742048600_50748456.png")
    # img = img_util.read_img(img_path)
    # logger.debug(img.shape)
    start_time = time.monotonic()
    # warm_start_time = time.monotonic()
    # warm_img = img_util.read_img(file_util.get_assets_screenshot("Error_001.png"))
    # # img_util.resize(warm_img, 200)
    # engine(warm_img, use_det=True, use_rec=True, use_cls=False)
    # warm_use_time = time.monotonic() - warm_start_time
    # logger.debug("预热耗时: %s 秒", warm_use_time)


    input_dir = r"D:\Game\WutheringWavesAssistant\temp\screenshot\002"  # 指定输入目录
    output_dir = os.path.join(input_dir, "temp")
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)

        # 确保是文件且是图片
        if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = cv2.imread(file_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 转为 RGB 格式

            padded_img = pad_image(img)
            _time_use_test_rapidocr(engine, padded_img)
            # # 保存到 temp 目录
            # save_path = os.path.join(output_dir, file_name)
            # cv2.imwrite(save_path, cv2.cvtColor(padded_img, cv2.COLOR_RGB2BGR))

    use_time = time.monotonic() - start_time
    # gpu pp   耗时: 0.248191 秒, 100次平均耗时: 0.255488 秒，总耗时: 26.38999999999941，耗时:  1.060301 秒 (第1次不计入平均值)
    # gpu onnx 耗时: 0.226402 秒, 100次平均耗时: 0.222805 秒，总耗时: 63.21899999999732，耗时: 41.112181 秒 (第1次不计入平均值)
    # cpu      耗时: 0.605177 秒, 100次平均耗时: 0.605542 秒，总耗时: 61.73500000000058，耗时:  1.763791 秒 (第1次不计入平均值)
    logger.debug("总耗时: %s 秒", use_time)
    logger.debug("总耗时: %s 秒", use_time)
    logger.debug("总耗时: %s 秒", use_time)


def test_yolo_util():
    logger.debug("\n")
    img_path = file_util.get_temp_screenshot("screenshot_1742048600_50748456.png")
    img = img_util.read_img(img_path)
    logger.debug(img.shape)
    models = [
        r"D:\Tools\miniconda3\envs\WutheringWavesAssistant\Lib\site-packages\rapidocr\models\ch_PP-OCRv4_det_infer.onnx",
        r"D:\Tools\miniconda3\envs\WutheringWavesAssistant\Lib\site-packages\rapidocr\models\ch_PP-OCRv4_rec_infer.onnx",
    ]
    for model in models:
        yyy_test(img, model)

def yyy_test(img, model):
    start_time = time.monotonic()
    ort_provider = yolo_util.get_ort_providers()
    ort_session_options = yolo_util.create_ort_session_options()
    session = yolo_util.create_ort_session(
        model_path=model, providers=ort_provider, sess_options=ort_session_options
    )
    input_shape = session.get_inputs()[0].shape
    logger.debug("Model input shape: %s", input_shape)  # [1, 3, 640, 640] NCHW
    img_process, ratio, pad = yolo_util.preprocess(img)
    outputs = yolo_util.run_ort_session(session, img_process)
    logger.debug(outputs)
    use_time = time.monotonic() - start_time
    logger.debug("总耗时: %s", use_time)
    logger.debug("总耗时: %s", use_time)
    logger.debug("总耗时: %s", use_time)


@timeit
def _time_use_test_rapidocr(engine, img):
    output = engine(img, use_det=True, use_rec=False, use_cls=False)


def test_ocr_login():
    logger.debug("\n")
    img_path = file_util.get_assets_screenshot("Login_001.png")
    img = img_util.read_img(img_path)
    # paddleocr = paddleocr_util.create_paddleocr()
    # results = paddleocr_util.execute_paddleocr(paddleocr, img)
    # paddleocr_util.print_paddleocr_result(results)
    # img = paddleocr_util.draw_paddleocr_result(results, img)
    # img_util.show_img(img)
    # img_util.save_img_in_temp(img)
