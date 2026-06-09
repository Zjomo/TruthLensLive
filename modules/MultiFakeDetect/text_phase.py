# 文本语义

from typing import List, Literal, Tuple
import re, unicodedata
from unidecode import unidecode
import torch
import torch.nn as nn
from transformers import BertTokenizerFast, BertModel


class BERTFeaturizer:
    def __init__(
        self,
        model_name: str = "bert-base-uncased",
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
        self.hidden_size = hidden_size
        self.proj = None
        if self.output_dim != hidden_size:
            self.proj = nn.Linear(hidden_size, self.output_dim, bias=False)
            nn.init.orthogonal_(self.proj.weight)
            self.proj.to(self.device)
            for p in self.proj.parameters():
                p.requires_grad = proj_trainable

        # 分类头 (output_dim -> 2) —— 可保留；与本次输出无关
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

    # 数据清洗：正则和替换表
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

    # ========= 新增：返回 (N, 512, 768) token级隐藏层 + (N, 512) 池化后投影 =========
    @torch.no_grad()
    def encode_tokens_and_pooled(
        self,
        texts: List[str],
        batch_size: int = 16
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        返回:
          token_hidden: (N, 512, 768)  — 直接的 token 级隐藏层（固定到 512 token）
          pooled_512:   (N, 512)      — mean pooling 后，线性投影到 512 维并 L2 归一化
        """
        # 预清洗
        cleaned = [self.clean_ocr_text(t) for t in texts]

        # 批量编码到固定 512 长度
        token_hiddens = []
        pooled_list = []

        for i in range(0, len(cleaned), batch_size):
            batch_texts = cleaned[i:i+batch_size]
            enc = self.tokenizer(
                batch_texts,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=512  # 硬对齐 512
            )
            enc = {k: v.to(self.device) for k, v in enc.items()}
            out = self.model(**enc)  # last_hidden_state: (B, 512, H)
            last_hidden = out.last_hidden_state  # (B, 512, 768)

            # 句向量 mean pooling -> (B, H)
            mask = enc["attention_mask"].unsqueeze(-1)  # (B, 512, 1)
            sum_hidden = (last_hidden * mask).sum(dim=1)  # (B, H)
            lengths = mask.sum(dim=1).clamp(min=1)       # (B, 1)
            sent_emb = sum_hidden / lengths              # (B, H)

            # 归一化 + 投影到 (B, 512)
            sent_emb = torch.nn.functional.normalize(sent_emb, p=2, dim=1)
            if self.proj is not None:
                self.proj.eval() if not any(p.requires_grad for p in self.proj.parameters()) else None
                sent_emb = self.proj(sent_emb)
            sent_emb = torch.nn.functional.normalize(sent_emb, p=2, dim=1)

            token_hiddens.append(last_hidden.detach().cpu())
            pooled_list.append(sent_emb.detach().cpu())

        token_hidden_all = torch.cat(token_hiddens, dim=0)  # (N, 512, 768)
        pooled_512_all = torch.cat(pooled_list, dim=0)      # (N, 512)
        return token_hidden_all, pooled_512_all
    # ========= 新增方法结束 =========

    @torch.no_grad()
    def encode_texts(
        self,
        texts: List[str],
        batch_size: int = 16,
        aggregate_long: Literal["mean", "cls"] = "mean"
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        原方法：分块-汇总得到 (N, output_dim) + (N, 2) + pooled(未投影的)(N, H)
        """
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
            return torch.empty((0, self.output_dim)), torch.empty((0, 2)), torch.empty((0, self.hidden_size))

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
        pooled = torch.stack(pooled, dim=0)  # (N, H)

        embs = torch.nn.functional.normalize(pooled, p=2, dim=1)

        if self.proj is not None:
            self.proj.eval() if not any(p.requires_grad for p in self.proj.parameters()) else None
            embs = self.proj(embs.to(self.device)).detach().cpu()

        embs = torch.nn.functional.normalize(embs, p=2, dim=1)

        # 分类头输出 (N, 2)
        logits = self.classifier(embs.to(self.device)).detach().cpu()

        return embs, logits, pooled  # (N, output_dim), (N,2), (N, H)