# -*- coding: utf-8 -*-
import os
import time
import threading
import queue
import hashlib
import json
import torch
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

import feedparser
import requests
from flask import Flask, render_template, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from transformers import pipeline, AutoTokenizer
from bs4 import BeautifulSoup


# ------------ 配置 -------------
DB_PATH = os.environ.get("DB_PATH", "sqlite:///rumor.db")
# 可配置 RSSHub 实例 / 直连RSS。为了长期可用，建议自行部署 RSSHub，或将下述链接替换为你所在网络可访问的稳定源。
FEED_URLS = [
    # RSSHub
    r"https://rsshub.app/gov/miit/zcjd",
    # "https://rsshub.rssforever.com/cctv/xwlb",
    # "https://rsshub.rssforever.com/36kr/newsflashes",
    r"https://rsshub.rssforever.com/guancha/headline",
    # "http://127.0.0.1:1200/cctv/xwlb",
]

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))  # 轮询间隔（秒）
MAX_ITEMS_PER_FEED = int(os.environ.get("MAX_ITEMS_PER_FEED", "30"))

# ------------ Flask & DB -------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


def translate_with_zhipu(text,
                         api_key=r"7eaba50915a641379732f5c0f50cbe11.QlJ9StdNwa1OZZkb",
                         model='glm-4-flash',
                         target_lang='en',
                         source_lang='cn'):
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,  # 可选其他模型如 glm-3-turbo
        "messages": [
            # {"role": "system", "content": "你是一个翻译助手，把%s翻译成%s，不需要解释说明"%(source_lang,target_lang)},
            {"role": "system", "content": f"你是一个翻译助手，把{source_lang}翻译成{target_lang}，不需要解释说明"},
            {"role": "user", "content": text}
        ],
        "temperature": 0.2
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("[翻译接口出错]", e)
        return "(翻译失败)"


class NewsItem(db.Model):
    __tablename__ = "news_items"
    id = db.Column(db.Integer, primary_key=True)
    guid = db.Column(db.String(64), unique=True, index=True, nullable=False)  # 去重Key
    title = db.Column(db.String(512))
    link = db.Column(db.String(1024))
    source = db.Column(db.String(128))
    published = db.Column(db.DateTime, index=True)
    summary = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_fake_news = db.Column(db.Boolean, default=None)
    fake_news_score = db.Column(db.Float, default=None)

def init_db():
    with app.app_context():
        db.create_all()


# 全局谣言检测模型（建议只加载一次）
rumor_clf = None
tokenizer = None

def load_rumor_model():
    global rumor_clf, tokenizer
    rumor_clf = pipeline(
        "text-classification",
        model="./model/Fake-News-Bert-Detect",
        tokenizer="./model/Fake-News-Bert-Detect",
        device=0 if torch.cuda.is_available() else -1,
        truncation=True  # ✅ 自动截断
    )
    tokenizer = AutoTokenizer.from_pretrained(r'./model/Fake-News-Bert-Detect')


def compute_guid(title: str, link: str) -> str:
    raw = (title or "") + "|" + (link or "")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


# SSE 事件队列
event_q = queue.Queue(maxsize=1000)

def put_event(payload: dict):
    try:
        event_q.put_nowait(payload)
    except queue.Full:
        # 丢弃最旧的一条，保证实时性
        try:
            event_q.get_nowait()
            event_q.put_nowait(payload)
        except Exception:
            pass

def sse_stream():
    # 持续向客户端推送
    while True:
        data = event_q.get()
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

def fetch_feed(url: str):
    parsed = feedparser.parse(url)
    items = []
    for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        # 发布时间
        published = None
        if entry.get("published_parsed"):
            published = datetime(*entry.published_parsed[:6])
        elif entry.get("updated_parsed"):
            published = datetime(*entry.updated_parsed[:6])
        else:
            published = datetime.utcnow()

        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "published": published,
            "source": urlparse(url).netloc,
        })
    return items

def poller():
    # 后台线程：周期性拉取新闻
    while True:
        try:
            for url in FEED_URLS:
                items = fetch_feed(url)
                with app.app_context():
                    for it in items:
                        guid = compute_guid(it["title"], it["link"])
                        if not NewsItem.query.filter_by(guid=guid).first():
                            # 抓取页面并用模型，详细检测 ---
                            full_text = ""
                            try:
                                headers = {
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                                }
                                resp = requests.get(it["link"], headers=headers, timeout=10)
                                soup = BeautifulSoup(resp.text, "html.parser")
                                content = soup.select_one('div.content.all-txt')
                                full_text = content.get_text(separator="\n", strip=True)                # 仅提取文本
                                full_text = translate_with_zhipu(full_text)                             # 中文翻译成英文
                                full_text = re.sub(r'\s+', ' ', full_text).strip()                      # 去除换行符

                                print(full_text)
                                print('------------------------------------')
                            except Exception as e:
                                print(f"抓取 {it['link']} 失败：{e}")

                            clf_result = None
                            if full_text:
                                try:
                                    clf_result = rumor_clf(full_text, truncation=True)[0]
                                    is_fake = clf_result["label"] == "LABEL_0"
                                    clf_score = round(clf_result["score"], 4)

                                    print(clf_result["label"])
                                except Exception as e:
                                    is_fake = None
                                    clf_score = None
                            else:
                                is_fake = None
                                clf_score = None
                            # --- 模型检测结束 ---

                            row = NewsItem(
                                guid=guid,
                                title=it["title"],
                                link=it["link"],
                                source=it["source"],
                                published=it["published"],
                                summary=it["summary"],
                                is_fake_news=is_fake,
                                fake_news_score=clf_score,
                            )
                            db.session.add(row)
                            db.session.commit()
                            put_event({
                                "type": "news",
                                "payload": {
                                    "title": row.title,
                                    "link": row.link,
                                    "source": row.source,
                                    "published": row.published.isoformat(),
                                    "fake_news_score": row.fake_news_score,
                                    "is_fake": row.is_fake_news,
                                }
                            })
        except Exception as e:
            put_event({"type": "error", "payload": {"msg": str(e)}})
        time.sleep(POLL_INTERVAL)

# ------------ 路由 -------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stream")
def stream():
    return Response(sse_stream(), mimetype="text/event-stream")

@app.route("/api/news")
def api_news():
    limit = int(request.args.get("limit", 50))  # 控制爬取新闻的数量
    rows = NewsItem.query.order_by(NewsItem.published.desc()).limit(limit).all()
    data = [{
        "title": r.title,
        "link": r.link,
        "source": r.source,
        "published": r.published.isoformat() if r.published else None,
        "is_fake": r.is_fake_news,
        "fake_news_score": r.fake_news_score
    } for r in rows]
    return jsonify(data)

@app.route("/api/stats")
def api_stats():
    # 按天聚合近7天
    now = datetime.utcnow()
    start = now - timedelta(days=6)
    rows = (db.session.query(NewsItem)
            .filter(NewsItem.published >= start)
            .all())

    # 时间序列
    ts = {}
    by_source = {}

    rumor_vs_not = {"rumor": 0, "not_rumor": 0}
    for r in rows:
        day = (r.published.date() if r.published else now.date()).isoformat()

        ts.setdefault(day, {"rumor": 0, "not_rumor": 0})
        if r.is_fake_news:
            ts[day]["rumor"] += 1
            rumor_vs_not["rumor"] += 1
        else:
            ts[day]["not_rumor"] += 1
            rumor_vs_not["not_rumor"] += 1
        by_source.setdefault(r.source, 0)
        by_source[r.source] += 1

    # 确保每一天都有
    days = [(start + timedelta(days=i)).date().isoformat() for i in range(7)]
    series = {
        "labels": days,
        "rumor": [ts.get(d, {}).get("rumor", 0) for d in days],
        "not_rumor": [ts.get(d, {}).get("not_rumor", 0) for d in days],
    }

    fake_vs_real = {"fake": 0, "real": 0, "unknown": 0}
    for r in rows:
        if r.is_fake_news is True:
            fake_vs_real["fake"] += 1
        elif r.is_fake_news is False:
            fake_vs_real["real"] += 1
        else:
            fake_vs_real["unknown"] += 1

    return jsonify({
        "series": series,
        "by_source": by_source,
        "rumor_vs_not": rumor_vs_not,
        "fake_vs_real": fake_vs_real
    })

@app.route("/api/first_news_page")
def api_first_news_page():
    # 获取最新一条新闻
    row = (NewsItem.query
           .order_by(NewsItem.published.desc())
           .first())
    if not row:
        return jsonify({"error": "no news yet"}), 404
    url = row.link or ""
    try:
        # 以常见浏览器头部抓取，提升成功率
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        return jsonify({"title": row.title, "link": url, "html": f"<p>抓取失败：{e}</p>"}), 200

    # 为了避免相对路径资源失效，在 <head> 注入 <base>，让图片/样式/链接相对定位能生效
    # 如果页面没有 <head>，则简单拼到最前面
    base_tag = f'<base href="{url}" />'
    if "<head" in html.lower():
        html = html.replace("<head>", f"<head>{base_tag}", 1)
        html = html.replace("<HEAD>", f"<HEAD>{base_tag}", 1)
    else:
        html = f"<!DOCTYPE html><html><head>{base_tag}</head><body>" + html + "</body></html>"

    return jsonify({"title": row.title, "link": url, "html": html})


# 对每条新闻进行验证
@app.route("/api/verify_news", methods=["POST"])
def verify_news():
    # 模型初始化
    clf = pipeline(
      "text-classification",
      model=r"./model/Fake-News-Bert-Detect",
      tokenizer=r"./model/Fake-News-Bert-Detect",
      device=0 if torch.cuda.is_available() else -1
    )
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "no text"}), 400
    try:
        result = clf(text[:512])[0]  # 或 full_text[:2048] 再手动截断 token
        label = result["label"]
        score = result["score"]
        is_fake = (label == "LABEL_0")
        return jsonify({
            "label": "虚假" if is_fake else "真实",
            "score": round(score, 4),
            "raw_label": label
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    init_db()             # 加载 新闻数据
    load_rumor_model()    # 加载 谣言检测模型
    t = threading.Thread(target=poller, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", "5017"))
    app.run(host="127.0.0.1", port=port, threaded=True, debug=True)


if __name__ == "__main__":
    main()
