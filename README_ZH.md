# 🎵 PolyMusic: 音乐市场量化分析系统

PolyMusic 是一个独立的量化分析系统，旨在为音乐类预测市场（如 PolyMarket）提供精准的决策支持。它通过聚合 Spotify 实测数据、TikTok/YouTube 社交信号以及行业动态，捕捉市场中的定价偏差。

## 🚀 核心功能

- **Spotify 榜单扫描器**：通过 kworb.net 高速抓取全球、美国及英国的每日 Top 200 榜单。
- **量化引擎**：
  - **积分缺口分析 (Accumulation Solver)**：计算周榜中反超第一名所需的每日平均流值及其标准差。
  - **衰减控制器 (Decay Controller)**：建立了热度半衰期曲线，判断增长是“单日突发”还是“长期阶跃”。
- **AI 决策层 (LLaMA 3.3 70B)**：基于 P0/P1/P2 逻辑框架，深度解析流值增长与赔率之间的定价误差。
- **高级 Web 面板**：基于玻璃拟态 (Glassmorphism) 设计的高级感看板，实时展示量化报告。
- **一键部署**：完整支持 Docker 容器化，适配各类海外 VPS。

## 🛠️ 技术栈

- **后端**: Python 3.11, FastAPI
- **数据库**: SQLite
- **AI 引擎**: Groq SDK (LLaMA 3.3 70B)
- **部署**: Docker, Docker Compose
- **设计**: 原生 CSS + 玻璃拟态效果

## 📦 快速开始

### 1. 准备工作

- Python 3.11+ 或 Docker
- [Groq API Key](https://console.groq.com/)

### 2. 环境配置

在根目录下创建 `.env` 文件：

```env
GROQ_API_KEY=你的Key
```

### 3. 使用 Docker 部署 (推荐)

```bash
docker-compose up -d --build
```

访问面板地址：`http://localhost:8000`

## 📂 目录结构

```text
PolyMusic/
├── src/
│   ├── data/            # 爬虫与数据库逻辑
│   ├── analysis/        # 量化核心算法
│   └── ai/              # AI 决策管线
├── web/                 # FastAPI 面板与 UI
├── data/                # 本地 SQLite 存储
├── bot_listener.py      # 主程序入口
└── Dockerfile
```

## 📄 许可证

本项目采用 MIT 许可证。
