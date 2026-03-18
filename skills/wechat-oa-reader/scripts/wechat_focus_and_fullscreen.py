#!/usr/bin/env python3
"""Focus WeChat main window and optionally enter fullscreen on macOS.

Why this exists
- WeChat often has multiple windows (main chat list, official account webview, image viewer, etc.)
- Ctrl+Cmd+F is a toggle, so we must *read state first*, focus the intended window, then toggle if needed.

Approach
- Use AppleScript (osascript) via subprocess to:
  1) Activate WeChat
  2) Dismiss overlays with ESC
  3) Enumerate windows of process "WeChat" and choose a likely "main" window
  4) Raise that window
  5) Read AXFullScreen
  6) Toggle fullscreen only if not already fullscreen (optional)
  7) Return a JSON-ish summary for logging

Usage
  python wechat_focus_and_fullscreen.py --ensure-fullscreen --screenshot /tmp/wechat.png

Notes
- Requires Accessibility permissions for System Events.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass


def run_osascript(script: str) -> str:
    cp = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    out = (cp.stdout or "").strip()
    err = (cp.stderr or "").strip()
    if cp.returncode != 0:
        raise RuntimeError(f"osascript failed ({cp.returncode}): {err or out}")
    return out


@dataclass
class WinInfo:
    idx: int
    title: str
    fullscreen: str  # true/false/unknown


APPLE_ENUM = r'''
set outLines to {}
try
  tell application "System Events"
    tell process "WeChat"
      set n to count of windows
      repeat with i from 1 to n
        set w to window i
        set t to ""
        try
          set t to name of w
        end try
        set fs to "unknown"
        try
          set v to value of attribute "AXFullScreen" of w
          if v is true then
            set fs to "true"
          else
            set fs to "false"
          end if
        end try
        copy ((i as string) & "\t" & t & "\t" & fs) to end of outLines
      end repeat
    end tell
  end tell
on error errMsg number errNum
  return "ERROR\t" & errNum & "\t" & errMsg
end try
return outLines as string
'''


def parse_windows(raw: str) -> list[WinInfo]:
    if raw.startswith("ERROR\t"):
        parts = raw.split("\t", 2)
        raise RuntimeError(f"AppleScript error {parts[1]}: {parts[2] if len(parts)>2 else raw}")

    wins: list[WinInfo] = []
    for line in raw.split(", "):
        # AppleScript list string joins with ", "
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        idx = int(cols[0])
        title = cols[1]
        fs = cols[2]
        wins.append(WinInfo(idx=idx, title=title, fullscreen=fs))
    return wins


def score_main_window(w: WinInfo) -> int:
    """Heuristic scoring.

    WeChat main window often has empty/short title or a normal chat title.
    WebView windows often contain 'Weixin Official Accounts', 'Platform', article titles, etc.
    Image viewer windows often have 'Open in Window' overlay; title can differ.

    This is heuristic; always screenshot-verify afterwards.
    """
    t = (w.title or "").lower()
    score = 0

    # Prefer not-fullscreen? no, not relevant.

    # Penalize obvious webview/article windows
    bad_keywords = [
        "weixin official accounts",
        "official accounts",
        "platform",
        "http",
        "https",
        "minds in ai",
    ]
    if any(k in t for k in bad_keywords):
        score -= 50

    # Prefer empty or generic titles
    if w.title.strip() == "":
        score += 20

    # Slightly prefer shorter titles
    score += max(0, 15 - len(w.title.strip()))

    # Small bonus if title contains chinese for main tabs is hard; skip.
    return score


def pick_main_window(wins: list[WinInfo]) -> WinInfo | None:
    if not wins:
        return None
    return max(wins, key=score_main_window)


def activate_wechat():
    run_osascript('tell application "WeChat" to activate')


def press_esc(times: int = 1):
    for _ in range(times):
        run_osascript('tell application "System Events" to key code 53')


def raise_window(idx: int):
    run_osascript(
        f'''tell application "System Events"
  tell process "WeChat"
    perform action "AXRaise" of window {idx}
  end tell
end tell'''
    )


def read_fullscreen_of_front() -> str:
    return run_osascript(
        '''set isFull to "unknown"
try
  tell application "System Events"
    tell process "WeChat"
      if (count of windows) = 0 then return "NO_WINDOW"
      tell front window
        set axFull to value of attribute "AXFullScreen"
        if axFull is true then
          set isFull to "true"
        else
          set isFull to "false"
        end if
      end tell
    end tell
  end tell
on error errMsg number errNum
  return "ERROR " & errNum & ": " & errMsg
end try
return isFull'''
    )


def toggle_fullscreen():
    # Ctrl+Cmd+F
    run_osascript('tell application "System Events" to keystroke "f" using {command down, control down}')


def take_screenshot(path: str):
    subprocess.run(["screencapture", "-x", path], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensure-fullscreen", action="store_true", help="If set, enter fullscreen when not already fullscreen")
    ap.add_argument("--screenshot", default=None, help="Optional screenshot path after focusing (and toggling if requested)")
    ap.add_argument("--esc", type=int, default=1, help="How many times to press ESC before focusing")
    args = ap.parse_args()

    activate_wechat()
    if args.esc > 0:
        press_esc(args.esc)

    raw = run_osascript(APPLE_ENUM)
    wins = parse_windows(raw)
    picked = pick_main_window(wins)
    if picked is None:
        raise SystemExit("No WeChat windows found")

    raise_window(picked.idx)

    fs = read_fullscreen_of_front()
    toggled = False
    if args.ensure_fullscreen and fs.strip() == "false":
        toggle_fullscreen()
        toggled = True
        # Re-read
        fs = read_fullscreen_of_front()

    if args.screenshot:
        take_screenshot(args.screenshot)

    out = {
        "picked_window": {"idx": picked.idx, "title": picked.title, "score": score_main_window(picked)},
        "fullscreen": fs.strip(),
        "toggled": toggled,
        "window_count": len(wins),
        "windows": [{"idx": w.idx, "title": w.title, "fullscreen": w.fullscreen, "score": score_main_window(w)} for w in wins],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
