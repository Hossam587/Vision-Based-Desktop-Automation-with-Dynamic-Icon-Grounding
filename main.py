import cv2
import numpy as np
import pyautogui
import easyocr
import time
import requests
from rapidfuzz import fuzz
import pygetwindow as gw

# =============================
# CONFIG
# =============================
TARGET = "notepad"
MATCH_THRESHOLD = 70
ICON_OFFSET_Y = 45  # distance above text to click icon
MAX_RETRIES = 5

reader = easyocr.Reader(['en'], gpu=False)

# =============================
# SCREENSHOT
# =============================
def capture_screen():
    img = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    cv2.imwrite("debug_screen.png", img)
    return img

# =============================
# OCR DETECTION
# =============================
# def find_notepad_candidates(debug=True):
#     img = capture_screen()
#     results = reader.readtext(img)

#     candidates = []

#     for (bbox, text, prob) in results:
#         text_clean = text.lower()
#         score = fuzz.partial_ratio(text_clean, TARGET)

#         if score >= 50:  # collect more options
#             (tl, tr, br, bl) = bbox

#             center_x = int((tl[0] + br[0]) / 2)
#             center_y = int((tl[1] + br[1]) / 2)

#             icon_y = int(center_y - ICON_OFFSET_Y)

#             candidates.append((score, center_x, icon_y, bbox, text_clean))

#     # sort best first
#     candidates.sort(key=lambda x: x[0], reverse=True)

#     # DEBUG DRAW
#     if debug:
#         for score, cx, cy, bbox, text in candidates:
#             (tl, tr, br, bl) = bbox

#             color = (0, 0, 255)
#             if score > 70:
#                 color = (0, 255, 255)
#             if score > 85:
#                 color = (0, 255, 0)

            
#             cv2.rectangle(img,
#               (int(tl[0]), int(tl[1])),
#               (int(br[0]), int(br[1])),
#               color, 2)

#             # draw click point
#             cv2.circle(img, (cx, cy), 6, (255, 0, 0), -1)

#             cv2.putText(img, f"{text}:{score}",
#                         (int(tl[0]), int(tl[1]) - 5),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.4,
#                         color, 1)

#         cv2.imwrite("debug_detection.png", img)

#     return candidates

def find_notepad_candidates(debug=True):
    img = capture_screen()
    h, w = img.shape[:2]

    results = reader.readtext(img)
    candidates = []

    for (bbox, text, prob) in results:
        text_clean = text.lower().strip()
        score = fuzz.partial_ratio(text_clean, TARGET)

        if score < 60:   #slightly stricter
            continue

        (tl, tr, br, bl) = bbox

        center_x = int((tl[0] + br[0]) / 2)
        text_h = abs(br[1] - tl[1])
        text_w = abs(br[0] - tl[0])

        # ICON SIZE (adaptive)
        icon_height = max(70, int(text_h * 2.8))
        icon_width  = max(70, int(text_w * 2.0))

        # ICON BOX
        icon_top_y = int(tl[1] - icon_height)
        icon_bottom_y = int(br[1])

        icon_left_x = int(center_x - icon_width // 2)
        icon_right_x = int(center_x + icon_width // 2)

        # clamp
        icon_top_y = max(0, icon_top_y)
        icon_left_x = max(0, icon_left_x)
        icon_right_x = min(w, icon_right_x)
        icon_bottom_y = min(h, icon_bottom_y)

        # SAFE CLICK POINT (center of icon only)
        click_x = int((icon_left_x + icon_right_x) / 2)
        click_y = int(icon_top_y + icon_height * 0.4)

        candidates.append((score, click_x, click_y,
                           (icon_left_x, icon_top_y, icon_right_x, icon_bottom_y),
                           text_clean))

    candidates.sort(key=lambda x: x[0], reverse=True)

    # =============================
    # DEBUG DRAW (FULL ICON BOX)
    # =============================
    if debug:
        debug_img = img.copy()

        for score, cx, cy, bbox, text in candidates:
            x1, y1, x2, y2 = bbox

            color = (0, 0, 255)
            if score > 70:
                color = (0, 255, 255)
            if score > 85:
                color = (0, 255, 0)

            # ✅ FULL ICON BOX
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)

            # ✅ CLICK POINT
            cv2.circle(debug_img, (cx, cy), 6, (255, 0, 0), -1)

            cv2.putText(debug_img,
                        f"{text}:{score}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        color,
                        1)

        cv2.imwrite("debug_detection.png", debug_img)
        print("Saved debug image → debug_detection.png")

    return candidates

# =============================
# VERIFY NOTEPAD
# =============================
def is_notepad_open():
    titles = pyautogui.getAllTitles()
    for t in titles:
        if "notepad" in t.lower():
            return True
    return False

# =============================
# CLOSE WINDOW
# =============================
# def close_window():
#     pyautogui.hotkey("alt", "f4")
#     time.sleep(1)
def close_window():
    windows = gw.getWindowsWithTitle("Notepad")

    if windows:
        windows[0].activate()
        time.sleep(0.5)

        pyautogui.hotkey("alt", "f4")
        time.sleep(1)
    else:
        print("⚠️ Notepad not active — skipping close")

# =============================
# OPEN NOTEPAD (RETRY)
# =============================
def open_notepad():
    for attempt in range(3):  
        print(f"\nAttempt {attempt+1} to find Notepad")
        time.sleep(0.8)
        candidates = find_notepad_candidates()

        if not candidates:
            print("⚠️ No candidates — retrying...")
            time.sleep(1)
            continue

        for i, (score, x, y, _, text) in enumerate(candidates[:5]):
            print(f"Trying {i+1}: {text} ({score}) at ({x},{y})")

            pyautogui.doubleClick(x, y)

            #  wait with timeout
            for _ in range(5):
                time.sleep(0.5)
                if is_notepad_open():
                    print("✅ Notepad opened")
                    return True

            print("❌ Wrong app — closing")
            close_window()

    print("❌ Failed to open Notepad after retries")

    # fallback: show desktop (handle occlusion)
    print("Trying fallback: show desktop")
    pyautogui.hotkey("win", "d")
    time.sleep(1)

    return False

# =============================
# FETCH POSTS
# =============================
def fetch_posts():
    try:
        return requests.get(
            "https://jsonplaceholder.typicode.com/posts",
            timeout=5
        ).json()[:10]
    except:
        print(" API failed — using fallback data")
        return [
            {"id": i, "title": f"Fallback {i}", "body": "Sample content"}
            for i in range(1, 11)
        ]

# =============================
# WRITE / SAVE
# =============================
def write_post(post):
    text = f"Title: {post['title']}\n\n{post['body']}"
    pyautogui.write(text, interval=0.01)

# def save_post(post_id):
#     pyautogui.hotkey("ctrl", "s")
#     time.sleep(1)

#     filename = f"post_{post_id}.txt"
#     pyautogui.write(filename)
#     pyautogui.press("enter")
#     time.sleep(1)

#     # handle overwrite popup
#     pyautogui.press("left")   # select "Yes"
#     pyautogui.press("enter")
#     time.sleep(1)
# 
# def save_post(post_id):
#     # Focus Notepad first (VERY important)
#     window = gw.getWindowsWithTitle("Notepad")
#     if window:
#         window[0].activate()
#         time.sleep(0.5)

#     # Open Save dialog
#     pyautogui.hotkey("ctrl", "s")
#     time.sleep(1.5)

#     filename = f"post_{post_id}.txt"

#     # Clear any prefilled text (important for stability)
#     pyautogui.hotkey("ctrl", "a")
#     pyautogui.press("backspace")

#     pyautogui.write(filename, interval=0.01)
#     pyautogui.press("enter")

#     time.sleep(1)

#     # 🔴 KEY FIX: ensure dialog is gone and focus won't return to editor
#     pyautogui.press("esc")
#     time.sleep(0.3)

# def save_post(post_id):

#     pyautogui.hotkey("ctrl", "s")
#     time.sleep(1.5)   # IMPORTANT: give dialog time
#     filename = f"post_{post_id}.txt"
#     pyautogui.write(filename, interval=0.01)

#     #time.sleep(0.3)
#     pyautogui.press("enter")


    # Check for overwrite popup (best-effort)
    # if is_save_popup_open():
    #     print("Overwrite popup detected → confirming")

    #     pyautogui.press("left")   # move to "Yes"
    #     pyautogui.press("enter")
    #     time.sleep(1)
    # else:
    #print("Saved without overwrite popup")
def save_post(post_id):
    window = gw.getWindowsWithTitle("Notepad")
    if window:
        window[0].activate()
        time.sleep(0.5)

    pyautogui.hotkey("ctrl", "s")
    time.sleep(1.5)

    filename = f"post_{post_id}.txt"
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    pyautogui.write(filename, interval=0.01)
    pyautogui.press("enter")
    time.sleep(1)

    # If the "Confirm Save As" overwrite popup appears, it becomes the active window
    active_window = pyautogui.getActiveWindow()
    if active_window and "save as" in active_window.title.lower():
        print(f"⚠️ Overwrite popup detected for {filename} -> confirming")
        pyautogui.press("left")   # Move to "Yes"
        pyautogui.press("enter")
        time.sleep(1)
    else:
        print(f"✅ Saved {filename}")
def save_post(post_id):
    window = gw.getWindowsWithTitle("Notepad")
    if window:
        window[0].activate()
        time.sleep(0.5)

    pyautogui.hotkey("ctrl", "s")
    time.sleep(1.5)

    filename = f"post_{post_id}.txt"

    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")

    pyautogui.write(filename, interval=0.01)
    pyautogui.press("enter")
    
    # Give the system time to trigger the overwrite popup
    time.sleep(1.5) 

    # ==========================================
    # POINT 2 FIX: HANDLE OVERWRITE POPUP
    # ==========================================
    active_window = pyautogui.getActiveWindow()
    
    # Windows names this specific popup "Confirm Save As"
    if active_window and "confirm save as" in active_window.title.lower():
        print(f"⚠️ File '{filename}' already exists -> Overwriting")
        
        # In Windows, pressing Alt+Y is the built-in shortcut to click "Yes" 
        # on dialog boxes. It is safer than relying on Left/Right arrows.
        pyautogui.hotkey("alt", "y") 
        
        # Alternatively, if Alt+Y doesn't work on your specific OS version, use:
        # pyautogui.press("left")
        # pyautogui.press("enter")
        
        time.sleep(1)
    else:
        print(f"✅ Saved '{filename}' successfully.")

def is_save_popup_open():
    """
    Heuristic detection:
    If a dialog window is active (not Notepad),
    assume it's the overwrite popup.
    """
    try:
        window = pyautogui.getActiveWindow()

        if window is None:
            return False

        title = window.title.lower()

        # If it's NOT notepad → likely a dialog
        if "notepad" not in title:
            return True

    except:
        pass

    return False

# def close_notepad():
#     pyautogui.hotkey("alt", "f4")
#     time.sleep(1)

#     # handle "Save changes?" popup
#     if is_notepad_open():
#         pyautogui.press("right")  # move to "Don't Save"
#         pyautogui.press("enter")
#         time.sleep(1)
# def close_notepad():
#     window = gw.getWindowsWithTitle("Notepad")

#     if window:
#         window[0].activate()
#         time.sleep(0.5)

#         # force close immediately (prevents typing into editor)
#         pyautogui.hotkey("alt", "f4")
#         time.sleep(1)

#         # if "Save changes?" appears, discard it safely
#         pyautogui.press("right")  # move to Don't Save
#         pyautogui.press("enter")
#         time.sleep(1)
def close_notepad():
    windows = gw.getWindowsWithTitle("Notepad")

    if windows:
        windows[0].activate()
        time.sleep(0.5)

        pyautogui.hotkey("alt", "f4")
        time.sleep(1)

        # Check if a Notepad dialog ("Save changes?") is blocking the close
        active_window = pyautogui.getActiveWindow()
        if active_window and "notepad" in active_window.title.lower():
            print("⚠️ 'Save changes?' prompt detected -> Discarding")
            pyautogui.press("right")  # Move to "Don't Save"
            pyautogui.press("enter")
            time.sleep(1)
        else:
            print("✅ Notepad closed cleanly")
# =============================
# MAIN
# =============================
def main():
    print("Starting in 5 seconds...")
    time.sleep(5)

    posts = fetch_posts()

    for post in posts:
        # --- VERIFICATION STEP ---
        # Before opening a new one, make sure no Notepads are lingering
        existing_notepads = gw.getWindowsWithTitle("Notepad")
        for win in existing_notepads:
            print(f"🧹 Cleaning up leftover window: {win.title}")
            win.close() 
            time.sleep(0.5)
            # Handle the "Save changes?" if it appears during cleanup
            active = pyautogui.getActiveWindow()
            if active and "notepad" in active.title.lower():
                pyautogui.press("right") # Don't Save
                pyautogui.press("enter")
        print(f"\nProcessing post {post['id']}")

        success = open_notepad()

        if not success:
            print("Skipping this post — Notepad not available")
            continue

        write_post(post)
        save_post(post["id"])
        close_notepad()

    print("\nDone!")

# =============================
if __name__ == "__main__":
    main()