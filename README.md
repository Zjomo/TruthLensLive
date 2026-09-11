# TruthLensLive V2.0

[🇨🇳 中文](README.zh-CN.md) | [🇬🇧 English](README.en-US.md)

**Read this in other languages:** [简体中文](README.zh-CN.md)

---

一个综合的全栈应用，用于实时谣言检测和新闻验证。采用现代网络技术和人工智能驱动的分析来对抗错误信息。

A comprehensive full-stack application for real-time rumor detection and news verification. Built with modern web technologies and AI-powered analysis to combat misinformation.

![License](https://img.shields.io/github/license/Zjomo/TruthLensLive?style=flat-square)
![Language](https://img.shields.io/github/languages/top/Zjomo/TruthLensLive?style=flat-square)

---

## 📖 Language Selector | 语言选择

### 快速导航 | Quick Navigation

| 语言 | Language | 文档 | Documentation |
|------|----------|------|---|
| 🇨🇳 中文 | Chinese | [README.zh-CN.md](README.zh-CN.md) | [中文完整文档](README.zh-CN.md) |
| 🇬🇧 English | English | [README.en-US.md](README.en-US.md) | [Full English Documentation](README.en-US.md) |

---

## 🎯 Project Overview | 项目概述

**TruthLensLive** is a real-time rumor detection system that combines:
- 📡 **Real-time Data Streaming**: RSS feed aggregation with live updates
- 🤖 **AI-Powered Analysis**: Heuristic scoring for rumor detection
- 🧠 **RAG + Multimodal Fusion**: Text / image / audio / video detection with evidence-chain explanations
- 📊 **Visual Analytics**: Interactive dashboards and charts
- 🌍 **Multi-language Support**: English and Chinese interfaces
- 🐳 **Cloud-Ready**: Docker support for easy deployment

**TruthLensLive** 是一个实时谣言检测系统，结合：
- 📡 **实时数据流**：RSS 源聚合和实时更新
- 🤖 **AI 驱动分析**：用于谣言检测的启发式评分
- 🧠 **RAG + 多模态融合**：文本 / 图像 / 音频 / 视频检测，生成"证据链"式解释
- 📊 **可视化分析**：交互式仪表板和图表
- 🌍 **多语言支持**：英文和中文界面
- 🐳 **云就绪**：支持 Docker 快速部署

---

## 🎬 Demo Showcase | 系统案例演示

### 📰 RAG Real-time Fake News Detection | 基于 RAG 的实时虚假新闻检测

Input news headline and content, the system returns a credibility score, BERT detection result, AI analysis and a downloadable full log in seconds.
输入新闻标题与正文，系统秒级返回可信度评分、BERT 检测结果、AI 分析说明与完整日志下载。

![RAG 实时虚假新闻检测界面](docs/images/rag-detect-ui.png)

### 🎞️ Multimodal Video Detection | 多模态视频检测

End-to-end pipeline from "news video + text" to "classification result, text emotion and audio emotion", with light / dark themes.
从"新闻视频 + 文本"到"分类结果、文本情绪与音频情绪"的端到端流程，支持深色 / 浅色主题。

<table>
  <tr>
    <td width="50%"><img src="docs/images/multimodal-input-light.jpeg" alt="多模态检测-输入界面（浅色）"/></td>
    <td width="50%"><img src="docs/images/multimodal-video-dark.jpeg" alt="多模态检测-视频处理界面（深色）"/></td>
  </tr>
  <tr>
    <td colspan="2"><img src="docs/images/multimodal-result.jpeg" alt="多模态检测-结果与分析界面"/></td>
  </tr>
</table>

### 📹 Project Demo Video | 项目演示视频

Full system walkthrough (screen recording, ~91 MB):
完整系统演示录屏（约 91 MB，仓库内路径）：

> 🎥 [`Material/我的刀盾_TruthLensLive—基于RAG-多模态融合的虚假新闻实时检测系统_项目视频.mp4`](Material/我的刀盾_TruthLensLive—基于RAG-多模态融合的虚假新闻实时检测系统_项目视频.mp4)
>
> 💡 GitHub renders large videos poorly — for online playback, upload to GitHub Releases / Bilibili / YouTube and replace the link above.
> 提示：GitHub 对大视频渲染支持有限，建议上传至 Releases / B站 / YouTube 后替换为在线播放链接。

### 🧪 Detection Case Examples | 检测案例示例

Real-world multimodal fake-news samples used in evaluation (video + multilingual captions):
评测中使用的真实多模态虚假新闻样例（视频 + 多语言字幕）：

<table>
  <tr>
    <td width="50%"><img src="docs/images/example-video-zh.png" alt="案例：突发事件剪辑视频"/></td>
    <td width="50%"><img src="docs/images/example-video-multilingual.png" alt="案例：多语言场景剪辑视频"/></td>
  </tr>
</table>

---

## 🏗️ Model Architecture & Performance | 模型架构与性能

### FakingRecipe Multimodal Framework | 多模态融合框架

Material selection-aware + editing-aware modeling over audio, title/transcript and key frames.
面向音频、标题/转录与关键帧的"素材选取感知 + 素材编辑感知"建模。

<table>
  <tr>
    <td width="60%"><img src="docs/images/architecture-fakingrecipe.png" alt="FakingRecipe 多模态框架"/></td>
    <td width="40%"><img src="docs/images/llm-label-propagation.png" alt="LLM 标签传播集成"/></td>
  </tr>
</table>

### Benchmark Results | 基准测试结果

EQ-Former / EQFFG-Trans reach state-of-the-art F1 on both Weibo and Tweet datasets.
EQ-Former / EQFFG-Trans 在 Weibo 与 Tweet 数据集上均达到 SOTA F1。

<table>
  <tr>
    <td width="50%"><img src="docs/images/metrics-weibo-multimodal.png" alt="Weibo 多图文情感融合模型"/></td>
    <td width="50%"><img src="docs/images/metrics-tweet-multimodal.png" alt="Tweet 多图文情感融合模型"/></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/metrics-weibo-fuzzy-transformer.png" alt="Weibo 模糊图 Transformer"/></td>
    <td width="50%"><img src="docs/images/metrics-tweet-fuzzy-transformer.png" alt="Tweet 模糊图 Transformer"/></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/radar-weibo-fuzzy-transformer.png" alt="Weibo 雷达图"/></td>
    <td width="50%"><img src="docs/images/radar-tweet-fuzzy-transformer.png" alt="Tweet 雷达图"/></td>
  </tr>
</table>

---

## 🚀 Quick Start | 快速开始

### English Users | 英文用户
👉 **[Go to English README →](README.en-US.md)**

### 中文用户
👉 **[前往中文 README →](README.zh-CN.md)**

---

## 🌐 Supported Languages | 支持的语言

| Language | 语言 | Status | 状态 | Documentation |
|----------|------|--------|------|---|
| English | 英文 | ✅ Complete | 完整 | [README.en-US.md](README.en-US.md) |
| 中文简体 | Chinese Simplified | ✅ Complete | 完整 | [README.zh-CN.md](README.zh-CN.md) |
| 中文繁體 | Chinese Traditional | ⏳ Coming Soon | 即将推出 | - |
| 日本語 | Japanese | ⏳ Coming Soon | 即将推出 | - |

---

## 📁 Documentation Structure | 文档结构

```
📦 Documentation / 文档
├── 📄 README.md (This file - 当前文件)
├── 📄 README.en-US.md (English - 英文)
├── 📄 README.zh-CN.md (中文简体)
├── 📂 docs/images/ (System screenshots & benchmark charts - 系统截图与性能图表)
├── 📂 Material/ (Project video, PPT & docs - 项目视频、PPT 与文档)
├── 📂 modules/
│   ├── 📄 RagDetect/ (RAG text detection - RAG 文本检测)
│   ├── 📄 MultiFakeDetect/ (Multimodal video detection - 多模态视频检测)
│   └── 📄 ClashLinux/README.md (Linux Proxy - Linux 代理)
└── 📚 Additional Resources (其他资源)
```

---

## 🛠️ Tech Stack at a Glance | 技术栈一览

| Category | 分类 | Technologies | 技术 |
|----------|------|---|---|
| Frontend | 前端 | Vue 3, TypeScript, Vite, Element Plus | Vue 3、TypeScript、Vite、Element Plus |
| Backend | 后端 | Flask, Python, SQLite | Flask、Python、SQLite |
| Tools | 工具 | Docker, RSSHub, Tailwind CSS | Docker、RSSHub、Tailwind CSS |
| Styling | 样式 | SCSS, Tailwind CSS | SCSS、Tailwind CSS |

---

## ✨ Key Features | 主要功能

### 🎨 User Interface | 用户界面
- ✅ Real-time News Feed | 实时新闻源
- ✅ Interactive Dashboards | 交互式仪表板
- ✅ Responsive Mobile Design | 响应式移动设计
- ✅ Dark/Light Mode Support | 深色/浅色模式支持

### 🔧 Core Features | 核心功能
- ✅ AI-Powered Rumor Detection | AI 驱动的谣言检测
- ✅ Multi-Source Aggregation | 多源聚合
- ✅ Real-time Updates via SSE | 通过 SSE 实时更新
- ✅ Admin Management Panel | 管理面板

### 🌍 Localization | 本地化
- ✅ English (en-US) | 英文
- ✅ Chinese Simplified (zh-CN) | 中文简体
- ⏳ More languages coming | 更多语言即将推出

---

## 📊 Project Statistics | 项目统计

- **Repository**: [Zjomo/TruthLensLive](https://github.com/Zjomo/TruthLensLive)
- **License**: Apache License 2.0
- **Language Distribution | 语言分布**:
  - Vue: 49.5%
  - TypeScript: 21%
  - Python: 17.6%
  - HTML: 5.2%
  - Others: 6.7%

---

## 🎯 Getting Started | 入门指南

### For English Speakers | 英文用户
1. Navigate to [README.en-US.md](README.en-US.md)
2. Follow the installation steps
3. Start developing!

### 中文用户
1. 前往 [README.zh-CN.md](README.zh-CN.md)
2. 按照安装步骤操作
3. 开始开发！

---

## 🤝 Contributing | 贡献

We welcome contributions! | 欢迎贡献！

- [Contribution Guide | 贡献指南](CONTRIBUTING.md) (Coming Soon | 即将推出)
- Report bugs | 报告错误: [Issues](https://github.com/Zjomo/TruthLensLive/issues)
- Suggest features | 建议功能: [Discussions](https://github.com/Zjomo/TruthLensLive/discussions)

---

## 📞 Support & Help | 支持和帮助

- 📧 **Issues**: [GitHub Issues](https://github.com/Zjomo/TruthLensLive/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Zjomo/TruthLensLive/discussions)
- 📖 **Documentation**: See language-specific READMEs below | 查看下面的语言特定 README

---

## 📜 License | 许可证

This project is licensed under the **Apache License 2.0** | 本项目采用 **Apache License 2.0** 许可证

See [LICENSE](LICENSE) file for details | 详见 [LICENSE](LICENSE) 文件

---

## 👨‍💻 Author | 作者

**[Zjomo](https://github.com/Zjomo)** - Creator & Maintainer | 创建者和维护者

---

## 🔗 Useful Links | 有用的链接

### Documentation | 文档
- [English README | 英文 README](README.en-US.md)
- [Chinese README | 中文 README](README.zh-CN.md)
- [Backend Documentation | 后端文档](modules/Index/README.md)

### Resources | 资源
- [Vue 3 Docs](https://vuejs.org) / [Vue 3 文档](https://vuejs.org/zh/)
- [Element Plus](https://element-plus.org) / [Element Plus 中文](https://element-plus.org/zh-CN/)
- [Flask Documentation](https://flask.palletsprojects.com)
- [RSSHub Documentation](https://docs.rsshub.app/)

### Repository | 仓库
- [GitHub Repository](https://github.com/Zjomo/TruthLensLive)
- [Issues | 问题](https://github.com/Zjomo/TruthLensLive/issues)
- [Discussions | 讨论](https://github.com/Zjomo/TruthLensLive/discussions)

---

<div align="center">

### 🌟 Star Us! | 给我们一个 Star！

If you find this project helpful, please consider giving it a star ⭐

如果您觉得这个项目有帮助，请考虑给它一个 Star ⭐

[⭐ Star on GitHub](https://github.com/Zjomo/TruthLensLive)

</div>

---

**Made with ❤️ by [Zjomo](https://github.com/Zjomo)**
