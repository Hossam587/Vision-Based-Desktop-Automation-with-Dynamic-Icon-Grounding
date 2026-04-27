import cv2
import numpy as np
import pyautogui
import easyocr
import time
import requests
from rapidfuzz import fuzz

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
def find_notepad_coordinates(debug=True):
    img = capture_screen()

    results = reader.readtext(img)

    best_score = 0
    best_coords = None

    for (bbox, text, prob) in results:
        text_clean = text.lower()

        score = fuzz.partial_ratio(text_clean, TARGET)

        if score > best_score:
            (tl, tr, br, bl) = bbox

            center_x = int((tl[0] + br[0]) / 2)
            center_y = int((tl[1] + br[1]) / 2)

            icon_y = int(center_y - ICON_OFFSET_Y)

            best_score = score
            best_coords = (center_x, icon_y)

            if debug:
                cv2.rectangle(img,
                              (int(tl[0]), int(tl[1])),
                              (int(br[0]), int(br[1])),
                              (0, 255, 0), 2)

                cv2.putText(img, f"{text_clean}:{score}",
                            (int(tl[0]), int(tl[1]) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 1)

    if debug:
        cv2.imwrite("debug_detection.png", img)

    if best_score >= MATCH_THRESHOLD:
        print(f"✅ Found Notepad (score={best_score}) at {best_coords}")
        return best_coords

    print("⚠️ Notepad not found confidently")
    return None

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
def close_window():
    pyautogui.hotkey("alt", "f4")
    time.sleep(1)

# =============================
# OPEN NOTEPAD (RETRY)
# =============================
def open_notepad():
    for attempt in range(MAX_RETRIES):
        coords = find_notepad_coordinates()

        if coords is None:
            continue

        x, y = coords
        print(f"Clicking at {x}, {y}")

        pyautogui.doubleClick(x, y)
        time.sleep(2.5)

        if is_notepad_open():
            print("✅ Notepad opened")
            return True

        print("❌ Wrong app — closing")
        close_window()

    return False

# =============================
# FETCH POSTS
# =============================
def fetch_posts():
    return requests.get(
        "https://jsonplaceholder.typicode.com/posts"
    ).json()[:10]

# =============================
# WRITE / SAVE
# =============================
def write_post(post):
    text = f"Title: {post['title']}\n\n{post['body']}"
    pyautogui.write(text, interval=0.01)

def save_post(post_id):
    pyautogui.hotkey("ctrl", "s")
    time.sleep(1)

    pyautogui.write(f"post_{post_id}.txt")
    pyautogui.press("enter")

    time.sleep(1)

def close_notepad():
    pyautogui.hotkey("alt", "f4")
    time.sleep(1)

# =============================
# MAIN
# =============================
def main():
    print("Starting in 5 seconds...")
    time.sleep(5)

    posts = fetch_posts()

    for post in posts:
        print(f"\nProcessing post {post['id']}")

        success = open_notepad()

        if not success:
            print("Skipping...")
            continue

        write_post(post)
        save_post(post["id"])
        close_notepad()

    print("\nDone!")

# =============================
if __name__ == "__main__":
    main()