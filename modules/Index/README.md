# 实时谣言检测系统

基于 **Flask + RSS(SSE) + Chart.js** 的最小可运行原型：
- 主页展示实时新闻推送（Server-Sent Events）。
- 启发式“谣言倾向”打分（可替换为你自己的模型）。
- 折线图（趋势）、柱状图（来源分布）、饼图（谣言占比）。

## 快速开始

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
# 浏览器打开 http://127.0.0.1:5000
```

> **国内长期可用的实时新闻源**：建议使用自建 **RSSHub** 实例作为统一抓取层；
> 默认代码使用了 `https://rsshub.app/...` 路径作为示例，你可以：
> - 将 `FEED_URLS` 替换为你自建 RSSHub 的域名；
> - 或者改为你网络可达的官方 RSS 源。

## 配置

通过环境变量调整：

- `DB_PATH`：SQLite 连接串（默认 `sqlite:///rumor.db`）
- `POLL_INTERVAL`：轮询间隔秒（默认 60）
- `MAX_ITEMS_PER_FEED`：每源拉取条数（默认 30）

在 `app.py` 顶部修改 `FEED_URLS` 以增删新闻源。

## 说明

- 本示例仅为功能原型，启发式规则用于演示，生产建议引入标注数据训练模型；
- 如果部署在多副本环境，请将 SSE 改为消息中间件广播（如 Redis pub/sub）。
