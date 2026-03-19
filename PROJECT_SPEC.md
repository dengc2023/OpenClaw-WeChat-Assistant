# 🦞 OpenClaw-WeChat-Assistant 项目说明书

> **为 AI 从业者打造的微信自动化技能集：无 API 环境下的纯视觉驱动探索。**

---

## 🔗 项目资源 (Project Resources)

- **GitHub 仓库**: [https://github.com/dengc2023/OpenClaw-WeChat-Assistant](https://github.com/dengc2023/OpenClaw-WeChat-Assistant)
- **在线演示页 (GitHub Pages)**: [https://dengc2023.github.io/OpenClaw-WeChat-Assistant/docs/index.html](https://dengc2023.github.io/OpenClaw-WeChat-Assistant/docs/index.html)

---

## 1. 项目背景与定位 (Background & Vision)

作为 AI 从业者，我们每天面临着**海量的前沿信息**和**跨设备的碎片化任务**。由于国民级应用微信在桌面端**高度封闭，没有任何官方开放 API**，传统的接口调用或爬虫方案彻底失效。

为了解决这一痛点，**OpenClaw-WeChat-Assistant** 选择了一条最困难但也最彻底的路径：**视觉驱动 (Vision-Driven)**。基于 OpenClaw 的 VLA（视觉-语言-动作）架构，本项目像一个坐在电脑前的真实人类一样：
- **“看” (Perception)**: 全屏截图，通过 OCR 和 OpenCV 模板匹配识别 UI 元素。
- **“想” (Decision)**: 基于长尾特征（如群聊 vs 个人、候选行列表）进行启发式的多模态决策。
- **“动” (Action)**: 直接操控系统底层 (`cliclick` 与 AppleScript) 发起精准的鼠键事件。

---

## 2. 核心技能深度解析 (Core Skillsets in Detail)

技能库统一按照 **“看清当前屏幕 → 制定局部决策 → 执行动作分支”** 的状态机 (FSM) 模式运行。以下是各个核心技能的底层实现流与关键技术点。

### 2.1 懒人阅读: WeChat OA Reader (公众号自动阅读与整理)
这是一个极具代表性的长链路长上下文推理任务，智能体需要跨越多个层级界面（微信主页面 → 公众号主页 → 历史文章列表 → 正文），保持环境追踪。

- **工作流 (Workflow)**:
  1. **搜索进入**: 剪贴板输入公众号名称 → 锚点区域 OCR (`ocr_roi_search.py`) 定位公众号并点击。
  2. **获取列表**: 找屏幕右上角的“人形轮廓”图标 (`find_icon.py` 模板匹配) → 进入主页。
  3. **获取标题**: 点击安全区聚焦 → 使用 `↓` (Key 125) 动态滚动获取最近 10 条文章。
  4. **进入文章**: 倒序回滚 → 动态 OCR 查词 (`ocr_click_box.py`) 算出精确坐标 → 点击进入。
  5. **循环阅读**: 点击正文聚焦 → `Esc` 关掉误触图片 → 循环滚动截图至"THE END"或底部 → 输出结构化总结。

- **核心技术挑战已攻克**:
  - **动态模板降维打击**: 默认图标匹配阈值在不同暗黑模式下变动大，系统会自动执行阈值降级 (`0.8 -> 0.4`) 以提升鲁棒性。
  - **坐标系转换**: 引入 Retina 屏幕校准机制（截图坐标 `/2` 下发给底层点击驱动）。

### 2.2 懒人社交: WeChat Moments Post (自动发朋友圈)
突破了全屏界面的复杂弹窗交互盲区，实现了本地素材向社交媒体的一键分发。

- **工作流 (Workflow)**:
  1. **进入朋友圈**: `Cmd+4` 打开朋友圈页面。
  2. **精准触发**: 全屏截图 → 匹配极小的相机图标模板 → **(关键) 先 Move 再 Click** 以唤醒组件。
  3. **路径直达**: 在文件选择器中执行 `Cmd+Shift+G`，剪贴板下发绝对路径 `imagePath` 并键入 `Return`。
  4. **内容上屏**: `Cmd+O` 选中图片后 → 单独高亮锁定并聚焦配文区输入框 → 把剪贴板切换为 `caption` 并粘贴。
  5. **视觉识别发送**: 截取弹窗底部特征，识别绿色「发表」按钮并精确点击。

- **核心技术挑战已攻克**:
  - **焦点紊乱防治**: 严格分离文件路径与文案内容的剪贴板使用，避免旧路径残留到朋友圈配文内。

### 2.3 懒人互联: WeChat Search-Pick-Send (精准搜索与跨端发送)
不再依赖写死的坐标或硬编码，真正实现了让智能体从一堆“长得差不多”的搜索结果里挑出正确的人。

- **工作流 (Workflow)**:
  1. **唤醒与全屏**: `open -a WeChat` → 触发二次校验的 `Ctrl+Cmd+F`，提供坚实的视距锚点。
  2. **鲁棒搜索**: 剪贴板注入目标（支持好友或群聊）。
  3. **视觉多目标启发 (Visual Decision)**: 
     - 截取当前左侧边栏区域。
     - 若找特定的群，则大幅度提高 "包含目标文字的群聊" 模块的分类置信度。
     - 若找个人，遇到同名时优先匹配 "联系人" 项，而不是 "聊天记录" 的结果。
     - 从返回图计算目标在结果集中的 `rowIndex`。
  4. **键盘导航穿梭**: 利用 `↓` 移动对应次数，敲击 `Enter` 进入聊天区域。
  5. **双重发送机制**:
     - *文本模式*: `Esc` 退出搜索焦点 → `Tab` 进入聊天框 → `Cmd+V` 粘贴 → `Enter`。
     - *文件模式*: 对于文件夹输入，先静默触发 `/usr/bin/ditto` 打包为 `.zip` → 调用 Finder `open -R` 高亮并 `Cmd+C` 提取系统文件句柄 → 回到微信粘帖发送。

---

## 3. 核心驱动层与避坑指南 (Drivers & Best Practices)

### 3.1 核心组件池 (Components)
- **视觉驱动 (Python)**: OpenCV (`cv2.matchTemplate`), numpy, EasyOCR, Pillow。
- **动作执行 (macOS Native)**: 
  - [cliclick](https://github.com/BlueM/cliclick) 用于终端化的精准鼠标控制。
  - AppleScript & Quartz 用于生成无干扰的底层键鼠事件、剪贴板读写与应用前置置顶。

### 3.2 实战避坑指南 (The "Hard Rules")
为了在无 API 且复杂的桌面端实现工业级的稳定性，项目提炼了以下血泪经验：

1. **绝对不要用 KeyStroke 输入中文**: 
   由 `osascript` 触发的中文击键会严重污染当前系统的输入法（如 macOS 拼音状态下会打出 `Ècïèâõ`）。
   **正确解法**: 永远将中文载入剪贴板 (`osascript -e 'set the clipboard to "中文"'`) 并使用 `Cmd+V` 释放。
2. **所有点击坐标必由工具产出**:
   人类肉眼的像素估算偏差极大，所有 `c:X,Y` 必须来源于 `find_icon.py` 或 `ocr_click_box.py` 的绝对输出（再经过 Retina 的 `/2` 换算）。
3. **安全焦点转移**:
   很多操作失效的根源在于焦点遗留在错误的面板（如左侧搜索栏）。利用 `Enter` 进入后，跟一个 `Esc` 或者 `Tab` 来退回默认安全区是必须的防御动作。 
4. **延迟保护 (Delay Margin)**:
   不同性能的机器渲染 UI 速度不一，任何引发弹窗 (`Cmd+Shift+G`) 或发包的操作前后，必须夹杂 `0.2s - 0.8s` 的安全缓冲。

---

## 4. 后续规划 (Roadmap)

1. **环境泛化提升**: 加入基于 YOLO 或 GroundingDINO 的零样本跨平台 (Windows/Linux) UI组件识别引擎，摆脱分辨率依赖。
2. **多模态长文本输入能力**: 结合语音转文字大模型，直接在桌面进行语音派单给 OpenClaw 发布复合指令。

---

**"Let OpenClaw handle the reading, while you focus on the leading."**
