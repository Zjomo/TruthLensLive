# 导入模块
import os
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field ,field_validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import requests
import spacy

import logging
import traceback
import uuid
import re
import uvicorn
import asyncio

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from logging import Handler
from pyserxng import SearXNGClient, SearchConfig
from pyserxng.models import SearchCategory,SafeSearchLevel
from langchain.chat_models import ChatZhipuAI
from typing import List, Optional
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from ReliableHostSource import reliable_sources
from transformers import pipeline


# 1、可信源
reliable_sources

# 2、配置日志文件
logging.basicConfig(
    level=logging.INFO,                                                         # 设置日志级别为：INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'               # 设置日志格式
)
logger = logging.getLogger(__name__)                                            # 提取当前模块的日志记录器，用于记录日志信息


# 添加 FileHandler 将日志写入 logging.log 文件
file_handler = logging.FileHandler("logging.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

load_dotenv()                                                                   # 加载环境变量【.env文件】

# 生成 API 实例
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


# 把根路径重定向到静态首页（也可直接 FileResponse 返回 index.html）
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")


# 捕获正在运行的事件循环
@app.on_event("startup")
async def _capture_loop():
    app.state.main_loop = asyncio.get_running_loop()


# logger 通过 WebSocket将日志推送到前端
connected_clients: List[WebSocket] = []
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # 可接收心跳，保持连接
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def broadcast_log(message: str):
    for client in connected_clients:
        try:
            await client.send_text(message)
        except:
            connected_clients.remove(client)


class WebSocketLogHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        try:
            loop = getattr(app.state, "main_loop", None)
            if loop and loop.is_running():
                # 线程安全派发到主 loop
                loop.call_soon_threadsafe(asyncio.create_task, broadcast_log(log_entry))
            else:
                # 兜底
                print(log_entry)
        except Exception as e:
            print(f"Failed to send log to WebSocket: {e}")


ws_handler = WebSocketLogHandler()
fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ws_handler.setFormatter(fmt)
logger.addHandler(ws_handler)


# 3、导入分词模型，并输出日志信息
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("成功加载了 spaCy 模型")
except Exception as e:
    logger.error(f"加载 spaCy 模型失败: {str(e)}")
    logger.error("尝试下载模型...")
    try:
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
        nlp = spacy.load("en_core_web_sm")
        logger.info("成功下载并加载了 spaCy 模型")
    except Exception as download_error:
        logger.critical(f"下载 spaCy 模型失败: {str(download_error)}")
        logger.critical("继续运行，但不支持 NLP 功能")
        nlp = None


# 4、允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------- 5、本地BERT虚假新闻检测模型 -----------------------------

try:
    clf = pipeline(
        "text-classification",
        model=r"F:\0_MyProject\TruthLensLive\modules\Index\model\Fake-News-Bert-Detect",
        tokenizer=r"F:\0_MyProject\TruthLensLive\modules\Index\model\Fake-News-Bert-Detect",
        device=0,
        truncation=True
    )
    logger.info("Fake-News-Bert 模型加载成功")
except Exception as e:
    logger.error(f"加载 BERT 模型失败: {str(e)}")
    clf = None


# ----------------------------- 6、大模型 API接入 -- 用于优化 输出的分析结果  -----------------------------
# 初始化大语言模型
llm = ChatZhipuAI(
    model_name="GLM-4-Flash",
    zhipuai_api_key=r'3788341215274329929d1b9cf955d43c.92BSbl8CC63KfwmG'
)




# ----------------------------- 新闻域名验证 ------------------------------
# 验证新闻是否为空 or 是否包含空格 && 验证 URL是否有效 -- 用于结构化 client.py 的post数据信息 -- headline, content, source_url
class NewsVerificationRequest(BaseModel):
    headline: str
    content: str
    source_url: str = Field(default="")

    # 验证输入数据(headline, content)是否为空【field_validator是声明好的装饰器方法】
    @field_validator('headline', 'content')
    def must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    # 验证 URL (source_url)是否符合规范
    @field_validator('source_url')
    def validate_url(cls, v):
        if v and v.strip():
            # Simple URL validation
            url_pattern = re.compile(
                r'^(?:http|https)://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)

            if not url_pattern.match(v.strip()):
                raise ValueError('Invalid URL format')
            return v.strip()
        return ""


# ----------------------------- 可信源验证 ------------------------------
# 验证 URL 是否来自可靠的 URL源
def is_from_reliable_source(url):
    try:
        # 日志：URL 为空
        if not url:
            logger.debug("Empty URL provided to is_from_reliable_source")
            return False

        # 提取域名，并将其设为小写
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # 去除 "www." ，并打印 "验证域名"的日志消息
        if domain.startswith('www.'):
            domain = domain[4:]
        logger.debug(f"Checking domain: {domain}")

        # 提取基础域名，如：subdomain.example.com ->  example.com
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            base_domain = '.'.join(domain_parts[-2:])
        else:
            base_domain = domain

        # New extended domain checking logic
        for source in reliable_sources:
            # 域名 匹配 可信源
            if domain == source:
                logger.debug(f"Direct match found for {domain}")
                return True

            # 子域名 匹配 可行源
            if domain.endswith(f".{source}"):
                logger.debug(f"Subdomain match found for {domain} with source {source}")
                return True

            # 路径域名 匹配 可信源   如：medium.com/reliable-publisher ->  medium.com
            if source.endswith(f".{domain}"):
                logger.debug(f"Path-based match found for {domain} with source {source}")
                return True

            # 基础域名（类似子域名） 可信源
            if base_domain == source:
                logger.debug(f"Base domain match found for {domain}")
                return True

        logger.debug(f"No reliable source match found for {domain}")
        return False
    except Exception as e:
        logger.error(f"Error parsing URL {url}: {str(e)}")
        return False


'''
headline = 'AI'
entities = 'Musk says AI will take over the world'
query = headline + entities
'''


# ----------------------------- 搜索引擎API搜索 -- 响应对象 -------------------
def Search_Engines(query):
    client = SearXNGClient()                           # 初始化
    config = SearchConfig(                             # 客户端搜索 配置
        categories=[SearchCategory.GENERAL],
        language="en",
        safe_search=SafeSearchLevel.MODERATE,
        page=1)
    news_results = client.search_news(query)  # 开搜
    for i in range(len(news_results.results)):
        result_ = news_results.results[i]
        response = requests.get(result_.url, timeout=15)
        if response.status_code == 200:
            return response
        else:
            assert('搜索失败')


# ----------------------------- 翻译工具 -- 智谱  -------------------
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


# ----------------------------- 搜索引擎API搜索 -- 域名 -------------------
def Search_Engines_Link(query):
    client = SearXNGClient()                           # 初始化
    search_results = {"organic_results": []}
    config = SearchConfig(                             # 客户端搜索 配置
        categories=[SearchCategory.GENERAL],
        language="en",
        safe_search=SafeSearchLevel.MODERATE,
        page=1)
    news_results = client.search_news(query)  # 开搜
    for i in range(len(news_results.results)):
        result_ = news_results.results[i]
        host = result_.url.host
        search_results['organic_results'].append({'link':host})
    return search_results


# ----------------------------- 新闻域名测试 -----------------------------
@app.get("/test-domain")
# 异步函数，允许程序等待"用户操作 -- 异步操作"后执行
async def test_domain(url: str):
    """Endpoint to test domain matching logic"""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]

        # Extract base domain for better matching
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            base_domain = '.'.join(domain_parts[-2:])
        else:
            base_domain = domain

        matching_sources = []
        for source in reliable_sources:
            if (domain == source or
                domain.endswith(f".{source}") or
                source.endswith(f".{domain}") or
                base_domain == source):
                matching_sources.append(source)

        is_reliable = len(matching_sources) > 0

        return {
            "url": url,
            "parsed_domain": domain,
            "base_domain": base_domain,
            "is_reliable_source": is_reliable,
            "matching_sources": matching_sources,
            "reliable_sources_checked": len(reliable_sources)
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error analyzing domain: {str(e)}"
        )
# ----------------------------- 虚假新闻分类  -----------------------------
'''
处理新闻的分类请求，主要包含：
当收到一则请求时，会进行如下操作：
1、进行输入验证
2、进行url验证
3、进行命名实体验证
4、进行搜索引擎API搜索
5、对API搜索的URL源进行可行性研究
6、最终基于llm进行虚假新闻的最终分类
'''

@app.post("/verify")
async def verify_news(news: NewsVerificationRequest):
    try:
        # 生成 -- session ID
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        logger.info(f"[{session_id}] Received verification request at {datetime.utcnow().isoformat()}")

        # 初始化 -- 验证信息
        found_in_reliable_sources = False
        direct_source_verified = False
        potential_match = False
        fake_news = None
        final_verdict = None
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        current_user = "NewsVerifierSystem"
        api_failures = []
        search_results_count = 0
        matched_source_urls = []

        # 生成 -- 验证ID
        verification_id = f"{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

        # 验证 -- 输入数据的格式 -- headline & content
        if not news.headline or not news.headline.strip():
            logger.error(f"[{session_id}] Empty headline provided")
            raise HTTPException(
                status_code=400,
                detail="Headline cannot be empty"
            )
        if not news.content or not news.content.strip():
            logger.error(f"[{session_id}] Empty content provided")
            raise HTTPException(
                status_code=400,
                detail="Content cannot be empty"
            )
        logger.info(f"[{session_id}] Processing 标题: {news.headline[:50]}...")
        logger.info(f"[{session_id}] Processing 内容字符数: {len(news.content)} characters")
        if news.source_url:
            logger.info(f"[{session_id}] 源URL: {news.source_url}")

        # 单模态谣言检测
        bert_result = None
        if clf:
          try:
            text_trans = translate_with_zhipu(news.content)
            prediction = clf(text_trans[:512])[0]  # 截断至BERT最大长度
            logger.info('这里👇')
            logger.info(text_trans)
            label_map = {"LABEL_0": "假新闻", "LABEL_1": "真实新闻"}
            bert_result = {
              "bert_label": label_map.get(prediction["label"], prediction["label"]),
              "bert_score": round(prediction["score"] * 100, 2)
            }
            logger.info(f"[{session_id}] BERT 检测结果: {bert_result}")
          except Exception as e:
            logger.warning(f"[{session_id}] BERT 检测失败: {str(e)}")

        # 简化 -- 标准化输入
        news.headline = news.headline.strip()
        news.content = news.content.strip()

        # 直接验证 -- 若本"新闻源"与"可靠源"重合，则说明该"新闻源"是可靠的
        if news.source_url:
            logger.info(f"[{session_id}] 验证提供的源URL: {news.source_url}")
            if is_from_reliable_source(news.source_url):
                logger.info(f"[{session_id}] 源URL直接验证为可靠: {news.source_url}")
                direct_source_verified = True
                found_in_reliable_sources = True
                potential_match = True
                matched_source_urls.append(news.source_url)
            else:
                logger.warning(f"[{session_id}] 提供的源URL不在可靠源列表中: {news.source_url}")

        # 命名实体提取
        entities = ""
        if nlp:
            try:
                doc = nlp(news.headline + " " + news.content[:1000])  # Limit content length for entity extraction
                entities = " ".join([ent.text for ent in doc.ents if ent.label_ in ["ORG", "GPE", "PERSON", "LOC", "DATE", "EVENT"]])
                logger.info(f"[{session_id}] 提取实体: {entities[:100]}...")
                if not entities:
                    logger.warning(f"[{session_id}] 未找到实体")
                    entities = news.headline  # Fall back to using the headline for searching
            except Exception as e:
                logger.error(f"[{session_id}] 实体提取错误: {str(e)}")
                logger.error(traceback.format_exc())
                entities = news.headline  # Fall back to using the headline for searching
        else:
            logger.warning(f"[{session_id}] 使用标题进行搜索，因为NLP不可用")
            entities = news.headline

        # 间接验证 -- 通过搜索结果 与 可信源对比，根据数量确定准确率
        if not direct_source_verified:
            search_results = {"organic_results": []}
            search_query = f"{news.headline} {entities[:100]}"

            logger.info(f"[{session_id}] 初始化搜索API请求，搜索关键字： {search_query[:50]}...")
            response_search = Search_Engines_Link(search_query)

            search_results = response_search
            search_results_count += len(search_results.get("organic_results", []))
            logger.info(f"[{session_id}] SearchAPI 返回 {search_results_count} 个结果")

            # 将搜索结果 与 可信源 进行匹配
            for result in search_results.get("organic_results", []):
                result_url = result.get("link", "")
                if is_from_reliable_source(result_url):
                    found_in_reliable_sources = True
                    logger.info(f"[{session_id}] 发现可靠来源匹配: {result_url}")

        # 验证结果打印
        logger.info(f"[{session_id}] 发现可靠来源: {found_in_reliable_sources}")
        logger.info(f"[{session_id}] 直接来源验证: {direct_source_verified}")
        logger.info(f"[{session_id}] 可能匹配: {potential_match}")
        logger.info(f"[{session_id}] 搜索结果数量: {search_results_count}")
        logger.info(f"[{session_id}] 匹配可靠来源: {matched_source_urls}")

        # 基于RAG的 "直接来源" + "可靠来源" 辅助评估
        source_confidence = 0
        if direct_source_verified:
            source_confidence = 90  # 直接来源验证 高置信度
            logger.info(f"[{session_id}] 来源置信度: 90 (直接验证)")
        elif found_in_reliable_sources:
            # 基于搜索结果数量 评分
            source_confidence = min(85, 50 + (len(matched_source_urls) * 10))
            logger.info(f"[{session_id}] 来源置信度: {source_confidence} ({len(matched_source_urls)} 匹配)")
        elif search_results_count > 0:
            # 存在搜索结果 但没有可靠来源
            source_confidence = 30
            logger.info(f"[{session_id}] 来源置信度: 30 (无可靠匹配)")
        else:
            # 没有搜索结果
            source_confidence = 10
            logger.info(f"[{session_id}] 来源置信度: 10 (无搜索结果)")

        # 基于LLM + prompt 进行新闻验证
        try:
            # Current date for context
            current_date = datetime.now().strftime("%Y-%m-%d")

            prompt = ChatPromptTemplate.from_template("""
            你是一个高级的新闻验证系统，请分析下述内容：

            标题: {headline}
            内容: {content}

            当前日期: {current_date}
            其他信息：
            - 已发现的可靠来源: {found_in_sources}
            - 直接来源验证: {direct_verified}
            - 来源置信度评分: {source_confidence}/100
            - 实体匹配情况: {has_matches}
            - 搜索结果数量: {search_count}
            - 匹配的可靠来源: {matched_sources}

            请极其谨慎地进行分析，尤其是对于以下方面的声明：
            - 死亡或伤害
            - 重大事件或灾难
            - 政治声明
            - 金融市场
            - 公共卫生信息

            重要说明：
            1. 不要仅凭日期将新闻标记为虚假，因为有些文章可能合法地引用未来事件或日期。
            2. 聚焦于事实不一致、逻辑矛盾、证据验证。
            3. 如果来源验证成功（直接或间接），请高度重视这一积极信号。
            4. 考虑内容中声明的性质和具体性。
            5. 如果新闻来自经过验证的可靠来源，且没有明显的矛盾或不合理之处，倾向于验证其真实性。

            请提供详细的分析，随后给出最终结论。

            你的结论必须是以下确切短语之一，并单独成行：
            "结论：已验证"（当对真实性有很高把握，特别是有可靠来源确认时使用）
            "结论：疑似为假"（用于有明确的伪造证据、逻辑缺失的情况）
            "结论：待进一步验证"（用于不确定的情况）
            """)

            logger.info(f"[{session_id}] LLM 分析初始化")
            chain = prompt | llm

            # 填充prompt中的变量
            llm_response = chain.invoke({
                "headline": news.headline,
                "content": news.content,
                "found_in_sources": "Yes" if found_in_reliable_sources else "No",
                "direct_verified": "Yes" if direct_source_verified else "No",
                "source_confidence": source_confidence,
                "has_matches": "Yes" if potential_match else "No",
                "search_count": search_results_count,
                "matched_sources": ", ".join(matched_source_urls[:3]) if matched_source_urls else "None",
                "current_date": current_date
            })
            logger.info(f"[{session_id}] LLM 分析完成")

        except Exception as e:
            logger.error(f"[{session_id}] LLM 分析报错信息: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"LLM 分析期间的报错信息: {str(e)}"
            )

        # 解析LLM 输出内容
        llm_response_upper = llm_response.content.upper()

        print(llm_response_upper)

        # 定义假新闻 标签
        fake_indicators = [
            "疑似为假", "假", "不可信", "未验证",
            "错误信息", "没有证据", "无法验证",
            "可疑", "误导", "伪造",'不真实', '虚假',
            '不实','不合法', '不可信', '谣言', '传闻',
            "未经证实", "未经验证", "不可靠", "不实",
        ]

        # 定义可信新闻 标签
        verify_indicators = [
            "已验证", "可信", "已证实", "确认",
            "真实", "合法", "可信", "事实", "证据",
            "可靠来源", "已确认", "已核实", "已证实",
            '真实', '合法', '可信', '事实', '证据',
        ]

        # 综合验证新闻的虚假性
        fake_score = sum(1 for indicator in fake_indicators if indicator in llm_response_upper)
        verify_score = sum(1 for indicator in verify_indicators if indicator in llm_response_upper)

        # 改进逻辑后,做出判断 (更加重视来源验证)
        if "已验证" in llm_response_upper:
            if direct_source_verified or (found_in_reliable_sources and source_confidence >= 60) or verify_score > 2:
                final_verdict = "已验证"
                fake_news = False
                logger.info(f"[{session_id}] 内容已验证真实")
            else:
                final_verdict = "待进一步验证"
                fake_news = None
                logger.info(f"[{session_id}] 内容标记为进一步验证 - LLM 结论积极但来源置信度较弱")
        elif "疑似为假" in llm_response_upper:
            # 若新闻来源已验证，但 LLM分类为假，则需进一步验证
            if direct_source_verified:
                final_verdict = "待进一步验证"
                fake_news = None
                logger.info(f"[{session_id}] 内容标记为进一步验证 - 来源验证与 LLM 分析之间存在冲突")
            else:
                final_verdict = "疑似为假"
                fake_news = True
                logger.info(f"[{session_id}] 内容标记为：疑似为假")
        else:
            final_verdict = "待进一步验证"
            fake_news = None
            logger.info(f"[{session_id}] 内容标记为：待进一步验证")

        # 基于验证信息，反馈对应的 message
        if fake_news is False:
            status_message = f"""✅ 已验证 | 置信水平: 高

**VERIFICATION REPORT ID**: VR-{verification_id}

🔍 该新闻经过我们的验证系统分析，似乎是真实的。
{"内容来自直接验证的可靠来源。" if direct_source_verified else "内容已与可靠来源交叉引用。"}
它通过了我们的事实检查标准。

**验证完成时间**: {current_time}
"""
        elif fake_news is True:
            status_message = f"""⚠️ 疑似为假 | 置信水平: 高

**ALERT REPORT ID**: FR-{verification_id}

🔍 我们的验证系统检测到该内容存在潜在的可靠性问题。
在分享或处理此信息之前，请谨慎行事。

**验证完成时间**: {current_time}
"""
        else:
            status_message = f"""🔄 待验证 | 状态: 进行中

**ASSESSMENT ID**: PR-{verification_id}

🔍 该内容需要进一步验证。我们的系统无法根据现有信息明确判断其真实性。

**初步评估完成时间**: {current_time}
"""

        # 构建"信息验证"矩阵
        verification_metrics = {
            "source_validation_score": source_confidence,
            "content_reliability_index": 85 if fake_news is False else 30 if fake_news is True else 50,
            "entity_verification_status": "Validated" if fake_news is False else "Failed" if fake_news is True else "Pending",
            "ai_confidence_level": "High" if direct_source_verified or source_confidence >= 70 or abs(verify_score - fake_score) > 2 else "Medium",
            "analyst": current_user,
            "verification_id": verification_id,
            "api_failures": api_failures,
            "search_results_found": search_results_count,
            "direct_source_verified": direct_source_verified,
            "matched_reliable_sources": len(matched_source_urls)
        }

        # 反馈验证信息
        return {
          "bert_result": bert_result,
          "verdict": final_verdict,
            "status_message": status_message,
            "llm_response": llm_response.content,
            "verification_data": {
                "direct_source_verified": direct_source_verified,
                "found_in_reliable_sources": found_in_reliable_sources,
                "potential_match": potential_match,
                "source_confidence": source_confidence,
                "fake_indicators_found": fake_score,
                "verify_indicators_found": verify_score,
                "matched_sources": matched_source_urls[:5] if matched_source_urls else [],
                "verification_metrics": verification_metrics,
                "timestamp_utc": current_time,
                "analyst": current_user,
                "report_id": f"{'VR' if fake_news is False else 'FR' if fake_news is True else 'PR'}-{verification_id}"
            }
        }

    except Exception as e:
        logger.error(f"未预期报错: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"未预期报错: {str(e)}"
        )


# 动态新闻接口
class NewsItem(BaseModel):
    title: str
    url: str
    host: str
    snippet: Optional[str] = ""
    published_at: Optional[str] = ""
    reliable: bool = False  # 是否命中你的可靠源库


def _normalize_host(u: str) -> str:
    try:
        return urlparse(u).netloc.lower()
    except:
        return ""


@app.get("/news/search", response_model=List[NewsItem])
async def news_search(q: str, page: int = 1, limit: int = 20):
    """
    基于 SearXNG 的新闻搜索，返回结构化结果并标注是否为可靠源。
    """
    try:
        client = SearXNGClient()
        config = SearchConfig(
            categories=[SearchCategory.GENERAL],
            language="en",
            safe_search=SafeSearchLevel.MODERATE,
            page=page
        )
        results = client.search_news(q)
        items: List[NewsItem] = []
        seen = set()

        for r in results.results:
            # 尽量兼容不同字段名称
            title = getattr(r, "title", "") or getattr(r, "name", "") or ""
            url = str(getattr(r, "url", "") or getattr(r, "link", "") or "")
            snippet = getattr(r, "content", "") or getattr(r, "snippet", "") or getattr(r, "summary", "") or ""
            published_at = getattr(r, "published", "") or getattr(r, "publishedDate", "") or ""

            if not url or (url in seen):
                continue
            seen.add(url)

            host = _normalize_host(url)
            items.append(NewsItem(
                title=title[:300] if title else "(无标题)",
                url=url,
                host=host,
                snippet=snippet[:500] if snippet else "",
                published_at=str(published_at)[:32] if published_at else "",
                reliable=is_from_reliable_source(url)
            ))
            if len(items) >= limit:
                break
        return items
    except Exception as e:
        logger.error(f"/news/search error: {e}")
        raise HTTPException(status_code=500, detail="搜索服务暂不可用")


from fastapi.responses import JSONResponse

@app.get("/logs")
async def read_logs():
    try:
        with open("logging.log", "r", encoding="utf-8") as f:
            content = f.read()
        return JSONResponse(content={"status": "success", "log": content})
    except FileNotFoundError:
        return JSONResponse(content={"status": "error", "log": "日志文件不存在。"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "log": str(e)})

from fastapi.responses import FileResponse

@app.get("/download_log")
async def download_log():
    try:
        return FileResponse("logging.log", filename="logging.log", media_type="text/plain")
    except FileNotFoundError:
        return JSONResponse(content={"status": "error", "message": "日志文件不存在。"})


if __name__ == "__main__":
    # 启动
    logger.info("虚假新闻识别 API 启动...")
    # 日志广播

    uvicorn.run(app, host="127.0.0.1", port=5018)



