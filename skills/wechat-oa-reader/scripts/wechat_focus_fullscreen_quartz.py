#!/usr/bin/env python3
"""Focus WeChat "main" window and ensure fullscreen using Quartz window enumeration.

Why
- System Events / Accessibility can report AXFullScreen for *front window*, but enumerating windows
  of WeChat via AX API is unreliable on some WeChat builds (invalid index, -10006 errors).
- Quartz CGWindowListCopyWindowInfo can enumerate all windows owned by WeChat at the OS level.

What it does
1) Enumerate windows where kCGWindowOwnerName == 'WeChat'
2) Pick a likely "main" window by heuristics (exclude web/article windows; prefer larger, on-screen)
3) Activate WeChat and bring that window to front (best-effort)
4) Read AXFullScreen of the *front* window and toggle fullscreen if requested
5) Optional screenshot for verification

Requirements
- pyobjc-framework-Quartz, pyobjc-framework-Cocoa (install into conda base):
  pip install pyobjc-framework-Quartz pyobjc-framework-Cocoa
- Accessibility permissions for System Events keystrokes / AXFullScreen read

Note
- Quartz can enumerate windows, but cannot directly 'raise' arbitrary windows without Accessibility.
  We therefore use a best-effort approach:
  - activate WeChat
  - click the target window's center point (cliclick) to focus it
  Then use AXFullScreen toggle on the focused window.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from typing import Any

import Quartz


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def osascript(script: str) -> str:
    cp = run(["osascript", "-e", script], check=True)
    return (cp.stdout or "").strip()


@dataclass
class QWin:
    wid: int
    owner: str
    name: str
    x: float
    y: float
    w: float
    h: float
    layer: int
    onscreen: int
    alpha: float

    @property
    def area(self) -> float:
        return max(0.0, self.w) * max(0.0, self.h)

    def center(self) -> tuple[int, int]:
        return (int(self.x + self.w / 2), int(self.y + self.h / 2))


def list_wechat_windows() -> list[QWin]:
    # NOTE: WeChat windows may report kCGWindowIsOnscreen=None; using OnScreenOnly can return 0.
    # Use OptionAll and filter by owner name instead.
    opts = Quartz.kCGWindowListOptionAll | Quartz.kCGWindowListExcludeDesktopElements
    info_list = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID) or []
    wins: list[QWin] = []
    for d in info_list:
        owner = d.get("kCGWindowOwnerName", "")
        if owner != "WeChat":
            continue
        bounds = d.get("kCGWindowBounds") or {}
        wins.append(
            QWin(
                wid=int(d.get("kCGWindowNumber")),
                owner=owner,
                name=str(d.get("kCGWindowName") or ""),
                x=float(bounds.get("X", 0.0)),
                y=float(bounds.get("Y", 0.0)),
                w=float(bounds.get("Width", 0.0)),
                h=float(bounds.get("Height", 0.0)),
                layer=int(d.get("kCGWindowLayer", 0)),
                onscreen=int(d.get("kCGWindowIsOnscreen", 0)),
                alpha=float(d.get("kCGWindowAlpha", 1.0)),
            )
        )
    return wins


def score_main(w: QWin) -> float:
    t = (w.name or "").lower()
    score = 0.0

    # prefer big visible windows
    score += min(w.area / 1_000_000.0, 10.0)  # cap contribution

    # penalize tiny / tool windows
    if w.area < 200_000:
        score -= 10

    # penalize transparency / odd layers
    if w.alpha < 0.9:
        score -= 5
    if w.layer != 0:
        score -= 2

    # penalize obvious webview/article windows
    bad = ["weixin", "official", "platform", "http", "minds in ai"]
    if any(k in t for k in bad):
        score -= 15

    # empty name often means main app window
    if w.name.strip() == "":
        score += 5

    return score


def pick_main(wins: list[QWin]) -> QWin | None:
    if not wins:
        return None
    return max(wins, key=score_main)


def activate_wechat():
    osascript('tell application "WeChat" to activate')


def read_ax_fullscreen_front() -> str:
    return osascript(
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
    osascript('tell application "System Events" to keystroke "f" using {command down, control down}')


def screenshot(path: str):
    run(["screencapture", "-x", path], check=True)


def click_point(x: int, y: int):
    # rely on cliclick if present
    cp = run(["bash", "-lc", "command -v cliclick >/dev/null 2>&1 && echo yes || echo no"], check=True)
    if cp.stdout.strip() != "yes":
        raise RuntimeError("cliclick not installed")
    run(["cliclick", f"c:{x},{y}"], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensure-fullscreen", action="store_true")
    ap.add_argument("--screenshot", default=None, help="Screenshot after focusing/toggling")
    ap.add_argument("--click-scale", type=float, default=1.0, help="Scale Quartz pixel coords to cliclick coords (Retina often needs 0.5)")
    ap.add_argument("--dump-screens", default=None, help="If set, screenshot candidate windows into this directory (debug)")
    ap.add_argument("--dump-limit", type=int, default=8, help="How many top-scored windows to dump")
    args = ap.parse_args()

    wins = list_wechat_windows()
    ranked = sorted(wins, key=score_main, reverse=True)

    activate_wechat()

    dumped = []
    if args.dump_screens:
        import os
        os.makedirs(args.dump_screens, exist_ok=True)
        # Dump top-N windows by score. We focus each window by clicking its center,
        # then take a screenshot. This is language-agnostic and robust for manual selection.
        for k, w in enumerate(ranked[: max(1, args.dump_limit)], start=1):
            cx, cy = w.center()
            cx = int(cx * args.click_scale)
            cy = int(cy * args.click_scale)
            try:
                click_point(cx, cy)
            except Exception as e:
                dumped.append({"id": w.wid, "name": w.name, "error": str(e)})
                continue
            # small delay for focus
            import time
            time.sleep(0.6)
            out_path = os.path.join(args.dump_screens, f"wx_win_{k:02d}_id{w.wid}_score{score_main(w):.2f}.png")
            screenshot(out_path)
            dumped.append({"id": w.wid, "name": w.name, "score": score_main(w), "center": [cx, cy], "screenshot": out_path})

    picked = pick_main(wins)

    focused = None
    if picked:
        cx, cy = picked.center()
        cx = int(cx * args.click_scale)
        cy = int(cy * args.click_scale)
        click_point(cx, cy)
        focused = {"window_id": picked.wid, "name": picked.name, "center": [cx, cy], "score": score_main(picked)}

    fs = read_ax_fullscreen_front()
    toggled = False
    if args.ensure_fullscreen and fs.strip() == "false":
        toggle_fullscreen()
        toggled = True
        fs = read_ax_fullscreen_front()

    if args.screenshot:
        screenshot(args.screenshot)

    out: dict[str, Any] = {
        "picked": None if not picked else {
            "id": picked.wid,
            "name": picked.name,
            "bounds": [picked.x, picked.y, picked.w, picked.h],
            "score": score_main(picked),
        },
        "focused": focused,
        "fullscreen": fs.strip(),
        "toggled": toggled,
        "window_count": len(wins),
        "dumped": dumped,
        "windows": [
            {
                "id": w.wid,
                "name": w.name,
                "bounds": [w.x, w.y, w.w, w.h],
                "layer": w.layer,
                "alpha": w.alpha,
                "score": score_main(w),
            }
            for w in ranked
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
