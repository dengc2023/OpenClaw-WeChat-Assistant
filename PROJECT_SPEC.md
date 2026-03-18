# 🦞 OpenClaw-Desktop-Skillset 项目说明书

> **为 AI 从业者打造的桌面端技能集：基于视觉驱动的封闭桌面应用自动化探索（微信）。**

---

## 🔗 项目资源 (Project Resources)

- **GitHub 仓库**: [https://github.com/dengc2023/OpenClaw-Desktop-Skillset](https://github.com/dengc2023/OpenClaw-Desktop-Skillset)
- **在线演示页 (GitHub Pages)**: [https://dengc2023.github.io/OpenClaw-Desktop-Skillset/docs/index.html](https://dengc2023.github.io/OpenClaw-Desktop-Skillset/docs/index.html)

---

## 1. 项目背景与需求 (Background & Requirements)

### 1.1 核心痛点
作为 AI 从业者，我们每天需要从海量微信公众号中获取前沿信息（论文解读、技术干货）。然而，手动点开、翻阅、整理非常耗时。同时，在远程办公或差旅场景下，由于微信桌面端的封闭性，跨设备的文件传输（尤其是发送电脑内的大文件/图片）依然存在操作断点。

### 1.2 项目定位
**OpenClaw-Desktop-Skillset** 是基于 **OpenClaw** 视觉-语言-动作 (VLA) 架构开发的一套桌面端技能集。我们通过**视觉驱动**（Vision-Driven）的路径，尝试解决微信等无开放 API 应用的自动化操作问题，为用户提供一套可远程指令驱动的“数字助手”。

---

## 2. 技术实现方案 (Technical Implementation)

### 2.1 视觉驱动路径 (Vision-Driven Approach)
由于微信桌面端不提供开放 API，本项目采用模拟人类操作的逻辑：
- **感知 (Perception)**: 利用 OCR 与模板匹配识别 UI 元素。针对 macOS Retina 屏幕的 2x 缩放进行了坐标校准。
- **决策 (Decision)**: 实现了基础的“视觉决策”逻辑，能从截图的搜索结果中根据文本特征甄别目标行。
- **动作 (Action)**: 通过 `cliclick` 和 AppleScript 模拟点击、按键及剪贴板操作，确保在无接口环境下的操作可行性。

### 2.2 长链路操作流 (Long-Chain Operations)
项目中的核心技能（如 OA Reader）实现了跨越多个 UI 层级的长链路操作：从搜索、导航、列表定位到模拟滚动阅读。智能体根据实时视觉反馈（如：是否到达文末、是否搜索成功）执行对应的逻辑分支。

---

## 3. 核心技能库 (Core Skillset - "Lazy Series")

### 3.1 WeChat OA Reader (公众号自动阅读与整理)
- **功能**: 自动搜索公众号，进入历史消息，匹配目标标题，模拟滚动阅读并输出摘要。
- **价值**: 辅助用户快速筛选和沉淀公众号干货信息。

### 3.2 WeChat Moments Post (自动发朋友圈)
- **功能**: 自动识别相机图标，调用 `Cmd+Shift+G` 进行跨应用文件选择，自动填写配文并发表。
- **价值**: 方便用户直接从电脑端分享高清素材。

### 3.3 WeChat Search-Pick-Send (精准搜索与发送)
- **功能**: 智能搜索联系人/群聊，支持自动压缩文件夹并发送。
- **价值**: 解决特定联系人查找繁琐及远程文件传输的断点问题。

---

## 4. 系统架构 (System Architecture)

```text
[ 用户指令 ] -> [ OpenClaw 决策层 ]
                       |
                       v
[ 技能库 (Skills) ] <-> [ 视觉层 (OCR/匹配) ]
                       |
                       v
[ 驱动层 (cliclick/AppleScript) ] -> [ 微信客户端 UI ]
```

---

## 5. 项目工程化说明 (Engineering)

- **环境适配**: 优先支持 macOS (Intel/Silicon)，适配了高分屏 Retina 的缩放逻辑。
- **文档规范**: 提供中英文双语 `README`，并建立了直观的视频演示网页。
- **配置管理**: 通过 `requirements.txt` 规范了视觉与系统自动化所需的 Python 依赖。

---

## 6. 后续规划 (Roadmap)

1. **技能扩充**: 探索更多办公场景下的视觉驱动技能（如邮件自动化、文档整理）。
2. **鲁棒性提升**: 进一步优化视觉算法，提升在不同分辨率和主题模式下的适配精度。
3. **远程联动**: 配合 OpenClaw 核心，实现更灵活的移动端指令下发。

---

**"Let OpenClaw handle the reading, while you focus on the leading."**
