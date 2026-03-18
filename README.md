# 🦞 OpenClaw-Desktop-Skillset

> **OpenClaw 桌面技能集：为 AI 从业者打造的全天候“数字分身”。**

[![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue.svg)](VERSION)
[![Powered by](https://img.shields.io/badge/powered%20by-OpenClaw-orange.svg)](https://github.com/OpenClaw/openclaw)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](#-相关配置-configuration)
[![Live Demo](https://img.shields.io/badge/demo-Live%20Showcase-E63946.svg)](https://dengc2023.github.io/OpenClaw-Desktop-Skillset/docs/index.html)

**中文版** | [English Version](README_EN.md)

---

## 🌐 在线展示页 (Live Showcase)

> **"Experience the precision of OpenClaw-Desktop-Skillset in our interactive showcase."**

我们为本项目打造了一个专属的展示网页，包含全技能的演示视频和交互式介绍：
👉 **[点击访问在线演示页](https://dengc2023.github.io/OpenClaw-Desktop-Skillset/docs/index.html)**

![Website Preview](imgs/web_preview.png)

---

## 🧐 为什么需要这个项目？ (The "Why")

作为 AI 从业者，我们每天面临着**海量的前沿信息**和**繁杂的碎片化任务**：
- **信息过载**: 微信公众号是我们获取行业动态、论文解读、技术干货的核心渠道。但手动点开、翻阅、整理非常耗时，且往往在忙碌中错过重要内容。
- **多端断流**: 我们经常遇到“手机不在身边”或“人在身边，想发电脑里的某个大文件/图片给朋友”的窘境。

### 🔑 核心突破：攻克 "API 荒漠" (Breaking the API Barrier)

传统的自动化方案往往依赖于官方 API，但对于微信等高度封闭的桌面端应用，**官方并未提供任何用于读取、搜索或社交操作的 API**。这使得传统的爬虫或集成方案彻底失效。

**OpenClaw-Desktop-Skillset** 选择了最困难但最彻底的路径：
- **视觉驱动 (Vision-Driven)**: 像人类操作员一样，通过“看”（OCR/图像匹配）和“动”（模拟点击/按键）来驱动 UI。
- **零 API 依赖**: 无论应用是否开放接口，只要屏幕上有 UI，OpenClaw 就能操作。
- **真实环境模拟**: 这种方式最贴近用户真实操作，能够绕过接口限制，实现真正的“全桌面自动化”。

---

## 🚀 核心技能库 (Core Skillset)
### 1. 懒人必备：WeChat OA Reader (公众号自动阅读与整理)
- **目标**: 解决“想看却没时间看，收藏了就等于看了”的懒人痛点。
- **能力**: 自动搜索公众号 -> 进入历史消息 -> OCR 动态匹配标题 -> 模拟滚动阅读 -> 生成结构化知识总结。

#### 🧩 长链路推理全流程展示 (Visual Workflow)

| Step 1: 搜索进入主页 | | Step 2: 浏览历史消息 | | Step 3: 滚动阅读文章 |
| :---: | :---: | :---: | :---: | :---: |
| <img src="imgs/search-and-click.gif" width="250"> | <font size="10">➔</font> | <img src="imgs/enter-and-scroll.gif" width="250"> | <font size="10">➔</font> | <img src="imgs/read-first-article.gif" width="250"> |
| *搜索公众号并激活主界面* | | *OCR 动态匹配历史消息* | | *模拟人类习惯进行滚动阅读* |

- **长链路推理意义 (Long-Chain Reasoning)**: 

    - 它要求智能体在复杂的 UI 环境中跨越多个层级（搜索页、主页、列表页、正文页）保持任务上下文。

    - 智能体必须根据每一帧的视觉反馈（如：是否搜索到目标、是否加载完列表、是否到达文末）进行实时决策，体现了 OpenClaw 处理高复杂、多步骤任务流的卓越上限。
- **价值**: 让 OpenClaw 成为你的全天候“数字阅读秘书”，彻底解放双手。

### 2. 懒人社交：社交与协作 (Developing...)
- **自动朋友圈**: 自动抓取前沿资讯并分享，让你在不经意间保持技术敏感度。
- **懒人文件传输**: 远程驱动 OpenClaw 发送电脑内的文件或图片，解决“人在外面，文件在电脑”的断点。

---

## 🎬 演示视频 (Demos)

> **"See it in action: Automation with Human-like Precision."**

- [WeChat OA Reader Demo](examples/demos/wechat-oa-reader-demo.mp4) (展示了如何全屏搜索、精确定位并滚动阅读)

---

## 🛠️ 相关配置 (Configuration)

> [!IMPORTANT]
> **当前版本优先支持 macOS (Intel/Apple Silicon)**。核心驱动依赖以下组件：

### 1. 基础驱动 (macOS Native)
- **UI 操作**: [cliclick](https://github.com/BlueM/cliclick) (用于 macOS 坐标模拟点击)。
  ```bash
  brew install cliclick
  ```
- **系统交互**: AppleScript (用于按键模拟和剪贴板操作，内置于 macOS)。
- **窗口管理**: 使用 Python `Quartz` 框架实现微信窗口的精准定位与全屏控制。

### 2. Python 环境
- **Conda 环境**: 建议使用 `base` 或专门的 OpenClaw 环境。
- **核心依赖**: 详见 `requirements.txt`。

### 3. 屏幕与缩放 (Retina 校准)
- **核心逻辑**: 针对 macOS Retina 屏幕（2x 缩放），截图获取的像素坐标需进行 **`/2`** 处理后方才传给 `cliclick` 使用。本项目内置脚本已自动处理此逻辑。
- **界面设置**: 建议微信客户端设置为“全屏模式”以保证视觉锚点的稳定性。

---

## 🤝 贡献与比赛支持

如果你也深受信息过载之苦，欢迎加入我们，为 OpenClaw 开发更多实用的桌面技能。

**"Let OpenClaw handle the reading, while you focus on the leading."**
