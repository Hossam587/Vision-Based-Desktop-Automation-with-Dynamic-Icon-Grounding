# Vision-Based-Desktop-Automation-with-Dynamic-Icon-Grounding
Develop a Python application that uses computer vision to dynamically locate and interact with desktop icons on Windows (1920x1080 resolution). The system must find the Notepad icon regardless of its position on the desktop, enabling robust automation even when icon positions change.
# Notepad Automation Script

This repository contains a Windows automation script that uses OCR and GUI control to open Notepad, fetch sample posts from a remote API, type the post content into Notepad, save each file as `post_<id>.txt`, and close Notepad.

## What it does

- Takes a screenshot of the desktop
- Uses `easyocr` to find a visible `Notepad` label or icon text
- Clicks the detected Notepad area to open the app
- Fetches 10 posts from `https://jsonplaceholder.typicode.com/posts`
- Writes each post into Notepad
- Saves each post as `post_<id>.txt`
- Closes Notepad cleanly, dismissing save prompts when needed

## Requirements

- Windows OS
- Python 3.8+ recommended
- Notepad must be visible or detectable on screen
- Screen must not be blocked by full-screen apps while automation runs

## Python dependencies

Install the required packages with:

```bash
pip install opencv-python numpy pyautogui easyocr requests rapidfuzz pygetwindow
```

> Note: `pyautogui` may also require `pillow`, which is normally installed as a dependency.

## Usage

Run the script from the project root:

```bash
python main.py
```

The script pauses for 5 seconds before starting to allow you to prepare the desktop.

## Important details

- The current implementation uses OCR to detect text matching `notepad`.
- It writes files using Notepad save dialogs and handles overwrite confirmation popups.
- Output files are saved in the current working directory as:
  - `post_1.txt`
  - `post_2.txt`
  - ...
  - `post_10.txt`

## Notes from code review

- The final `save_post` function is the active implementation; earlier versions are commented out or overridden.
- `MATCH_THRESHOLD` and `MAX_RETRIES` constants are defined but not fully used in the current active logic.
- `is_save_popup_open()` is defined but not currently used by the active save flow.
- Because this is a screen-based automation script, it is sensitive to window placement and visible desktop state.

## Troubleshooting

- If Notepad is not detected, make sure Notepad is visible and not hidden behind another window.
- If save dialogs behave differently on your system, you may need to adapt the popup handling logic in `main.py`.
- Run the script when the desktop is idle and avoid moving the mouse during execution.

## License

This repository has no license specified.
