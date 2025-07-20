import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

# Attempt to import required third-party libraries
try:
    import PySimpleGUI as sg
    import pyautogui
except Exception:
    # Fallback message using tkinter so we do not require PySimpleGUI
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependencies",
        "This script requires PySimpleGUI and pyautogui.\n"
        "Install with: pip install pysimplegui pyautogui",
    )
    sys.exit(1)

# ------------------------------ Utility Functions -----------------------------

def capture_click_position():
    """Capture a single mouse click position using a transparent Tk window."""
    coords = {}
    catcher = tk.Tk()
    catcher.attributes("-fullscreen", True)
    catcher.attributes("-alpha", 0.0)
    catcher.attributes("-topmost", True)

    def on_click(event):
        coords["x"] = event.x_root
        coords["y"] = event.y_root
        catcher.destroy()

    catcher.bind("<Button-1>", on_click)
    catcher.mainloop()
    return coords.get("x"), coords.get("y")


def mouse_in_corner():
    """Return True if mouse cursor is at any screen corner."""
    x, y = pyautogui.position()
    w, h = pyautogui.size()
    return (
        (x <= 0 and y <= 0)
        or (x >= w - 1 and y <= 0)
        or (x <= 0 and y >= h - 1)
        or (x >= w - 1 and y >= h - 1)
    )


# ----------------------------- GUI Layout -------------------------------------

def make_main_window():
    table_headings = ["Index", "X", "Y", "Clicks", "Interval (s)"]
    layout = [
        [sg.Text("Advanced Mouse Clicker", font=("Any", 16))],
        [sg.Button("Add Region", key="-ADD-"),
         sg.Button("Edit Selected", key="-EDIT-"),
         sg.Button("Delete Selected", key="-DEL-")],
        [sg.Table(
            values=[],
            headings=table_headings,
            auto_size_columns=False,
            col_widths=[6, 6, 6, 8, 12],
            key="-TABLE-",
            enable_events=True,
            justification="center",
            select_mode=sg.TABLE_SELECT_MODE_BROWSE,
        )],
        [sg.Frame(
            "Defaults for New Regions",
            [[sg.Text("Default Clicks"), sg.Input("1", size=(6,1), key="-DEF_CLICKS-")],
             [sg.Text("Default Interval"), sg.Input("1.0", size=(6,1), key="-DEF_INT-")]],
        )],
        [sg.Button("Start", key="-START-"), sg.Button("Stop", key="-STOP-")],
        [sg.Multiline(size=(50,10), key="-STATUS-", disabled=True)],
    ]
    return sg.Window("Advanced Mouse Clicker", layout, finalize=True)


# ----------------------------- Region Editing ---------------------------------

def edit_region_popup(region):
    layout = [
        [sg.Text(f"Edit Region {region['index']}")],
        [sg.Text("Clicks"), sg.Input(str(region['clicks']), key="-CLKS-")],
        [sg.Text("Interval (s)"), sg.Input(str(region['interval']), key="-INT-")],
        [sg.Button("OK"), sg.Button("Cancel")],
    ]
    win = sg.Window("Edit Region", layout, modal=True)
    event, values = win.read()
    win.close()
    if event == "OK":
        try:
            region['clicks'] = int(values['-CLKS-'])
            region['interval'] = float(values['-INT-'])
            return True
        except ValueError:
            sg.popup_error("Invalid values")
    return False


# ----------------------------- Click Thread -----------------------------------

def click_worker(regions, window, stop_event):
    try:
        for rindex, region in enumerate(regions, start=1):
            clicks = region['clicks']
            interval = region['interval']
            count = 0
            while not stop_event.is_set():
                if mouse_in_corner():
                    stop_event.set()
                    break
                pyautogui.click(region['x'], region['y'])
                count += 1
                window.write_event_value(
                    "-UPDATE-",
                    f"Clicking region {rindex}: {count}/{clicks if clicks else '∞'}"
                )
                if clicks and count >= clicks:
                    break
                time.sleep(interval)
            if stop_event.is_set():
                break
        window.write_event_value("-UPDATE-", "Done\n")
    except Exception as e:
        window.write_event_value("-UPDATE-", f"Error: {e}\n")


# ----------------------------- Main Application -------------------------------

def main():
    regions = []
    window = make_main_window()
    stop_event = threading.Event()
    click_thread = None

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            stop_event.set()
            break
        if event == "-ADD-":
            window.hide()
            x, y = capture_click_position()
            window.un_hide()
            if x is None:
                continue
            try:
                clicks = int(values["-DEF_CLICKS-"])
                interval = float(values["-DEF_INT-"])
            except ValueError:
                sg.popup_error("Invalid defaults")
                continue
            region = {
                'index': len(regions) + 1,
                'x': x,
                'y': y,
                'clicks': clicks,
                'interval': interval,
            }
            regions.append(region)
            window["-TABLE-"].update(values=[[r['index'], r['x'], r['y'], r['clicks'], r['interval']] for r in regions])
        elif event == "-EDIT-":
            selected = values["-TABLE-"]
            if selected:
                region = regions[selected[0]]
                if edit_region_popup(region):
                    window["-TABLE-"].update(values=[[r['index'], r['x'], r['y'], r['clicks'], r['interval']] for r in regions])
        elif event == "-DEL-":
            selected = values["-TABLE-"]
            if selected:
                index = selected[0]
                regions.pop(index)
                for i, r in enumerate(regions, start=1):
                    r['index'] = i
                window["-TABLE-"].update(values=[[r['index'], r['x'], r['y'], r['clicks'], r['interval']] for r in regions])
        elif event == "-START-" and not click_thread:
            if not regions:
                sg.popup_error("No regions defined")
                continue
            stop_event.clear()
            window["-STATUS-"].update("")
            click_thread = threading.Thread(target=click_worker, args=(regions, window, stop_event), daemon=True)
            click_thread.start()
        elif event == "-STOP-":
            stop_event.set()
            click_thread = None
        elif event == "-UPDATE-":
            window["-STATUS-"].print(values[event])
    window.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

# To bundle:
#   pyinstaller --onefile advanced_mouse_clicker.py
