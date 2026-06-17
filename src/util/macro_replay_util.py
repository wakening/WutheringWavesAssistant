import ctypes
import logging
import threading
import time
from dataclasses import dataclass

from typing import List, Union

# 声明：
# 初始回放代码来自B站up主 _-_7777777_-_ 分享的powershell录制脚本，重写为py版，录制脚本参考他的exe工具复现，录好的模板也来自他和评论区

logger = logging.getLogger(__name__)

# =========================
# WinAPI
# =========================

user32 = ctypes.WinDLL("user32", use_last_error=True)
winmm = ctypes.WinDLL("winmm")

timeBeginPeriod = winmm.timeBeginPeriod
timeEndPeriod = winmm.timeEndPeriod

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0

KEYEVENTF_KEYUP = 0x0002

MOUSE_LEFTDOWN = 0x0002
MOUSE_LEFTUP = 0x0004
MOUSE_RIGHTDOWN = 0x0008
MOUSE_RIGHTUP = 0x0010
MOUSE_MIDDLEDOWN = 0x0020
MOUSE_MIDDLEUP = 0x0040


# =========================
# 结构体
# =========================

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_uint),
        ("time", ctypes.c_uint),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_uint),
        ("dwFlags", ctypes.c_uint),
        ("time", ctypes.c_uint),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint),
        ("union", INPUT_UNION),
    ]


# =========================
# 数据结构
# =========================

@dataclass
class KeyEvent:
    time_ms: int
    vk: Union[int, str]
    is_down: bool


# =========================
# 解析文件
# =========================

def parse_file(path: str) -> List[KeyEvent]:
    logger.info(f"读取文件: {path}")

    events = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) < 3:
                continue

            try:
                ms = int(parts[0])
                key = parts[1]

                vk = key if key.startswith("MOUSE") else int(key)
                is_down = int(parts[2]) == 1

                events.append(KeyEvent(ms, vk, is_down))
            except:
                continue

    events.sort(key=lambda e: e.time_ms)
    return events


# =========================
# 输入发送
# =========================

def build_input(event: KeyEvent):
    if isinstance(event.vk, int):
        flags = 0 if event.is_down else KEYEVENTF_KEYUP
        return INPUT(
            type=INPUT_KEYBOARD,
            union=INPUT_UNION(
                ki=KEYBDINPUT(event.vk, 0, flags, 0, None)
            )
        )

    if event.vk == "MOUSE_LEFT":
        flags = MOUSE_LEFTDOWN if event.is_down else MOUSE_LEFTUP
    elif event.vk == "MOUSE_RIGHT":
        flags = MOUSE_RIGHTDOWN if event.is_down else MOUSE_RIGHTUP
    elif event.vk == "MOUSE_MIDDLE":
        flags = MOUSE_MIDDLEDOWN if event.is_down else MOUSE_MIDDLEUP
    else:
        return None

    return INPUT(
        type=INPUT_MOUSE,
        union=INPUT_UNION(
            mi=MOUSEINPUT(0, 0, 0, flags, 0, None)
        )
    )


def send_batch(events: List[KeyEvent]):
    inputs = []
    for e in events:
        inp = build_input(e)
        if inp:
            inputs.append(inp)

    if not inputs:
        return

    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), ctypes.byref(arr), ctypes.sizeof(INPUT))


# =========================
# 高精度时间轴（统一相对时间）
# =========================

class HybridTimer:
    def __init__(self):
        self.start = time.perf_counter()

    def wait_until(self, target_ms, stop_flag):
        target = target_ms / 1000

        while True:
            if stop_flag():
                return False

            now = time.perf_counter() - self.start
            remaining = target - now

            if remaining <= 0:
                return True

            if remaining > 0.25:
                time.sleep(0.20)
            elif remaining > 0.01:
                time.sleep(remaining - 0.005)
            elif remaining > 0.002:
                time.sleep(0.001)
            # 太卡，掉帧
            # elif remaining > 0.0003:
            #     time.sleep(0)
            # else:
            # while (time.perf_counter() - self.start) < target:
            #     if stop_flag():
            #         return False
            #     time.sleep(0)  # 让出时间片
            # return True
            else:
                time.sleep(0.001)
                if (time.perf_counter() - self.start) >= target:
                    return True


# =========================
# 回放器
# =========================

class MacroPlayer:
    def __init__(self):
        self._stop = False
        self._pressed_keys = set()  # 记录当前按下的键（vk 或字符串）

    def stop(self):
        self._stop = True

    def _release_all_keys(self):
        """补发所有未释放按键的弹起事件，防止卡键"""
        if not self._pressed_keys:
            return
        logger.info(f"释放残留按键: {self._pressed_keys}")
        release_events = [KeyEvent(0, key, False) for key in self._pressed_keys]
        send_batch(release_events)
        self._pressed_keys.clear()

    def play(self, events: List[KeyEvent]):
        if not events:
            return

        # timeBeginPeriod(1)

        try:
            first_time = 0
            timer = HybridTimer()
            i = 0
            n = len(events)

            # logger.info("开始播放")

            while i < n:
                if self._stop:
                    logger.info("停止播放")
                    self._release_all_keys()  # 中断时立即释放
                    return

                e = events[i]
                target = e.time_ms - first_time
                go = timer.wait_until(target, lambda: self._stop)
                if not go:
                    self._release_all_keys()
                    return

                batch = []
                base = e.time_ms

                while i < n and abs(events[i].time_ms - base) <= 1:
                    batch.append(events[i])
                    i += 1

                # =========================
                # DEBUG（已关闭）
                # =========================
                # for x in batch:
                #     logger.info(f"vk={x.vk} down={x.is_down}")

                # 记录按键状态变化
                for evt in batch:
                    if evt.is_down:
                        self._pressed_keys.add(evt.vk)
                    else:
                        self._pressed_keys.discard(evt.vk)

                send_batch(batch)

            logger.info("播放完成")
        finally:
            self._release_all_keys()  # 正常结束时再次确保清空（集合应为空）
            # timeEndPeriod(1)


# =========================
# 触发（只做启动）
# =========================

class TriggerController:

    POINTS_1280_720 = [(1136, 77), (1138, 83), (1141, 89), (1219, 38), (1219, 44)]

    def __init__(self, hwnd=None, points=None):
        self.key = 0x4A  # J
        self.hwnd = hwnd
        self.points = points

    def wait_trigger(self):
        logger.info("等待 J 触发...")

        last = False

        while True:
            state = (user32.GetAsyncKeyState(self.key) & 0x8000) != 0

            if state and not last:
                t = time.perf_counter()

                while (user32.GetAsyncKeyState(self.key) & 0x8000):
                    time.sleep(0)

                logger.info("J触发完成")
                return t

            last = state
            time.sleep(0.001)

    def wait_color(self, should_stop=None):
        hwnd = self.hwnd

        from src.util import hwnd_util, screenshot_util
        if not hwnd:
            hwnd_util.enable_dpi_awareness()
            hwnd = hwnd_util.get_hwnd()
        hwnd_util.window_activate(hwnd)

        points = self.points
        if not points:
            # 此处仅支持16:9
            w, h = hwnd_util.get_client_wh(hwnd)
            ratio = h / 720
            points = [(int(x * ratio), int(y * ratio)) for x, y in self.POINTS_1280_720]

        while True:
            if should_stop and should_stop():
                logger.info("等待触发已取消")
                return False  # 返回 False 表示未触发成功

            if not hwnd_util.is_foreground_window(hwnd):
                time.sleep(0.01)
                continue

            # img = mss_util.screenshot(client, region)
            # mss前台截图有延迟，判断已是前台但仍获取到旧的截图，正好脚本也是白色，会误判，改用后台截图
            img = screenshot_util.screenshot(hwnd)
            check = True
            for point in points:
                bgr = img[point[1]][point[0]]
                # color_bgr = (233, 233, 233)
                if bgr[0] > 225 and bgr[1] > 225 and bgr[2] > 225:
                    continue
                check = False
                break

            if check:
                logger.info("发现点位，开始回放")
                # from src.util import img_util
                # img_util.save_img_in_temp(img)
                break

            time.sleep(0.01)

        return True


# =========================
# ESC（测试）
# =========================

def start_esc(player: MacroPlayer):
    def loop(event):
        while event.is_set():
            if user32.GetAsyncKeyState(0x1B) & 0x8000:
                player.stop()
                logger.info("ESC退出")
                return
            time.sleep(0.02)

    event = threading.Event()
    esc_thread = threading.Thread(target=loop, args=(event,), daemon=True)
    event.set()
    esc_thread.start()
    return esc_thread, event


# =========================
# main
# =========================

def run(path: str, hwnd=None, points=None):
    events = parse_file(path)

    player = MacroPlayer()
    trigger = TriggerController(hwnd, points)

    esc_thread, event = start_esc(player)

    try:
        timeBeginPeriod(1)
        # trigger.wait_trigger()
        trigger.wait_color(should_stop=lambda: player._stop)

        # time.sleep(0.030)  # 模拟延迟

        player.play(events)
    finally:
        timeEndPeriod(1)
        event.clear()


if __name__ == "__main__":
    from src.util import file_util

    path = file_util.get_assets_macro_SoarToTheBeat_template("05_星云漫游_《致那暖明黄金》_困难.txt")

    logger.info(path)
    logger.info("准备就绪，等待开始")
    run(path)
