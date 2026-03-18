#!/usr/bin/env bash
set -euo pipefail

# Utilities for driving WeChat on macOS via AppleScript (System Events).
# Note: requires Accessibility permissions.

activate_wechat() {
  osascript -e 'tell application "WeChat" to activate'
}

key_code() {
  local code="$1"
  osascript -e "tell application \"System Events\" to key code ${code}"
}

cmd_f() {
  osascript -e 'tell application "System Events" to keystroke "f" using command down'
}

esc() { key_code 53; }
enter() { key_code 36; }
arrow_down() { key_code 125; }
arrow_up() { key_code 126; }
page_down() { key_code 121; }
space() { osascript -e 'tell application "System Events" to keystroke space'; }

screenshot() {
  local out="$1"
  screencapture -x "$out"
}

# Example:
#   source wechat_keystrokes.sh
#   activate_wechat
#   cmd_f
#   arrow_down
#   screenshot /tmp/a.png
