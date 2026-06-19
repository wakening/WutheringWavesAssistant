import threading
import time

from pynput import mouse, keyboard
from pynput.keyboard import Key

output_file = "recorded_mouse_clicks.txt"
events = []

# 上一次事件时间
last_time = time.time()

# 当前按下的键（用于过滤系统自动重复）
pressed_keys = set()

# 录制状态
is_recording = False

mouse_listener = None
keyboard_listener = None


def reset_timer():
    global last_time
    last_time = time.time()


def get_delay():
    global last_time
    now = time.time()
    delay_ms = int((now - last_time) * 1000)
    last_time = now
    return delay_ms


def record_delay():
    delay = get_delay()
    if delay > 0:
        print(f"Delay {delay}")
        events.append(f"Delay {delay}")


def on_click(x, y, button, pressed):
    if not is_recording:
        return

    record_delay()

    action = "Click" if pressed else "Release"
    msg = f"{action} {button} at ({x}, {y})"

    print(msg)
    events.append(msg)


def on_press(key):
    global is_recording

    try:
        # Z：开始/停止录制
        if hasattr(key, "char") and key.char == "z":
            if is_recording:
                print("🎬 停止录制")
                stop_recording()
                is_recording = False
            else:
                print("🎬 开始录制")
                events.clear()
                pressed_keys.clear()
                reset_timer()
                is_recording = True
                start_mouse_recording()
            return

        if not is_recording:
            return

        # 过滤按键自动重复
        if key in pressed_keys:
            return

        pressed_keys.add(key)

        if hasattr(key, "char") and key.char in {"e", "q", "r", "t"}:
            record_delay()
            msg = f"KeyDown {key.char}"
            print(msg)
            events.append(msg)

        elif key == Key.space:
            record_delay()
            print("KeyDown space")
            events.append("KeyDown space")

    except AttributeError:
        pass


def on_release(key):
    if not is_recording:
        return

    pressed_keys.discard(key)

    try:
        if hasattr(key, "char") and key.char in {"e", "q", "r", "t"}:
            record_delay()
            msg = f"KeyUp {key.char}"
            print(msg)
            events.append(msg)

        elif key == Key.space:
            record_delay()
            print("KeyUp space")
            events.append("KeyUp space")

    except AttributeError:
        pass


def start_mouse_recording():
    global mouse_listener

    if mouse_listener is None:
        mouse_listener = mouse.Listener(on_click=on_click)
        mouse_listener.start()


def stop_recording():
    global mouse_listener

    pressed_keys.clear()

    if mouse_listener:
        mouse_listener.stop()
        mouse_listener = None

    # save_events()


def save_events():
    with open(output_file, "w", encoding="utf-8") as f:
        for event in events:
            f.write(event + "\n")

    print(f"✅ 已保存：{output_file}")


def start_keyboard_listener():
    global keyboard_listener

    keyboard_listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
    )

    keyboard_listener.start()
    keyboard_listener.join()


keyboard_thread = threading.Thread(target=start_keyboard_listener, daemon=True)
keyboard_thread.start()
keyboard_thread.join()