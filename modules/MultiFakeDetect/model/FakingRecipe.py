import json
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from .attention import *


# 文本情绪+音频情绪+视觉特征+文本语义特征 -- 基于Transformer+MLP 的多模态融合的虚假新闻检测
class MSAM(torch.nn.Module):
    def __init__(self, dataset):
        super(MSAM, self).__init__()
        # 设置fakett 和 fakesv的文本情感 语义维度
        if dataset == 'fakett':
            self.encoded_text_semantic_fea_dim = 512
        elif dataset == 'fakesv':
            self.encoded_text_semantic_fea_dim = 768
        elif dataset == 'fakejm':
            self.encoded_text_semantic_fea_dim = 768

        # 设置视觉框数
        self.input_visual_frames = 83

        # 配置MLP 提取情绪特征（文本）
        self.mlp_text_emo = nn.Sequential(
            nn.Linear(768, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
        )

        # 配置MLP 提取文本语义特征
        self.mlp_text_semantic = nn.Sequential(
            nn.Linear(self.encoded_text_semantic_fea_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
        )

        # 配置MLP 提取视觉特征
        self.mlp_img = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
        )

        # === 关键修复：保持 ckpt 的 768->128，但为 512 维音频提供投影到 768 ===
        self.audio_proj_512_to_768 = nn.Linear(512, 768)
        self.mlp_audio = nn.Sequential(
            nn.Linear(768, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
        )

        # 配置交叉注意力
        self.co_attention_tv = co_attention(
            d_k=128,
            d_v=128,
            n_heads=4,
            dropout=0.1,
            d_model=128,
            visual_len=self.input_visual_frames,
            sen_len=512,
            fea_v=128,
            fea_s=128,
            pos=False,
        )

        # 配置Transformer 提取情绪特征
        self.trm_emo = nn.TransformerEncoderLayer(
            d_model=128, nhead=2, batch_first=True
        )

        # 配置Transformer 提取语义特征
        self.trm_semantic = nn.TransformerEncoderLayer(
            d_model=128, nhead=2, batch_first=True
        )

        # 配置全连接层，实现二分类
        self.content_classifier = nn.Sequential(
            nn.Linear(128 * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 2),
        )

    # 启动
    def forward(self, **kwargs):
        device = next(self.parameters()).device

        # 数据导入
        all_phrase_semantic_fea = kwargs['all_phrase_semantic_fea']
        all_phrase_emo_fea = kwargs['all_phrase_emo_fea']
        raw_visual_frames = kwargs['raw_visual_frames']
        raw_audio_emo = kwargs['raw_audio_emo']

        # ---- 1、文本情感特征（统一到 [B,1,128]）----
        text = self.mlp_text_emo(all_phrase_emo_fea)
        if text.dim() == 2:           # [B,D] -> [B,1,D]
            text = text.unsqueeze(1)
        elif text.dim() == 4:         # [B,1,1,D] -> [B,1,D]
            text = text.squeeze(2)
        raw_t_fea_emo = text

        # ---- 2、音频情感特征（统一到 [B,L,128]）----
        audio = raw_audio_emo
        if audio.dim() == 2:          # [L,F] -> [1,L,F]
            audio = audio.unsqueeze(0)
        # 适配 512/768 两种输入维
        if audio.size(-1) == 512:
            audio = self.audio_proj_512_to_768(audio.to(device))
        elif audio.size(-1) == 768:
            audio = audio.to(device)
        else:
            raise RuntimeError(f"Unexpected audio feature dim: {audio.size(-1)}; expected 512 or 768")
        raw_a_fea_emo = self.mlp_audio(audio)  # [B,L,128]

        # ---- 3、融合 ----
        fusion_emo_fea = self.trm_emo(torch.cat((raw_t_fea_emo, raw_a_fea_emo), dim=1))
        fusion_emo_fea = torch.mean(fusion_emo_fea, dim=1)  # [B,128]

        # 基于联合注意力机制（基于文本+视觉特征，以及对应的序列长度），
        # 再进行池化操作（两种特征分别求平均 -- 从上往下 -- 维度0）
        # 进行特征融合后，基于transformer进一步提取语义特征，并进行池化
        # 提取得到，文本语义+视觉特征
        raw_t_fea_semantic = self.mlp_text_semantic(all_phrase_semantic_fea)
        raw_v_fea = self.mlp_img(raw_visual_frames)
        content_v, content_t = self.co_attention_tv(
            v=raw_v_fea,
            s=raw_t_fea_semantic,
            v_len=raw_v_fea.shape[1],
            s_len=raw_t_fea_semantic.shape[1],
        )
        content_v = torch.mean(content_v, -2)
        content_t = torch.mean(content_t, -2)
        fusion_semantic_fea = self.trm_semantic(
            torch.cat((content_t.unsqueeze(1), content_v.unsqueeze(1)), 1)
        )
        fusion_semantic_fea = torch.mean(fusion_semantic_fea, 1)

        # 将文本+音频情绪特征 结合 文本语义+视觉特征，进行融合
        # 基于一个全连接层，实现二分类
        msam_fea = torch.cat((fusion_emo_fea, fusion_semantic_fea), 1)
        output_msam = self.content_classifier(msam_fea)
        return output_msam


# 2D层归一化
class LayerNorm2d(nn.Module):
    def __init__(self, num_channels: int, eps: float = 1e-6) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(num_channels))  # 动态缩放因子
        self.bias = nn.Parameter(torch.zeros(num_channels))   # 动态偏置
        self.eps = eps                                        # 最小常数

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        u = x.mean(1, keepdim=True)                           # 各通道均值
        s = (x - u).pow(2).mean(1, keepdim=True)              # 各通道方差
        x = (x - u) / torch.sqrt(s + self.eps)                # std 归一化处理
        x = self.weight[:, None, None] * x + self.bias[:, None, None]
        return x


# 设计位置编码，保留输入序列顺序，并与输入序列进行融合（相加）
class PosEncoding_fix(nn.Module):
    # 基于序列维度，定位置编码 的放缩因子(权重)--定整体基调 ，低维度变化慢，高维度变化快
    def __init__(self, d_word_vec):
        super(PosEncoding_fix, self).__init__()
        self.d_word_vec = d_word_vec
        # 使用 register_buffer，随模型移动设备
        w_k = torch.tensor([1.0 / (np.power(10000.0, 2 * (i // 2) / d_word_vec)) for i in range(d_word_vec)],
                           dtype=torch.float32)
        self.register_buffer('w_k', w_k)

    def forward(self, inputs: torch.Tensor):
        # inputs: [L]，按与模型相同设备/精度处理
        pos = inputs.to(dtype=torch.float32, device=self.w_k.device)
        # 外积得到 [L, D] 的基
        base = torch.outer(pos, self.w_k)  # [L, D]
        pos_embs = torch.zeros_like(base)
        pos_embs[:, 0::2] = torch.sin(base[:, 0::2])
        pos_embs[:, 1::2] = torch.cos(base[:, 1::2])
        # 对 pos==0 的位置强制置零（保持你的原逻辑）
        if (inputs == 0).any():
            pos_embs[inputs == 0] = 0
        return pos_embs


# 时间戳编码器 -- 提取时间中：动画图层绝对持续时间、动画图层相对持续时间、动态文本绝对持续时间、动态文本相对持续时间
class DurationEncoding(nn.Module):
    def __init__(self, dim, dataset):
        super(DurationEncoding, self).__init__()
        if dataset == 'fakett':
            # './fea/fakett/fakett_segment_duration.json' record the duration of each clip(segment) for each video
            with open('G:/MyDataset/Graduate/FakingRecipe/fea/fakett/fakett_segment_duration.json', 'r') as json_file:
                seg_dura_info = json.load(json_file)
        elif dataset == 'fakesv':
            # './fea/fakesv/fakesv_segment_duration.json' record the duration of each clip(segment) for each video
            with open('G:/MyDataset/Graduate/FakingRecipe/fea/fakesv/fakesv_segment_duration.json', 'r') as json_file:
                seg_dura_info = json.load(json_file)
        elif dataset == 'fakejm':
            # 修复：fakejm 的路径应为 fakejm_segment_duration.json
            with open('G:/MyDataset/Graduate/FakingRecipe/fea/fakejm/fakesv_segment_duration.json', 'r') as json_file:
                seg_dura_info = json.load(json_file)

        # 各片段持续时间 -- 绝对持续时间【具体时间】
        self.all_seg_duration = seg_dura_info['all_seg_duration']

        # 各片段持续时间，占总时长的比例 -- 相对持续时间【相对比例】
        self.all_seg_dura_ratio = seg_dura_info['all_seg_dura_ratio']

        # === 关键修复：使用 linspace & E+1 个桶 ===
        # 绝对时间：E_abs = 101 边界 => 102 个桶
        abs_edges = torch.quantile(
            torch.tensor(self.all_seg_duration, dtype=torch.float64),
            torch.linspace(0, 1, steps=101, dtype=torch.float64),
        )
        # 相对时间：E_rel = 51 边界 => 52 个桶
        rel_edges = torch.quantile(
            torch.tensor(self.all_seg_dura_ratio, dtype=torch.float64),
            torch.linspace(0, 1, steps=51, dtype=torch.float64),
        )
        self.register_buffer('absolute_bin_edges', abs_edges)
        self.register_buffer('relative_bin_edges', rel_edges)
        self.ab_duration_embed = nn.Embedding(abs_edges.numel() + 1, dim)  # 102
        self.re_duration_embed = nn.Embedding(rel_edges.numel() + 1, dim)  # 52

        # OCR 部分
        self.ocr_all_seg_duration = seg_dura_info['ocr_all_seg_duration']
        self.ocr_all_seg_dura_ratio = seg_dura_info['ocr_all_seg_dura_ratio']
        ocr_abs_edges = torch.quantile(
            torch.tensor(self.ocr_all_seg_duration, dtype=torch.float64),
            torch.linspace(0, 1, steps=101, dtype=torch.float64),
        )
        ocr_rel_edges = torch.quantile(
            torch.tensor(self.ocr_all_seg_dura_ratio, dtype=torch.float64),
            torch.linspace(0, 1, steps=51, dtype=torch.float64),
        )
        self.register_buffer('ocr_absolute_bin_edges', ocr_abs_edges)
        self.register_buffer('ocr_relative_bin_edges', ocr_rel_edges)
        self.ocr_ab_duration_embed = nn.Embedding(ocr_abs_edges.numel() + 1, dim)  # 102
        self.ocr_re_duration_embed = nn.Embedding(ocr_rel_edges.numel() + 1, dim)  # 52

        self.result_dim = dim

    def _embed_by_edges(self, values, edges, emb):
        # values: 1D/2D/列表，输出 [N, dim]
        vals = torch.as_tensor(values, dtype=torch.float64, device=edges.device)
        idx = torch.searchsorted(edges, vals)                           # [0..E]
        idx = idx.to(dtype=torch.long, device=emb.weight.device)
        # 保险措施
        idx = torch.clamp(idx, 0, emb.num_embeddings - 1)
        return emb(idx)

    def forward(self, time_value, attribute):
        if attribute == 'natural_ab':
            return self._embed_by_edges(time_value, self.absolute_bin_edges, self.ab_duration_embed)
        elif attribute == 'natural_re':
            return self._embed_by_edges(time_value, self.relative_bin_edges, self.re_duration_embed)
        elif attribute == 'ocr_ab':
            return self._embed_by_edges(time_value, self.ocr_absolute_bin_edges, self.ocr_ab_duration_embed)
        elif attribute == 'ocr_re':
            return self._embed_by_edges(time_value, self.ocr_relative_bin_edges, self.ocr_re_duration_embed)
        # 没有匹配：返回 0 向量（与设备对齐）
        return torch.zeros((1, self.result_dim), device=self.ab_duration_embed.weight.device)


# 输入：起始时间戳、视频fps、视频总帧数
# 输出：各片段持续时长、各片段持续时间比例
# 注：返回 CPU 张量，设备迁移在 DurationEncoding 内部处理
def get_dura_info_visual(segs, fps, total_frame):
    duration_frames = []
    duration_time = []
    for seg in segs:
        if seg[0] == -1 and seg[1] == -1:
            continue
        if seg[0] == 0 and seg[1] == 0:
            continue
        else:
            duration_frames.append(seg[1] - seg[0] + 1)
            duration_time.append((seg[1] - seg[0] + 1) / fps)
    duration_ratio = [min(dura / total_frame, 1) for dura in duration_frames]
    return torch.tensor(duration_time, dtype=torch.float64), torch.tensor(duration_ratio, dtype=torch.float64)


class MEAM(torch.nn.Module):
    def __init__(self, dataset):
        super(MEAM, self).__init__()
        self.input_visual_frames = 83     # 输入视觉的帧数
        self.pad_seg_count = 83           # 填充片段的数量
        self.pad_ocr_phrase_count = 80    # 填充ocr短语的数量

        # 提取ocr 图片特征
        # 预处理的./preprocess_ocr/sam/*.pkl 维度均为(256,64,64),所以卷积的输入维度为 256
        self.ocr_pattern_fea_downscaling = nn.Sequential(
            nn.Conv2d(256, 256 // 4, kernel_size=3, stride=2, padding=1),         # 卷积提特征图，输入256，输出64
            LayerNorm2d(256 // 4),                                                # 2D归一化，输入64，输出64
            nn.GELU(),                                                            # 激活函数，引入非线性，方便学习更复杂的特征
            nn.Conv2d(256 // 4, 256 // 16, kernel_size=3, stride=2, padding=1),   # 卷积提取特征图，输入64，输出16
            nn.GELU(),                                                            # 激活函数，归一化后一般特征被线性化，为学习更复杂的特征，所以引入GELU
        )

        # 配置MLP 对特征进行变换+抽象
        self.mlp_ocr_pattern = nn.Sequential(
            nn.Linear(4096, 2048),                  # 线性层，输入4096，输出2048（修正注释）
            nn.ReLU(),                              # 激活函数，引入非线性
            nn.Dropout(0.1),                        # dropout，随机丢弃 10%的神经元
            nn.Linear(2048, 512),                   # 线性映射，输入2048，输出512
            nn.ReLU(),                              # 后续同理
            nn.Dropout(0.1),
            nn.Linear(512, 128),
            nn.ReLU(),
        )

        # ocr语义特征图降维
        self.proj_t = nn.Linear(512, 128)

        # 基于多头注意力机制 提取全局依赖特征：时间戳特征
        self.t_interseg_attention = Attention(128, heads=4, dim_head=64)

        # 视觉特征图降维
        self.proj_v = nn.Linear(512, 128)

        # 提取视觉特征的片段内特征
        self.intraseg_att_v = Attention(dim=128, heads=4)

        # 提取视觉特征的片段间特征
        self.v_interseg_attention = Attention(dim=128, heads=4)

        # 构建绝对位置编码
        self.position_encoder = PosEncoding_fix(128)

        # 提取绝对/项目文本持续时间特征 + 绝对/项目动画持续时间特征
        self.dura_encoder = DurationEncoding(64, dataset)

        # transformer提取 多模态特征
        self.narative_interact_trm = nn.TransformerEncoderLayer(d_model=128, nhead=2, batch_first=True)

        # 基于MLP，实现二分类，输入：空间编辑特征+时间编辑特征，输出：分类结果
        self.narative_classifier = nn.Sequential(
            nn.Linear(128 * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 2),
        )

    # 提取一个视频的片段内特征
    def segment_feature_aggregation_att(self, frame_fea, frames_seg_indicator):
        seg_counts = torch.bincount(frames_seg_indicator[frames_seg_indicator != -1])       # 计算片段帧数
        max_frames = torch.max(seg_counts).item()                                           # 提取最大帧数
        unique_segments = torch.unique(frames_seg_indicator[frames_seg_indicator != -1])    # 片段标识去重

        # 对每个片段，进行帧数填充
        padded_seg_frames = []
        for idx, seg_id in enumerate(unique_segments):
            frames = frame_fea[frames_seg_indicator == seg_id]
            pad_amount = max_frames - frames.size(0)
            if pad_amount > 0:
                frames = F.pad(frames, (0, 0, 0, pad_amount), 'constant', 0)
            padded_seg_frames.append(frames)

        # 堆叠所有片段特征，并基于片段内注意力机制，提取全局的依赖特征，最终进行平均池化
        padded_seg_frames = torch.stack(padded_seg_frames).to(frame_fea.device)
        aggregated_seg_fea = self.intraseg_att_v(padded_seg_frames)
        return torch.mean(aggregated_seg_fea, 1)

    def forward(self, **kwargs):
        device = next(self.parameters()).device

        # 导入数据
        ocr_phrases_fea = kwargs['ocr_phrase_fea']
        ocr_time_region = kwargs['ocr_time_region']
        visual_frames_fea = kwargs['visual_frames_fea']
        visual_frames_seg_indicator = kwargs['visual_frames_seg_indicator']
        visual_seg_paded = kwargs['visual_seg_paded']
        fps = kwargs['fps']
        total_frames = kwargs['total_frame']
        ocr_pattern_fea = kwargs['ocr_pattern_fea']

        # 提取OCR 动画图层特征
        down_scaling_ocr_pattern_fea = self.ocr_pattern_fea_downscaling(ocr_pattern_fea)
        flatten_ocr_pattern_fea = down_scaling_ocr_pattern_fea.view(down_scaling_ocr_pattern_fea.size(0), -1)
        ocr_layout_pattern = self.mlp_ocr_pattern(flatten_ocr_pattern_fea)

        # 提取 视觉帧特征
        v_temporal = []
        narrative_v_fea = self.proj_v(visual_frames_fea)

        # 聚合各视频帧片段特征
        for v_idx in range(len(narrative_v_fea)):
            v_seg_fea = self.segment_feature_aggregation_att(narrative_v_fea[v_idx], visual_frames_seg_indicator[v_idx])
            v_ab_value, v_re_value = get_dura_info_visual(visual_seg_paded[v_idx], fps[v_idx], total_frames[v_idx])
            v_ab_emb = self.dura_encoder(v_ab_value, 'natural_ab')
            v_re_emb = self.dura_encoder(v_re_value, 'natural_re')
            dura_emd = torch.cat([v_ab_emb, v_re_emb], dim=1)
            seg_general_fea = v_seg_fea + dura_emd

            # 为每个片段添加位置编码
            seg_index = torch.arange(v_seg_fea.shape[0], device=device)
            seg_position_embedding = self.position_encoder(seg_index)
            seg_general_fea = seg_general_fea + seg_position_embedding  # 修复：基于已融合特征再加位置编码

            # 填充片段维度，至统一长度
            if seg_general_fea.shape[0] < self.pad_seg_count:
                pad_seg = torch.zeros((self.pad_seg_count - seg_general_fea.shape[0], 128), device=device)
                seg_general_fea = torch.cat([seg_general_fea, pad_seg], dim=0)
            v_temporal.append(seg_general_fea)

        # 堆叠所有片段特征
        v_temporal = torch.stack(v_temporal, dim=0)

        # 处理OCR 短语特征
        t_temporal = []
        for v_idx in range(len(ocr_phrases_fea)):
            ocr_phrase_fea = self.proj_t(ocr_phrases_fea[v_idx])
            ocr_ab_value, ocr_re_value = get_dura_info_visual(ocr_time_region[v_idx], fps[v_idx], total_frames[v_idx])
            ocr_ab_emb = self.dura_encoder(ocr_ab_value, 'ocr_ab')
            ocr_re_emb = self.dura_encoder(ocr_re_value, 'ocr_re')
            ocr_dura_emb = torch.cat([ocr_ab_emb, ocr_re_emb], dim=1)
            ocr_phrase_fea = ocr_phrase_fea[: ocr_dura_emb.shape[0]]
            ocr_word_fea = ocr_phrase_fea + ocr_dura_emb

            # 填充位置编码
            phrase_index = torch.arange(ocr_re_emb.shape[0], device=device)
            phrase_position_embedding = self.position_encoder(phrase_index)
            ocr_word_fea = ocr_word_fea + phrase_position_embedding

            # 填充ocr短语 至统一长度
            if ocr_word_fea.shape[0] < self.pad_ocr_phrase_count:
                pad_phrase = torch.zeros((self.pad_ocr_phrase_count - ocr_word_fea.shape[0], 128), device=device)
                ocr_word_fea = torch.cat((ocr_word_fea, pad_phrase), dim=0)
            t_temporal.append(ocr_word_fea)

        # 堆叠OCR短语特征
        t_temporal = torch.stack(t_temporal, dim=0)

        # 跨片段注意力计算（文本）
        narative_t = self.t_interseg_attention(t_temporal)
        ocr_seg_count = torch.tensor([len(ocr_time_region[i]) for i in range(len(ocr_time_region))], device=device)
        narative_t = torch.sum(narative_t, dim=1) / ocr_seg_count.unsqueeze(1)

        # 跨片段注意力计算（视觉）
        narrative_v = self.v_interseg_attention(v_temporal)
        v_seg_count = torch.tensor([len(visual_seg_paded[i]) for i in range(len(visual_seg_paded))], device=device)
        narrative_v = torch.sum(narrative_v, dim=1) / v_seg_count.unsqueeze(1)

        # OCR + 视觉多模态 特征融合
        narrative_multimodal_segs_fea = torch.cat((narative_t.unsqueeze(1), narrative_v.unsqueeze(1)), 1)
        narrative_multimodal_segs_fea = self.narative_interact_trm(narrative_multimodal_segs_fea)
        narrative_temporal_fea = torch.mean(narrative_multimodal_segs_fea, dim=1)

        # 最终实现二分类
        meam_fea = torch.cat((ocr_layout_pattern, narrative_temporal_fea), 1)
        output_meam = self.narative_classifier(meam_fea)
        return output_meam


# MSAM -- 多模态特征编码器
# MEAM -- 视频制作特征编码器
class FakingRecipe_Model(torch.nn.Module):
    def __init__(self, dataset):
        super(FakingRecipe_Model, self).__init__()
        self.content_branch = MSAM(dataset=dataset)
        self.editing_branch = MEAM(dataset=dataset)
        self.tanh = nn.Tanh()

    def forward(self, **kwargs):
        output_msam = self.content_branch(**kwargs)
        output_meam = self.editing_branch(**kwargs)
        output = output_msam * self.tanh(output_meam)
        return output, output_msam, output_meam
