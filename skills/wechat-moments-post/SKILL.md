---
name: wechat-moments-post

description: >
  Post a WeChat Moments (朋友圈) on macOS. Workflow: open WeChat, fullscreen, open Moments
  (Cmd+4), locate the small camera icon via full-screen screenshot + template matching, click
  it (ALWAYS move cursor first), open file picker and use Cmd+Shift+G to jump to an absolute
  file path, open the selected image, focus the caption text area, paste the caption once,
  and optionally locate the green publish button via screenshot analysis and click it to send.
  Use when the user asks to发朋友圈 / publish to WeChat Moments, especially when the task
  requires direct sending rather than stopping before publish.
---

# WeChat Moments Post (macOS)

用于在 macOS 上稳定发布微信朋友圈。这个 skill 处理的是**朋友圈发布弹窗**，不是普通聊天发消息。

## Preconditions

- WeChat 已安装并登录
- OpenClaw / Terminal 具备辅助功能（Accessibility）权限
- 已安装 `cliclick`
- Python 环境具备 `opencv-python` 和 `numpy`

## Hard rule

- 任何点击动作都必须先移动鼠标，再点击
- 用 `move -> click`，不要直接裸点

## Inputs

- `imagePath`：本地图片绝对路径，首尾不要带空格
- `caption`：朋友圈配文
- `--send`：需要直接点击绿色“发表”按钮时传入；默认不自动发送

## Verified flow

严格按这个流程执行：

1. `open -a WeChat`
2. `Ctrl+Cmd+F` 进入全屏
3. `Cmd+4` 打开朋友圈
4. 全屏截图，用模板匹配定位右上区域的小相机图标
5. 将截图像素坐标换算为屏幕点击坐标，**先 move 再 click** 打开发布弹窗
6. 在文件选择器里执行：
   - `Cmd+Shift+G`
   - 等待约 `0.8s`
   - 对“前往路径”输入框执行 `Cmd+A` + Delete，确保旧路径被清空
   - 粘贴 `imagePath`
   - 等待约 `0.45s`
   - 用 `System Events key code 36` 发送一次 Return
7. 等待约 `0.8s` 后执行 `Cmd+O` 打开图片
8. 等待弹窗稳定后，点击配文输入区域，让焦点明确落在配文框
9. 只粘贴一次 `caption`，不要再对配文区做整块清空
10. 如果用户要求直接发送：
    - 再做一次全屏截图
    - 识别弹窗底部偏右的绿色“发表”按钮
    - 将截图像素坐标换算为屏幕点击坐标
    - **先 move 再 click** 完成发送
11. 如果用户没有明确要求发送，就停在已填好图片和配文的状态

## Why this flow matters

- 必须只清空“前往路径”输入框，不能粗暴清空配文区
- 配文区要在图片打开后单独聚焦，再只粘贴一次配文
- 否则容易出现：
  - 文件路径残留进配文
  - 旧配文和新配文叠加
  - 焦点仍停留在错误输入框里
- 绿色“发表”按钮的实际位置是**弹窗底部偏右**，不要假设它在右上角

## Script

- `scripts/wechat_moments_post.py`

脚本职责：

- 打开微信并进入朋友圈
- 截图匹配小相机
- 处理 `Cmd+Shift+G -> 路径输入 -> Return -> Cmd+O`
- 聚焦配文区并粘贴一次配文
- 传 `--send` 时截图识别绿色“发表”按钮并点击发送

## References

- `references/camera_strip_template.png`：用于裁切并匹配小相机图标

## Command example

```bash
python3 scripts/wechat_moments_post.py \
  --image "/absolute/path/to/image.jpg" \
  --caption "Openclaw（小龙虾）测试" \
  --template ../references/camera_strip_template.png \
  --send
```

不想自动发送时，去掉 `--send`。

## Troubleshooting

- 如果 `Cmd+Shift+G` 后没有正确跳转：
  - 检查 Return 是否发到了“前往路径”输入框
  - 保留 `Cmd+Shift+G` 后的等待时间，不要过快
- 如果配文异常：
  - 先怀疑焦点没有落到配文输入区
  - 不要默认对配文区做 `Cmd+A + Delete`
- 如果发送按钮识别失败：
  - 检查是否真的打开了朋友圈发布弹窗
  - 注意按钮位于弹窗底部偏右，而不是右上角
- 如果点击不生效：
  - 检查 Accessibility 权限
  - 检查是否遵守了“先 move 再 click”
