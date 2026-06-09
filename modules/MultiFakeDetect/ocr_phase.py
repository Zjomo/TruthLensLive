import json
import subprocess
from pathlib import Path
from typing import List, Literal, Tuple
import re, unicodedata
import os

import torch
import torch.nn as nn
from transformers import BertTokenizerFast, BertModel
import pytesseract
from PIL import Image
from unidecode import unidecode


def run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def extract_keyframes(
        input_mp4: str,
        out_dir: str = "keyframes",
        prefix: str = "kf_",
        ext: str = "jpg"
) -> List[Path]:
    """
    基于 ffmpeg 导出关键帧图片，返回关键帧图片的路径列表（按时间排序）
    """
    input_mp4 = str(Path(input_mp4).resolve())
    out_dir_p = Path(out_dir).resolve()
    ensure_dir(out_dir_p)

    # 1) 导出 I 帧
    # 用 PTS 命名，便于后续对齐时间
    out_pattern = str(out_dir_p / f"{prefix}%010d.{ext}")
    cmd = [
        "ffmpeg", "-y",
        "-i", input_mp4,
        "-vf", "select=eq(pict_type\\,I)",
        "-vsync", "vfr",
        "-frame_pts", "1",
        out_pattern
    ]
    run(cmd)

    # 2) 读取关键帧时间戳（秒）
    # 过滤出 key_frame=1 的帧，并取 best_effort_timestamp_time
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_frames",
        "-show_entries", "frame=key_frame,pict_type,best_effort_timestamp_time,pkt_pts_time",
        "-of", "json",
        input_mp4
    ]
    ff = run(probe_cmd)
    info = json.loads(ff.stdout)

    key_times = []
    for fr in info.get("frames", []):
        if int(fr.get("key_frame", 0)) == 1 and fr.get("pict_type") == "I":
            # 优先 best_effort_timestamp_time
            t = fr.get("best_effort_timestamp_time")
            if t is None:
                t = fr.get("pkt_pts_time")
            if t is not None:
                try:
                    key_times.append(float(t))
                except:
                    pass

    # 3) 根据导出的文件名（PTS）构造路径列表并按时间排序
    imgs = list(out_dir_p.glob(f"{prefix}*.{ext}"))

    # 文件名形如 kf_0000001234.jpg（数字是 PTS）
    def pts_from_name(p: Path) -> int:
        stem = p.stem  # kf_0000001234
        num = "".join(ch for ch in stem if ch.isdigit())
        return int(num) if num else 0

    imgs_sorted = sorted(imgs, key=pts_from_name)

    return imgs_sorted


# 提取图像中的文本
def ocr_extract(image_path):
    # 使用PIL打开图像
    img = Image.open(image_path)
    # 使用Tesseract OCR提取文本
    # result = pytesseract.image_to_string(img, lang='chi_sim')
    result = pytesseract.image_to_string(img, lang='eng')

    return result


class OCRBERTFeaturizer:
    def __init__(
        self,
        model_name: str = "bert-base-chinese",  # 或 "bert-base-multilingual-cased"
        max_length: int = 512,
        stride: int = 64,
        use_cls: bool = False,
        remove_punct: bool = False,
        output_dim: int = 512,
        proj_trainable: bool = False
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = BertTokenizerFast.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        self.model.to(self.device).eval()
        self.max_length = max_length
        self.stride = stride
        self.use_cls = use_cls
        self.remove_punct = remove_punct

        # 正则和替换表
        self._re_ctrl = re.compile(r"[\u0000-\u0008\u000B-\u000C\u000E-\u001F]")
        self._re_spaces = re.compile(r"\s+")
        self._table = str.maketrans({
            "’": "'", "‘": "'", "“": '"', "”": '"', "—": "-",
            "–": "-", "￥": "¥", "，": ",", "。": ".", "：": ":",
            "；": ";", "！": "!", "？": "?", "（": "(", "）": ")",
            "【": "[", "】": "]", "《": "<", "》": ">", "、": "/",
        })

        # 投影层 (H -> output_dim)
        hidden_size = self.model.config.hidden_size
        self.output_dim = output_dim
        self.proj = None
        if self.output_dim != hidden_size:
            self.proj = nn.Linear(hidden_size, self.output_dim, bias=False)
            nn.init.orthogonal_(self.proj.weight)
            self.proj.to(self.device)
            for p in self.proj.parameters():
                p.requires_grad = proj_trainable

        # 分类头 (output_dim -> 2)
        self.classifier = nn.Linear(self.output_dim, 2, bias=True)
        nn.init.xavier_uniform_(self.classifier.weight)
        self.classifier.to(self.device)
        for p in self.classifier.parameters():
            p.requires_grad = proj_trainable  # 如果不训练，设为False

    def _to_halfwidth(self, s: str) -> str:
        return "".join(
            chr(ord(ch) - 0xFEE0) if 0xFF01 <= ord(ch) <= 0xFF5E else
            (" " if ord(ch) == 0x3000 else ch)
            for ch in s
        )

    def clean_ocr_text(self, s: str) -> str:
        if not s:
            return ""
        s = unicodedata.normalize("NFKC", s)
        s = self._to_halfwidth(s).translate(self._table)
        s = self._re_ctrl.sub("", s)
        s = s.replace("\r", "")
        s = re.sub(r"[ \t]*\n[ \t]*", "\n", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        if self.remove_punct:
            s = re.sub(r"[^\w\u4e00-\u9fa5\s]", " ", s)
        s = self._re_spaces.sub(" ", s).strip()
        return s

    @torch.no_grad()
    def _encode_chunk(self, texts: List[str]) -> torch.Tensor:
        enc = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}
        out = self.model(**enc)
        if self.use_cls:
            feats = out.last_hidden_state[:, 0]
        else:
            last_hidden = out.last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1)
            sum_hidden = (last_hidden * mask).sum(dim=1)
            lengths = mask.sum(dim=1).clamp(min=1)
            feats = sum_hidden / lengths
        return feats

    def _split_long(self, text: str) -> List[str]:
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        if len(tokens) <= self.max_length - 2:
            return [text]
        chunks, start = [], 0
        max_body = self.max_length - 2
        while start < len(tokens):
            end = min(start + max_body, len(tokens))
            piece = self.tokenizer.decode(tokens[start:end])
            chunks.append(piece)
            if end == len(tokens):
                break
            start = end - self.stride
            if start < 0:
                start = 0
        return chunks

    @torch.no_grad()
    def encode_texts(
        self,
        texts: List[str],
        batch_size: int = 16,
        aggregate_long: Literal["mean", "cls"] = "mean"
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        expanded_texts, owners = [], []
        for i, t in enumerate(texts):
            ct = self.clean_ocr_text(t)
            parts = self._split_long(ct)
            for p in parts:
                expanded_texts.append(p)
                owners.append(i)

        feats_list = []
        for i in range(0, len(expanded_texts), batch_size):
            batch = expanded_texts[i:i+batch_size]
            feats = self._encode_chunk(batch)
            feats_list.append(feats.cpu())
        if not feats_list:
            return torch.empty((0, self.output_dim)), torch.empty((0, 2))

        feats_all = torch.cat(feats_list, dim=0)
        dim_h = feats_all.shape[1]
        sums = [torch.zeros(dim_h) for _ in range(len(texts))]
        counts = [0 for _ in range(len(texts))]
        for vec, owner in zip(feats_all, owners):
            sums[owner] += vec
            counts[owner] += 1

        pooled = []
        for i in range(len(texts)):
            if counts[i] == 0:
                pooled.append(torch.zeros(dim_h))
            else:
                pooled.append(sums[i] / counts[i])
        embs = torch.stack(pooled, dim=0)

        embs = torch.nn.functional.normalize(embs, p=2, dim=1)

        if self.proj is not None:
            self.proj.eval() if not any(p.requires_grad for p in self.proj.parameters()) else None
            embs = self.proj(embs.to(self.device)).detach().cpu()

        embs = torch.nn.functional.normalize(embs, p=2, dim=1)

        # 分类头输出 (N, 2)
        logits = self.classifier(embs.to(self.device)).detach().cpu()

        return embs, logits  # 返回 (N, 512) 和 (N, 2)









