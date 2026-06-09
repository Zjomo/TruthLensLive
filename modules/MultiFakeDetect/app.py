import os
import sys
import shutil
import logging
import pandas as pd
import uvicorn
import re
import subprocess
import yt_dlp

from urllib.parse import urlparse
from time import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from Inference_run import Run
from VideoProcess import Process

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
console = Console()

# 设定路径
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# -----------------------------
# FastAPI app setup
# -----------------------------
app = FastAPI(title="VideoAIClip Web API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 输出文件夹
UPLOADS_DIR = PROJECT_ROOT / "uploads"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

# 加载输出，以便文件能导出道输出文件夹
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR), html=False), name="outputs")
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR), html=False), name="uploads")


# 设置日志
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("videoaiclip")


# ========================
# Helpers & Defaults
# ========================
DEFAULT_CSV_PATH = Path(os.getenv(
    "PREDICT_CSV_PATH",
    str(PROJECT_ROOT / "predict_result" / "FakeJM" / "FakingRecipe.csv"),
))
DEFAULT_CKP = os.getenv("INFERENCE_CKP", "./provided_ckp/FakingRecipe_fakesv")
DEFAULT_DEVICE = os.getenv("INFER_GPU", "0")  # e.g., "0" or "cpu"
DEFAULT_BATCH = int(os.getenv("INFER_BATCH", "1"))


def _copy_csv_to_run_folder(csv_path: Path, run_dir: Path) -> Optional[str]:
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        dst = run_dir / "predictions.csv"
        shutil.copyfile(csv_path, dst)
        rel = dst.relative_to(OUTPUTS_DIR)
        return f"/outputs/{rel.as_posix()}"
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
async def root_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>VideoAIClip</h1><p>Put your frontend at ./frontend/index.html</p>")


@app.post("/api/process")
async def api_process(
    file: UploadFile = File(...),
    news_text: str = Form(...),
    device: str = Form(DEFAULT_DEVICE),
    inference_ckp: str = Form(DEFAULT_CKP),
    batch_size: int = Form(DEFAULT_BATCH),
):
    """Upload an MP4 and a text. Runs feature process + inference, then returns
    text emotion (top-k), audio emotion, and news fake/real + probability.
    """
    try:
        if not file.filename.lower().endswith(".mp4"):
            raise HTTPException(status_code=400, detail="只支持 .mp4 视频文件")

        ts = int(time())
        # Save upload
        uploaded_path = UPLOADS_DIR / f"{ts}_{file.filename}"
        with uploaded_path.open("wb") as f:
            f.write(await file.read())

        # Set CUDA env for this request (optional)
        if device.lower() == "cpu":
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
        else:
            os.environ['CUDA_VISIBLE_DEVICES'] = str(device)
            os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

        # 1) 特征处理：你提供的 Process() 返回音频情绪分类与文本情绪 top-k
        #    注意：你最新代码示例使用 list(News_text)
        audio_emo_cls, topk_labels = Process(str(uploaded_path), news_text, list(news_text))

        # 2) 推理配置（与你的脚本一致，可被表单/环境变量覆盖）
        config = {
            'dataset': 'fakejm',
            'mode': 'inference_test',
            'epoches': 1,
            'batch_size': int(batch_size),
            'early_stop': 5,
            'device': str(device),
            'seed': 2025,
            'lr': 0.001,
            'alpha': 0,
            'beta': 255,
            'inference_ckp': str(inference_ckp),
            'path_ckp': './checkpoints/',
            'path_tb': './tensorboard/'
        }

        # 3) 执行推理
        Run(config=config).main()

        # 4) 读取预测 CSV（兼容逗号/空格/制表/引号）
        csv_path = DEFAULT_CSV_PATH
        if not csv_path.exists():
            raise HTTPException(status_code=500, detail=f"预测CSV不存在: {csv_path}")

        # 让 pandas 自动推断分隔符
        df = pd.read_csv(csv_path, engine='python', sep=None)
        if df.empty:
            raise HTTPException(status_code=500, detail="预测CSV为空")

        # 取最后一行作为本次运行的结果（如果你有更可靠的 vid 匹配逻辑，可替换这里）
        row = df.tail(1).iloc[0]
        try:
            vid = int(row.get('vid'))
        except Exception:
            vid = None
        try:
            label = int(row.get('label'))
        except Exception:
            label = None
        try:
            pred = int(row.get('pred'))
        except Exception:
            pred = None
        try:
            pred_prob = float(row.get('pred_prob')) if 'pred_prob' in df.columns else None
        except Exception:
            pred_prob = None

        fake_or_real = None
        if pred is not None:
            fake_or_real = '假' if pred == 1 else '真'

        # 5) 保存副本到本次 run 的 outputs 目录，供前端下载
        run_dir = OUTPUTS_DIR / str(ts)
        csv_public_url = _copy_csv_to_run_folder(csv_path, run_dir)

        payload = {
            "ts": ts,
            "video_path": str(uploaded_path),
            "text_topk_labels": topk_labels,
            "audio_emo_cls": audio_emo_cls,
            "classification": {
                "vid": vid,
                "label": label,
                "pred": pred,
                "pred_prob": pred_prob,
                "readable": fake_or_real,
            },
            "downloads": {
                "predictions_csv": csv_public_url or str(csv_path)
            }
        }
        return JSONResponse(payload)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Processing failed")
        raise HTTPException(status_code=500, detail=str(e))

def _print_summary_console(n_samples, n_classes, acc, f1, save_csv_path, save_html_path):
    table = Table(title="推理结果摘要", show_lines=True)
    table.add_column("指标", justify="left")
    table.add_column("值", justify="right")
    table.add_row("样本数", str(n_samples))
    table.add_row("类别数", str(n_classes))
    table.add_row("准确率", f"{acc:.4f}")
    table.add_row("F1(宏平均)", f"{f1:.4f}")
    table.add_row("CSV结果", save_csv_path)
    table.add_row("HTML报告", save_html_path)
    console.print(Panel.fit(table, title="✅ 推理完成", border_style="green"))


@app.post("/api/extract_features")
async def api_extract_features(
    file: UploadFile = File(...),
    news_text: str = Form(...),
):
    try:
        if not file.filename.lower().endswith(".mp4"):
            raise HTTPException(status_code=400, detail="只支持 .mp4 视频文件")

        ts = int(time())
        uploaded_path = UPLOADS_DIR / f"{ts}_{file.filename}"
        with uploaded_path.open("wb") as f:
            f.write(await file.read())

        audio_emo_cls, topk_labels = Process(str(uploaded_path), news_text, list(news_text))

        # 缓存结果到 outputs/ts/features.json
        run_dir = OUTPUTS_DIR / str(ts)
        run_dir.mkdir(parents=True, exist_ok=True)
        pd.Series({
            'audio_emo_cls': audio_emo_cls,
            'topk_labels': topk_labels,
            'video_path': str(uploaded_path),
            'news_text': news_text
        }).to_json(run_dir / "features.json")

        return JSONResponse({"ts": ts, "audio_emo_cls": audio_emo_cls, "text_topk_labels": topk_labels})
    except Exception as e:
        logger.exception("特征提取失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/infer")
async def api_infer(
    ts: int = Form(...),
    device: str = Form(DEFAULT_DEVICE),
    inference_ckp: str = Form(DEFAULT_CKP),
    batch_size: int = Form(DEFAULT_BATCH),
):
    try:
        run_dir = OUTPUTS_DIR / str(ts)
        features_file = run_dir / "features.json"
        if not features_file.exists():
            raise HTTPException(status_code=400, detail="未找到对应的特征文件，请先执行特征提取")

        data = pd.read_json(features_file, typ='series')
        video_path = data['video_path']
        news_text = data['news_text']
        audio_emo_cls = data['audio_emo_cls']
        topk_labels = data['topk_labels']

        # 设备设置
        if device.lower() == "cpu":
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
        else:
            os.environ['CUDA_VISIBLE_DEVICES'] = str(device)
            os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

        # 推理
        config = {
            'dataset': 'fakejm',
            'mode': 'inference_test',
            'epoches': 1,
            'batch_size': int(batch_size),
            'early_stop': 5,
            'device': str(device),
            'seed': 2025,
            'lr': 0.001,
            'alpha': 0,
            'beta': 255,
            'inference_ckp': str(inference_ckp),
            'path_ckp': './checkpoints/',
            'path_tb': './tensorboard/'
        }
        Run(config=config).main()

        # CSV 处理
        df = pd.read_csv(DEFAULT_CSV_PATH, engine='python', sep=None)
        row = df.tail(1).iloc[0]
        vid = int(row.get('vid', -1))
        label = int(row.get('label', -1))
        pred = int(row.get('pred', -1))
        pred_prob = float(row.get('pred_prob', 0.0))
        fake_or_real = '假' if pred == 1 else '真'

        csv_url = _copy_csv_to_run_folder(DEFAULT_CSV_PATH, run_dir)

        return JSONResponse({
            "ts": ts,
            "video_path": video_path,
            "text_topk_labels": topk_labels,
            "audio_emo_cls": audio_emo_cls,
            "classification": {
                "vid": vid,
                "label": label,
                "pred": pred,
                "pred_prob": pred_prob,
                "readable": fake_or_real,
            },
            "downloads": {
                "predictions_csv": csv_url or str(DEFAULT_CSV_PATH)
            }
        })
    except Exception as e:
        logger.exception("推理失败")
        raise HTTPException(status_code=500, detail=str(e))



# ==== 新增：简单 URL 与 YouTube 判定 ====
YOUTUBE_DOMAINS = (
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"
)

def is_youtube_url(url: str) -> bool:
    try:
        return any(d in url.lower() for d in YOUTUBE_DOMAINS)
    except Exception:
        return False

# ==== 新增：yt-dlp 下载为 mp4（需要 ffmpeg 存在于 PATH）====
def download_video_via_ytdlp(video_url: str, out_file: Path) -> Optional[Path]:
    # 目标文件形如 uploads/TS_online.mp4
    out_tmpl = str(out_file.with_suffix(""))  # yt-dlp 会自己加扩展名

    ydl_opts = {
        "format": "bv*+ba/b",   # 优先 bestvideo+bestaudio，否则退回最佳单流
        "merge_output_format": "mp4",  # 合并封装为 mp4
        "outtmpl": out_tmpl + ".%(ext)s",
        "noprogress": True,
        "quiet": True,
        # 你也可以按需增加代理、限速、重试等参数
    }
    # 参考：yt-dlp 手册关于合并流需 ffmpeg 支持。:contentReference[oaicite:4]{index=4}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        # 期望得到 mp4；若容器不同，取实际文件
        if "_filename" in info:
            downloaded = Path(info["_filename"])
        else:
            downloaded = Path(ydl.prepare_filename(info))

        # 如不是 mp4，则再用 ffmpeg 快速转封装（拷贝码流）
        if downloaded.suffix.lower() != ".mp4":
            target = out_file.with_suffix(".mp4")
            cmd = ["ffmpeg", "-y", "-i", str(downloaded), "-c", "copy", str(target)]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                downloaded.unlink(missing_ok=True)
            finally:
                return target

        return downloaded

# ==== 新增：对 .mp4/.m3u8 直链的回退（无需 yt-dlp）====
def download_direct_with_ffmpeg(video_url: str, out_file: Path) -> Optional[Path]:
    """
    用 ffmpeg 直接拉取直链（含 m3u8）到 mp4（拷贝码流）。
    部分 m3u8 直存 mp4 可能出现容器索引问题，可先存为 mkv 再二封装为 mp4。:contentReference[oaicite:5]{index=5}
    """
    # 首尝试直接转 mp4
    cmd = ["ffmpeg", "-y", "-i", video_url, "-c", "copy", str(out_file)]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode == 0 and out_file.exists():
        return out_file

    # 若失败，走 mkv → mp4 两步
    tmp_mkv = out_file.with_suffix(".mkv")
    p1 = subprocess.run(["ffmpeg", "-y", "-i", video_url, "-c", "copy", str(tmp_mkv)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p1.returncode == 0 and tmp_mkv.exists():
        p2 = subprocess.run(["ffmpeg", "-y", "-i", str(tmp_mkv), "-c", "copy", str(out_file)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            tmp_mkv.unlink(missing_ok=True)
        finally:
            if p2.returncode == 0 and out_file.exists():
                return out_file
    return None


YTDLP_COMMON_OPTS = {
    # —— 可靠性与限流 ——
    "retries": 5,
    "fragment_retries": 5,
    "extractor_retries": 3,             # < 新增：IE 级重试
    "skip_unavailable_fragments": True,
    "sleep_interval_requests": 1.0,      # < 原来是 1.0，放慢一些
    "socket_timeout": 30,
    "concurrent_fragment_downloads": 1,  # < 降并发更稳
    "nocheckcertificate": True,

    # —— 输出与日志 ——
    "quiet": False,
    "noprogress": False,

    # —— 指纹 ——
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),

    # —— 行为 ——
    "noplaylist": True,
}


def _is_youtube(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
        return any(h in host for h in ["youtube.com", "youtu.be", "m.youtube.com", "www.youtube.com"])
    except Exception:
        return False


def _ytdlp_download_video_to_mp4(video_url: str, out_file: Path) -> Path:
  base_noext = str(out_file.with_suffix(""))
  ydl_opts_with_subs = {
    **YTDLP_COMMON_OPTS,
    "format": "bv*+ba/b",
    "merge_output_format": "mp4",
    "outtmpl": base_noext + ".%(ext)s",
    # 自动字幕（有就拉，用于 news_text 兜底）
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["zh.*", "en.*"],
    "subtitlesformat": "vtt/srt",  # vtt 优先
  }

  def _download(ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=True)
      return Path(info.get("_filename") or ydl.prepare_filename(info))

  try:
    downloaded = _download(ydl_opts_with_subs)
  except yt_dlp.utils.DownloadError as e:
    # 只要是“字幕相关”或“429 限流”就降级再试（禁用字幕）
    msg = str(e)
    if "subtitles" in msg.lower() or "http error 429" in msg.lower():
      logging.warning("字幕下载失败或被限流，自动降级为不抓字幕后重试：%s", msg)
      ydl_opts_no_subs = {
        **YTDLP_COMMON_OPTS,
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "outtmpl": base_noext + ".%(ext)s",
        # 关键：彻底关闭字幕相关
        "writesubtitles": False,
        "writeautomaticsub": False,
        "subtitleslangs": [],
      }
      downloaded = _download(ydl_opts_no_subs)
    else:
      # 非字幕类错误，按原逻辑抛出
      raise

  # 若不是 mp4，则无损转封装
  if downloaded.suffix.lower() != ".mp4":
    target = out_file.with_suffix(".mp4")
    subprocess.run(
      ["ffmpeg", "-y", "-i", str(downloaded), "-c", "copy", str(target)],
      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
      downloaded.unlink(missing_ok=True)
    finally:
      downloaded = target

  return downloaded


def _ffmpeg_grab_to_mp4(video_url: str, out_file: Path) -> Optional[Path]:
    """
    对直链（含 HLS m3u8）用 ffmpeg 拉取；若直接 mp4 失败 → 先 mkv 再 mp4。
    这么做是因为部分 m3u8 直接封装 mp4 会导致索引/时间轴异常。:contentReference[oaicite:8]{index=8}
    """
    # 直存 mp4（拷贝码流）
    p = subprocess.run(["ffmpeg", "-y", "-i", video_url, "-c", "copy", str(out_file)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode == 0 and out_file.exists():
        return out_file

    # 回退：mkv → mp4
    tmp_mkv = out_file.with_suffix(".mkv")
    p1 = subprocess.run(["ffmpeg", "-y", "-i", video_url, "-c", "copy", str(tmp_mkv)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p1.returncode == 0 and tmp_mkv.exists():
        p2 = subprocess.run(["ffmpeg", "-y", "-i", str(tmp_mkv), "-c", "copy", str(out_file)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tmp_mkv.unlink(missing_ok=True)
        if p2.returncode == 0 and out_file.exists():
            return out_file
    return None

def _maybe_load_auto_subtitle_text(download_dir: Path) -> Optional[str]:
    """简单兜底：抓取下载目录下的 .vtt/.srt 字幕并拼接为纯文本"""
    texts = []
    for ext in (".vtt", ".srt"):
        for p in download_dir.glob(f"*{ext}"):
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                # 极简去时间戳（生产里建议用更稳的 vtt/srt 解析库）
                content = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3}.*\n?", "", content)
                texts.append(content)
            except Exception:
                pass
    return "\n".join(texts).strip() if texts else None


@app.post("/api/process_url")
async def api_process_url(
    video_url: str = Form(...),
    news_text: str = Form(""),          # 允许为空 → 自动字幕兜底
    device: str = Form(DEFAULT_DEVICE),
    inference_ckp: str = Form(DEFAULT_CKP),
    batch_size: int = Form(DEFAULT_BATCH),
):
    try:
        if not isinstance(video_url, str) or not video_url.strip():
            raise HTTPException(status_code=400, detail="请输入有效的视频链接")
        video_url = video_url.strip()

        ts = int(time())
        # 目标 mp4 存放到 uploads，并以 ts 命名
        target_mp4 = UPLOADS_DIR / f"{ts}_online.mp4"

        # 选择合适的抓取策略
        downloaded: Optional[Path] = None
        if _is_youtube(video_url):
            downloaded = _ytdlp_download_video_to_mp4(video_url, target_mp4)
        else:
            downloaded = _ffmpeg_grab_to_mp4(video_url, target_mp4)

        if not downloaded or not downloaded.exists():
            raise HTTPException(status_code=400, detail="视频下载失败：请检查链接有效性或后端 ffmpeg/yt-dlp 安装")

        # ⭐ 新增：把服务器文件路径转换为前端可直接访问的 URL
        public_video_url = f"/uploads/{downloaded.name}"  # NEW

        # 若 news_text 为空，尝试使用自动字幕
        if not news_text.strip():
            # 以 downloads 目录/同级目录找字幕
            auto_txt = _maybe_load_auto_subtitle_text(downloaded.parent)
            if auto_txt:
                news_text = auto_txt

        # 设备设置（与 /api/process 同步）
        if device.lower() == "cpu":
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
        else:
            os.environ['CUDA_VISIBLE_DEVICES'] = str(device)
            os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

        # 特征提取（与你的 Process(...) 一致）
        audio_emo_cls, topk_labels = Process(str(downloaded), news_text, list(news_text))

        # 推理（与你的 Run(...).main() 一致）
        config = {
            'dataset': 'fakejm',
            'mode': 'inference_test',
            'epoches': 1,
            'batch_size': int(batch_size),
            'early_stop': 5,
            'device': str(device),
            'seed': 2025,
            'lr': 0.001,
            'alpha': 0,
            'beta': 255,
            'inference_ckp': str(inference_ckp),
            'path_ckp': './checkpoints/',
            'path_tb': './tensorboard/'
        }
        Run(config=config).main()

        # 读取预测 CSV（与你当前实现一致）
        if not DEFAULT_CSV_PATH.exists():
            raise HTTPException(status_code=500, detail=f"预测CSV不存在: {DEFAULT_CSV_PATH}")
        df = pd.read_csv(DEFAULT_CSV_PATH, engine='python', sep=None)
        if df.empty:
            raise HTTPException(status_code=500, detail="预测CSV为空")

        row = df.tail(1).iloc[0]
        vid = int(row.get('vid')) if 'vid' in row else None
        label = int(row.get('label')) if 'label' in row else None
        pred = int(row.get('pred')) if 'pred' in row else None
        pred_prob = float(row.get('pred_prob')) if 'pred_prob' in row else None
        fake_or_real = '假' if (pred == 1) else ('真' if pred is not None else None)

        # 导出 CSV 到 outputs/ts 以供前端下载（与你现有一致）
        run_dir = OUTPUTS_DIR / str(ts)
        csv_public_url = _copy_csv_to_run_folder(DEFAULT_CSV_PATH, run_dir)

        return JSONResponse({
            "ts": ts,
            "video_path": str(downloaded),
            "video_url": public_video_url,
            "text_topk_labels": topk_labels,
            "audio_emo_cls": audio_emo_cls,
            "classification": {
                "vid": vid,
                "label": label,
                "pred": pred,
                "pred_prob": pred_prob,
                "readable": fake_or_real,
            },
            "downloads": {
                "predictions_csv": csv_public_url or str(DEFAULT_CSV_PATH)
            },
            "fromUrl": True
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("在线视频处理失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/import_url")
async def api_import_url(video_url: str = Form(...)):
    try:
        ts = int(time())
        target_mp4 = UPLOADS_DIR / f"{ts}_online.mp4"

        if _is_youtube(video_url):
            downloaded = _ytdlp_download_video_to_mp4(video_url, target_mp4)
        else:
            downloaded = _ffmpeg_grab_to_mp4(video_url, target_mp4)

        if not downloaded or not downloaded.exists():
            raise HTTPException(status_code=400, detail="视频下载失败")

        public_video_url = f"/uploads/{downloaded.name}"
        return JSONResponse({"ts": ts, "video_url": public_video_url})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5020)),
        reload=True,
    )

