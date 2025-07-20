import sys
import time
import subprocess

# Try to import pyautogui; install if missing
try:
    import pyautogui
except ImportError:
    print("pyautogui not found. Attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
        import pyautogui
    except Exception as e:
        print("Failed to install pyautogui: {}".format(e))
        print("Please install it manually and rerun the script.")
        sys.exit(1)

import msvcrt

# Prompt user for configuration

def get_float(prompt, allow_zero=False):
    while True:
        try:
            value = float(input(prompt).strip())
            if value < 0 or (value == 0 and not allow_zero):
                raise ValueError
            return value
        except ValueError:
            if allow_zero:
                print("Please enter a positive number or 0 for infinite.")
            else:
                print("Please enter a positive number.")

interval = get_float("Enter click interval in seconds: ")
count_limit = get_float("Enter total number of clicks (0 for infinite): ", allow_zero=True)

screen_width, screen_height = pyautogui.size()

F6 = b'@'   # scan code for F6
F7 = b'A'   # scan code for F7

print("\nPress F6 to start clicking and F7 to stop.")
print("Move the mouse to any corner of the screen to exit.\n")

# Wait for F6 to start
while True:
    if msvcrt.kbhit():
        first = msvcrt.getch()
        if first in (b'\x00', b'\xe0'):
            second = msvcrt.getch()
            if second == F6:
                break
            elif second == F7:
                sys.exit(0)
    time.sleep(0.1)

print("Started clicking. Press F7 to stop.")

click_count = 0
try:
    while True:
        # Stop if F7 pressed
        if msvcrt.kbhit():
            first = msvcrt.getch()
            if first in (b'\x00', b'\xe0'):
                second = msvcrt.getch()
                if second == F7:
                    print("Stop hotkey detected.")
                    break
        # Stop if moved to any screen corner
        x, y = pyautogui.position()
        if (x <= 0 and y <= 0) or (x >= screen_width - 1 and y <= 0) or (x <= 0 and y >= screen_height - 1) or (x >= screen_width - 1 and y >= screen_height - 1):
            print("Mouse moved to screen corner. Exiting.")
            break
        pyautogui.click()
        click_count += 1
        if count_limit and click_count >= count_limit:
            print("Reached target click count.")
            break
        time.sleep(interval)
except KeyboardInterrupt:
    print("Interrupted by user.")

print("Done. Restoring control.")

# Packaging note:
# To create a standalone executable, run:
# pyinstaller --onefile mouse_clicker.py
