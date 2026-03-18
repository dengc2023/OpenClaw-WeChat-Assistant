#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Post a WeChat Moments (朋友圈) on macOS using a verified, repeatable flow.

Verified flow (do not deviate unless updating the skill):
1) Open WeChat
2) Fullscreen (Ctrl+Cmd+F)
3) Open Moments (Cmd+4)
4) Fullscreen screenshot -> template match the small camera icon -> ALWAYS move cursor then click
5) STRICT: Cmd+Shift+G -> paste absolute image path -> press Return ONCE (jump)
6) Cmd+O open
7) Paste caption
8) Optional: fullscreen screenshot -> template match the green publish button -> ALWAYS move cursor then click
9) Wait (do NOT auto-send by default unless --send)

Hard rule: any click must be preceded by moving the mouse to that location.

Usage:
  python wechat_moments_post.py --image "/abs/path/to.jpg" --caption "text" \
    --template "../references/camera_strip_template.png"

Requires:
  - cliclick
  - /usr/sbin/screencapture
  - opencv-python + numpy
"""

import argparse
import os
import time
import subprocess

import cv2


def run(cmd):
    subprocess.run(cmd, check=True)


def cmd_type(ch: str, pause=0.07):
    run(["cliclick", "kd:cmd"])
    time.sleep(pause)
    run(["cliclick", f"t:{ch}"])
    time.sleep(pause)
    run(["cliclick", "ku:cmd"])


def cmd_shift_type(ch: str, pause=0.07):
    run(["cliclick", "kd:cmd,shift"])
    time.sleep(pause)
    run(["cliclick", f"t:{ch}"])
    time.sleep(pause)
    run(["cliclick", "ku:cmd,shift"])


def cmd_ctrl_type(ch: str, pause=0.07):
    run(["cliclick", "kd:cmd,ctrl"])
    time.sleep(pause)
    run(["cliclick", f"t:{ch}"])
    time.sleep(pause)
    run(["cliclick", "ku:cmd,ctrl"])


def key_return(pause=0.07):
    run(["osascript", "-e", 'tell application "System Events" to key code 36'])
    time.sleep(pause)


def key_escape(pause=0.07):
    run(["cliclick", "kp:esc"])
    time.sleep(pause)


def cmd_a(pause=0.07):
    run(["cliclick", "kd:cmd"])
    time.sleep(pause)
    run(["cliclick", "t:a"])
    time.sleep(pause)
    run(["cliclick", "ku:cmd"])


def key_delete(pause=0.07):
    run(["osascript", "-e", 'tell application "System Events" to key code 51'])
    time.sleep(pause)


def screenshot(path: str):
    run(["/usr/sbin/screencapture", "-x", path])


def move_then_click(x: float, y: float, pause=0.2):
    xi, yi = int(round(x)), int(round(y))
    # hard rule: move first
    run(["cliclick", f"m:{xi},{yi}"])
    time.sleep(pause)
    run(["cliclick", f"c:{xi},{yi}"])


def img_to_click(x_img: float, y_img: float):
    """Screenshot pixel coords -> cliclick coords (points).

    Verified on this machine: Retina scale=2 and NO y-flip.
    """
    return x_img / 2.0, y_img / 2.0


def match_camera_center(screen_path: str, strip_template_path: str):
    hay = cv2.imread(screen_path)
    if hay is None:
        raise RuntimeError(f"Failed to read screenshot: {screen_path}")

    tmpl = cv2.imread(strip_template_path)
    if tmpl is None:
        raise RuntimeError(f"Failed to read template: {strip_template_path}")

    # template is a strip of 3 icons; use rightmost third (camera)
    h, w = tmpl.shape[:2]
    cam = tmpl[:, int(w * 2 / 3): w]

    hay_g = cv2.cvtColor(hay, cv2.COLOR_BGR2GRAY)
    cam_g = cv2.cvtColor(cam, cv2.COLOR_BGR2GRAY)

    hay_e = cv2.Canny(hay_g, 50, 150)
    cam_e = cv2.Canny(cam_g, 50, 150)

    res = cv2.matchTemplate(hay_e, cam_e, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    th, tw = cam_e.shape
    x, y = max_loc
    cx = x + tw / 2.0
    cy = y + th / 2.0
    return cx, cy, float(max_val)




def match_send_button_center(screen_path: str):
    hay = cv2.imread(screen_path)
    if hay is None:
        raise RuntimeError(f"Failed to read screenshot: {screen_path}")

    hsv = cv2.cvtColor(hay, cv2.COLOR_BGR2HSV)
    lower = (35, 60, 60)
    upper = (90, 255, 255)
    mask = cv2.inRange(hsv, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    best = None
    best_area = 0
    H, W = mask.shape[:2]
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 1500:
            continue
        if w < 80 or h < 28:
            continue
        if y < H * 0.55:
            continue
        if x < W * 0.45 or x > W * 0.8:
            continue
        ratio = w / max(h, 1)
        if ratio < 1.8 or ratio > 5.5:
            continue
        if area > best_area:
            best_area = area
            best = (x, y, w, h)

    if not best:
        raise RuntimeError('Failed to locate green publish button')

    x, y, w, h = best
    cx = x + w / 2.0
    cy = y + h / 2.0
    return cx, cy, float(best_area), (x, y, w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="Absolute path to image file")
    ap.add_argument("--caption", required=True, help="Moments caption")
    ap.add_argument("--template", required=True, help="Path to camera strip template")
    ap.add_argument("--minScore", type=float, default=0.75)
    ap.add_argument("--noFullscreen", action="store_true")
    ap.add_argument("--waitSeconds", type=int, default=20)
    ap.add_argument("--send", action="store_true", help="After pasting caption, locate green publish button and click send")
    args = ap.parse_args()

    image_path = args.image.strip()
    if not os.path.isabs(image_path):
        raise SystemExit("--image must be an absolute path")
    if not os.path.exists(image_path):
        raise SystemExit(f"Image not found: {image_path}")
    if not os.path.exists(args.template):
        raise SystemExit(f"Template not found: {args.template}")

    # 1) open WeChat
    run(["open", "-a", "WeChat"])
    time.sleep(0.8)

    # 2) fullscreen
    if not args.noFullscreen:
        cmd_ctrl_type("f")
        time.sleep(0.8)

    # 3) Moments
    cmd_type("4")
    time.sleep(1.2)

    # 4) locate and click camera
    shot = os.path.join(os.getcwd(), "moments_step4.png")
    screenshot(shot)
    x_img, y_img, score = match_camera_center(shot, args.template)
    print(f"[match] img=({x_img:.1f},{y_img:.1f}) score={score:.3f}")
    if score < args.minScore:
        raise SystemExit("Camera match score too low; ensure Moments page is visible.")

    x_cg, y_cg = img_to_click(x_img, y_img)
    print(f"[click] cg=({x_cg:.1f},{y_cg:.1f})")
    move_then_click(x_cg, y_cg)
    time.sleep(0.8)

    # 5) Direct picker flow: Cmd+Shift+G -> paste absolute path -> Return -> Cmd+O
    cmd_shift_type("g")
    time.sleep(0.8)
    cmd_a()
    time.sleep(0.1)
    key_delete()
    time.sleep(0.1)
    run(["osascript", "-e", f"set the clipboard to \"{image_path}\""])
    time.sleep(0.2)
    cmd_type("v")
    time.sleep(0.45)
    key_return(pause=0.12)
    time.sleep(0.8)

    # 6) Open selected path/file
    cmd_type("o")
    time.sleep(1.0)

    # 7) focus text area, then paste caption exactly once
    time.sleep(0.5)
    move_then_click(520, 260)
    time.sleep(0.2)
    run(["osascript", "-e", f"set the clipboard to \"{args.caption}\""])
    time.sleep(0.15)
    cmd_type("v")
    time.sleep(0.3)

    if args.send:
        time.sleep(0.6)
        send_shot = os.path.join(os.getcwd(), "moments_send.png")
        screenshot(send_shot)
        sx_img, sy_img, send_area, send_box = match_send_button_center(send_shot)
        sx_cg, sy_cg = img_to_click(sx_img, sy_img)
        print(f"[send-match] img=({sx_img:.1f},{sy_img:.1f}) area={send_area:.0f} box={send_box}")
        print(f"[send-click] cg=({sx_cg:.1f},{sy_cg:.1f})")
        move_then_click(sx_cg, sy_cg)
        print("[sent] clicked green publish button")
        time.sleep(1.0)
    else:
        print(f"[done] image+caption filled. Not sending. Waiting {args.waitSeconds}s...")
        time.sleep(args.waitSeconds)


if __name__ == "__main__":
    main()
