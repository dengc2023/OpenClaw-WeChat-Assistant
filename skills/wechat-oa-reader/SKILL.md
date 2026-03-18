---
name: wechat-oa-reader
description: macOS 微信桌面端公众号自动化阅读与总结（搜索公众号→进入历史文章列表→OCR/模板定位→点击进入→滚动读完→结构化总结）。当用户说"帮我阅读xxx公众号…/阅读公众号xxx…/进入公众号xxx并整理最新10条/用OCR定位标题…并点进去/读完这篇公众号文章并总结"等，或需要在微信桌面端对公众号进行搜索、定位、滚动阅读、截图校验时使用。
---

# wechat-oa-reader

## 快速原则（先记住这些）
1) **点击交互**： 使用 `cliclick`，确定点击坐标有以下三种情况：
    - 头像/按钮：用 **图标模板** 匹配，如"人形轮廓/头像"（从 `assets/templates/` 找 `icon_template.png`）
    - 可滚动富文本对象（公众号主页/文章列表）：用 **OCR文字** 匹配，如公众号主页的标题、文章标题等
    - 搜索框搜索结果：用 **锚点区域OCR搜索脚本** 匹配，如"Official Accounts" + "公众号名称"
2) **点击坐标之前要标注，截图复核**：
    - 图标模板匹配：`find_icon.py <target_path> <template_path> <output_path>` 输出 bbox/center + 标注图
    - OCR文字匹配：`ocr_click_box.py <image_path> <query_text> <output_path>` 输出 bbox/center + 标注图
    - 锚点区域OCR搜索脚本：`ocr_roi_search.py <image_path> <anchor_text> <target_text> <output_path>` 输出 bbox/center + 标注图
2) **点击坐标要考虑缩放校准**：截图坐标与 `cliclick` 坐标可能存在 Retina 缩放（常见需要 `/2`）。
3) **正文滚动先聚焦**：先点正文文本区域，再用 `↓` 小步滚。
4) **执行脚本时请先激活 Conda Base 环境**：
```bash
source /Users/dengc_mac/miniconda3/etc/profile.d/conda.sh
conda activate base
```

## 资源文件
- 流程参考：`references/workflow.md`
- 图标模板匹配脚本：`scripts/find_icon.py`（命名参数：`--target_path`/`--template_path`/`--output_path`，默认模板在 assets/templates/）
- OCR文字匹配脚本：`scripts/ocr_click_box.py`（命名参数：`--image_path`/`--query_text`/`--output_path`）
- 锚点区域OCR搜索脚本：`scripts/ocr_roi_search.py`（命名参数：`--image_path`/`--anchor_text`/`--target_text`/`--output_path`）
- 微信按键工具（AppleScript 封装）：`scripts/wechat_keystrokes.sh`

## 工作流程
### 1. 进入微信主界面搜索框搜索
- 第一，截取当前屏幕，check 是否位于微信主界面并全屏，如果不是，考虑：
    - 如果是微信主界面但未全屏，使用快捷键 `Control+Cmd+F` 设置全屏
    - 如果不是微信主界面，关闭微信，重新激活，并设置全屏（如果遇到需要登录情况，执行 **OCR 文字匹配 + cliclick** 操作）
- 第二，截屏确保当前屏幕位于微信主界面并全屏后，按下 `Cmd+F` 进入搜索框，然后用 **剪贴板粘贴** 的方式输入公众号名称
   - **Never use `keystroke "中文"`.** It triggers the macOS input method and produces garbled pinyin candidates.
✅ Correct:
```applescript
osascript -e 'set the clipboard to "中文内容"'
osascript -e 'tell application "System Events" to keystroke "v" using command down'
```

❌ Wrong (garbled output):
```bash
printf '中文' | pbcopy   # Encoding mismatch in Node.js subprocess → produces Ècïèâõ
echo '中文' | pbcopy     # Same problem
```

**Root cause**: `pbcopy` via Node.js child process has encoding issues. `osascript -e 'set the clipboard to "..."'` handles Unicode natively.

### 2. 点击进入目标公众号
- 截屏，使用 **锚点区域 OCR 搜索脚本 (ocr_roi_search.py)** 直接点击目标公众号：
    - 先找锚点 "Official Accounts" (或 "公众号")
    - 在锚点下方区域搜索公众号名称
    - 获取坐标后先输出校验图（红框+绿点），需要确认无误
    - 做坐标缩放（如 `/2`），使用缩放后的坐标点击
    - **示例命令**：
      ```bash
      python3 scripts/ocr_roi_search.py --image_path current_screen.png --anchor_text "Official Accounts" --target_text "公众号名称" --output_path result.png
      ```

### 3. 进入更全文章列表（历史消息）
- 第一，截屏，检查图片，如果不是全屏，使用 `Control+Cmd+F` 设置全屏。正常情况下这时候尚未进入公众号主页，需要查看右上角是否存在"人形轮廓/头像"
- 第二，如果右上角存在"人形轮廓/头像"，执行 **图标模版匹配 + cliclick** 操作，即执行 `find_icon.py <target_path> <template_path> <output_path>` 对截图做模板匹配得到 bbox/center + 标注图，其中`template_path`为`assets/templates/icon_template.png`，`target_path`为当前截图路径，`output_path`为输出校验图路径
  - **示例命令**：
    ```bash
    python3 scripts/find_icon.py --target_path screen.png --template_path assets/templates/icon_template.png --output_path result.png --threshold 0.5
    ```
- 第三，先输出校验图（红框+绿点），需要确认无误
- 第四，做坐标缩放（如 `/2`），使用缩放后的坐标点击


### 4. 浏览最新10条历史消息（公众号文章标题）
- 第一，确保进入主页后，需要先点击可滚动对象（历史消息列表，屏幕中间），小心别点进具体某一篇文章
  - **示例命令 (点击聚焦)**：
    ```bash
    /opt/homebrew/bin/cliclick c:500,500  # 假设屏幕中间是安全区域
    ```
- 第二，先获取当前屏幕内的消息标题，如果不够10条，需要使用 `↓`（key code 125）小步持续滚动，分段截图，直到获取到10条消息标题
  - **示例命令 (滚动截图)**：
    ```bash
    osascript -e 'repeat 5 times' -e 'tell application "System Events" to key code 125' -e 'delay 0.1' -e 'end repeat'
    screencapture scroll_step_1.png
    ```
- 第三，获取到10条消息标题后，总结排列出消息标题

### 5. 选择第一条消息并进入
- 第一，因为获取消息标题时使用了滚动，所以需要回滚到第一条消息标题所在位置，使用 `↑`（key code 126）小步持续滚动，分段截图，直到获取到第一条消息标题
- 第二，确保回到第一条消息标题后，使用 **OCR文字匹配 + cliclick** 操作，即执行 `ocr_click_box.py <image_path> <query_text> <output_path>` 对截图做模板匹配得到 bbox/center + 标注图，其中`template_path`为`assets/templates/icon_template.png`，`target_path`为当前截图路径，`output_path`为输出校验图路径
  - **示例命令**：
    ```bash
    python3 scripts/ocr_click_box.py --image_path screen.png --query_text "标题关键字" --output_path result.png
    ```
- 第三，先输出校验图（红框+绿点），需要确认无误
- 第四，做坐标缩放（如 `/2`），使用缩放后的坐标点击进入

### 6. 读完整篇文章并总结
- 第一，截屏确保进入具体的文章页面后，先点击正文文本区域聚焦
  - **示例命令 (点击聚焦)**：
    ```bash
    /opt/homebrew/bin/cliclick c:600,600  # 点击正文区域
    ```
- 第二，用 `Esc` 关闭可能的图片弹层
  - **示例命令**：
    ```bash
    osascript -e 'tell application "System Events" to key code 53'
    ```
- 第三，先截取当前屏幕，如果没有看到文章结尾，就用 `↓`（key code 125）小步持续滚动，分段截图，直到看到文章结尾
  - **示例命令 (滚动)**：
    ```bash
    osascript -e 'repeat 10 times' -e 'tell application "System Events" to key code 125' -e 'delay 0.1' -e 'end repeat'
    ```
- 第四，看到 THE END/留言区/文末等标志后停止
- 第五，输出结构化总结：问题→方法→工程→结果数字→意义/局限→链接

## 坑点清单（高频）
- 方向键次数不可靠：必须截图复核高亮。
- `Space` 可能触发"打开图片/GIF"，优先用 `↓` 滚动。
- `PageDown` 在文章正文页可能不生效：先点正文聚焦再试，仍不行就用 `↓`。

## 实战经验补充（2026-03-18）

### 中文剪贴板
- ❌ `echo -n "中文" | pbcopy` → 粘贴到微信搜索框会乱码（shell UTF-8 编码问题）
- ✅ `osascript -e 'set the clipboard to "中文"'` → 正确粘贴，永远用这个方式

### 模板匹配阈值要灵活
- 默认 80% 阈值对人形图标太严格（实际只匹配到 ~53%），直接失败
- 用 `--threshold 0.4` 成功定位，且坐标完全准确
- 原因：图标在不同界面、深色/浅色背景下外观差异大，不要死守高阈值
- 建议：先用默认跑一次，失败后降到 0.4-0.5 重试

### 坐标永远用工具定位，不要靠目测估算
- 手动估算坐标 (410,80) 连点两次毫无反应
- find_icon.py 输出 (2007,391)，/2 → (1004,196)，一击命中
- **规则：所有点击坐标必须来自 find_icon.py 或 ocr_click_box.py 的输出**

### 脚本参数格式
- `find_icon.py`：命名参数 `--target_path`、`--template_path`、`--output_path`
- `ocr_click_box.py`：命名参数 `--image_path`、`--query_text`、`--output_path`

### Retina 缩放
- 截图分辨率 2940×1912，逻辑屏幕分辨率 1470×956
- 所有截图坐标 **÷2** 才能给 cliclick 使用，这一步绝不能省

### 搜索结果高亮难辨
- 微信搜索结果列表的高亮颜色与背景对比度极低，肉眼几乎看不出
- 方向键移动后必须截图验证当前高亮项，不能盲猜按 Enter
- 宁可多截一张图，不要猜错目标

### AppleScript 循环按键
- 多次按键用 `repeat N times / key code 125 / delay 0.1 / end repeat` 比多个 `-e` 拼接更可靠
- 多个 `-e` 拼接 delay 时语法容易出错（`syntax error: Expected end of line`）
