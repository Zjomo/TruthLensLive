import torch.nn.functional as F
import torch.nn as nn
import json
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

        # 配置MLP 提取情绪特征
        self.mlp_text_emo = nn.Sequential(
          nn.Linear(768, 128),
          nn.ReLU(),
          nn.Dropout(0.1))

        # 配置MLP 提取文本语义特征
        self.mlp_text_semantic = nn.Sequential(
          nn.Linear(self.encoded_text_semantic_fea_dim,128),
          nn.ReLU(),
          nn.Dropout(0.1))

        # 配置MLP 提取视觉特征
        self.mlp_img = nn.Sequential(
          nn.Linear(512, 128),
          nn.ReLU(),
          nn.Dropout(0.1))

        # 配置MLP 提取音频特征
        self.mlp_audio = nn.Sequential(
          #torch.nn.Linear(512, 128),
          torch.nn.Linear(768, 128),
          
          torch.nn.ReLU(),
          nn.Dropout(0.1))

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
          pos=False)

        # 配置Transformer 提取情绪特征
        self.trm_emo = nn.TransformerEncoderLayer(
          d_model=128,
          nhead=2,
          batch_first=True)

        # 配置Transformer 提取语义特征
        self.trm_semantic = nn.TransformerEncoderLayer(
          d_model=128,
          nhead=2,
          batch_first=True)

        # 配置全连接层，实现二分类
        self.content_classifier = nn.Sequential(
          nn.Linear(128*2, 128),
          nn.ReLU(),
          nn.Dropout(0.1),
          nn.Linear(128, 2))

    # 启动
    def forward(self, **kwargs):
        # 数据导入
        all_phrase_semantic_fea = kwargs['all_phrase_semantic_fea']
        all_phrase_emo_fea = kwargs['all_phrase_emo_fea']
        raw_visual_frames = kwargs['raw_visual_frames']
        raw_audio_emo = kwargs['raw_audio_emo']

        # 基于transformers 进行特征拼接+融合，提取得到，文本+音频情绪特征
        # ---- 源代码 ----
        # raw_t_fea_emo = self.mlp_text_emo(all_phrase_emo_fea).unsqueeze(1)
        # raw_a_fea_emo = self.mlp_audio(raw_audio_emo).unsqueeze(1)

        # fusion_emo_fea = self.trm_emo(torch.cat((raw_t_fea_emo, raw_a_fea_emo), 1))
        # fusion_emo_fea = torch.mean(fusion_emo_fea, 1)

        # ---- 1、文本情感特征 ----
        text = self.mlp_text_emo(all_phrase_emo_fea)  # 期望 [B, (L_t=1), D]
        if text.dim() == 2:  # [B, D] -> [B, 1, D]
            text = text.unsqueeze(1)
        elif text.dim() == 4:  # [B, 1, 1, D] -> [B, 1, D]
            text = text.squeeze(2)
        raw_t_fea_emo = text

        # ---- 2、音频情感特征 ----
        audio = raw_audio_emo  # 现在类似 [L_a=144, F]
        if audio.dim() == 2:  # 没有 batch 维，认为是单样本序列 -> [1, L_a, F]
            audio = audio.unsqueeze(0)

        # 适配 512/768 两种输入维
        if audio.size(-1) == 512:
            audio = self.audio_proj_512_to_768(audio.to(device))
        elif audio.size(-1) == 768:
            audio = audio.to(device)
        else:
            raise RuntimeError(f"Unexpected audio feature dim: {audio.size(-1)}; expected 512 or 768")
        raw_a_fea_emo = self.mlp_audio(audio)  # [B,L,128]
        # (144,768) * (768,128) -> (144,128)

        # ---- 3、融合 ----
        print('raw_t_fea_emo形状为:')
        print(raw_t_fea_emo.shape)
        print('raw_a_fea_emo形状为:')
        print(raw_a_fea_emo.shape)

        fusion_emo_fea = self.trm_emo(torch.cat((raw_t_fea_emo, raw_a_fea_emo), dim=1))  # [1, 1+L_a, 128]
        fusion_emo_fea = torch.mean(fusion_emo_fea, dim=1)  # [1, 128]

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
          s_len=raw_t_fea_semantic.shape[1])
        content_v = torch.mean(content_v, -2)
        content_t = torch.mean(content_t, -2)
        fusion_semantic_fea = self.trm_semantic(torch.cat((content_t.unsqueeze(1), content_v.unsqueeze(1)), 1))
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
    def __init__(self,  d_word_vec):
        super(PosEncoding_fix, self).__init__()
        self.d_word_vec=d_word_vec
        self.w_k=np.array([1/(np.power(10000, 2*(i//2)/d_word_vec)) for i in range(d_word_vec)])

    # 初始化一个inputs变量，表示序列中每个变量的顺序，结合放缩因子 + sin + cos实现 [1,2,...] -> [pos1,pos2]
    # 1、输入维度
    # 2、放缩因子 -- 定基调
    # 3、sin/cos -- 周期性 -- 0到2Π，再到0，使得位置序号的含义，得以保留
    #            -- 相似性 -- sin/cos对应相近的位置，值差很小，差异小故具有相似性
    def forward(self, inputs):
        pos_embs = []
        for pos in inputs:
            pos_emb = torch.tensor([self.w_k[i]*pos.cpu() for i in range(self.d_word_vec)])
            if pos != 0:
                pos_emb[0::2] = np.sin(pos_emb[0::2])
                pos_emb[1::2] = np.cos(pos_emb[1::2])
                pos_embs.append(pos_emb)
            else:
                pos_embs.append(torch.zeros(self.d_word_vec))
        pos_embs = torch.stack(pos_embs)
        return pos_embs.cuda()


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
            # './fea/fakesv/fakesv_segment_duration.json' record the duration of each clip(segment) for each video
            with open('G:/MyDataset/Graduate/FakingRecipe/fea/fakejm/fakesv_segment_duration.json', 'r') as json_file:
                seg_dura_info = json.load(json_file)

        # 各片段持续时间 -- 绝对持续时间【具体时间】
        self.all_seg_duration = seg_dura_info['all_seg_duration']

        # 各片段持续时间，占总时长的比例 -- 相对持续时间【相对比例】
        self.all_seg_dura_ratio = seg_dura_info['all_seg_dura_ratio']

        # 量化，减少计算量，并为绝对/相对持续时间，构建嵌入层
        self.absolute_bin_edges = torch.quantile(
            torch.tensor(self.all_seg_duration).to(torch.float64),
            torch.linspace(0, 1, steps=101, dtype=torch.float64),
        ).cuda()

        self.relative_bin_edges = torch.quantile(
            torch.tensor(self.all_seg_dura_ratio).to(torch.float64),
            torch.range(0, 1, 0.02).to(torch.float64)
        ).cuda()

        self.ab_duration_embed = torch.nn.Embedding(101, dim)
        self.re_duration_embed = torch.nn.Embedding(51, dim)

        self.ocr_all_seg_duration = seg_dura_info['ocr_all_seg_duration']
        self.ocr_all_seg_dura_ratio = seg_dura_info['ocr_all_seg_dura_ratio']
        self.ocr_absolute_bin_edges = torch.quantile(torch.tensor(self.ocr_all_seg_duration).to(torch.float64),torch.range(0,1,0.01).to(torch.float64)).cuda()
        self.ocr_relative_bin_edges = torch.quantile(torch.tensor( self.ocr_all_seg_dura_ratio).to(torch.float64),torch.range(0,1,0.02).to(torch.float64)).cuda()

        # 嵌入层处理 绝对时间&相对时间 -- time2vev
        # 原理：
        # 将离散的时间值，基于时间边界，通过"量化区间"转换为"低维的嵌入向量" -- 分区
        # 这些嵌入向量帮助神经网络捕捉时间信息的潜在结构和规律，从而提高模型的表现和泛化能力
        # 在实际应用中，嵌入层不仅仅是一个简单的映射，它还通过训练过程优化嵌入向量，使其能够反映时间信息与其他任务目标之间的关联
        self.ocr_ab_duration_embed = torch.nn.Embedding(101, dim)
        self.ocr_re_duration_embed = torch.nn.Embedding(51, dim)
        self.result_dim = dim

    def forward(self, time_value, attribute):
        all_segs_embedding = []
        # 绝对时间编码类型 -- 动态文本曝光时间
        if attribute == 'natural_ab':
            for dv in time_value:
                bucket_indice=torch.searchsorted(self.absolute_bin_edges, torch.tensor(dv,dtype=torch.float64)) # 确定量化边界 -- 用于分区
                dura_embedding=self.ab_duration_embed(bucket_indice)                                            # 得到嵌入向量
                all_segs_embedding.append(dura_embedding)

        # 相对时间编码类型
        elif attribute=='natural_re':
            for dv in time_value:
                bucket_indice=torch.searchsorted(self.relative_bin_edges, torch.tensor(dv,dtype=torch.float64))
                dura_embedding=self.re_duration_embed(bucket_indice)
                all_segs_embedding.append(dura_embedding)

        # 绝对ocr 时间编码类型 -- 动画图层持续时间
        elif attribute=='ocr_ab':
            for dv in time_value:
                bucket_indice=torch.searchsorted(self.ocr_absolute_bin_edges, torch.tensor(dv,dtype=torch.float64))
                dura_embedding=self.ocr_ab_duration_embed(bucket_indice)
                all_segs_embedding.append(dura_embedding)

        # 相对ocr 时间编码类型
        elif attribute=='ocr_re':
            for dv in time_value:
                bucket_indice=torch.searchsorted(self.ocr_relative_bin_edges, torch.tensor(dv,dtype=torch.float64))
                dura_embedding=self.ocr_re_duration_embed(bucket_indice)
                all_segs_embedding.append(dura_embedding)

        # 若没有匹配的嵌入向量，则return 0向量
        # 若有匹配向量，则堆叠上述所有嵌入的时间向量
        if len(all_segs_embedding)==0:
            return torch.zeros((1,self.result_dim)).cuda()
        return torch.stack(all_segs_embedding,dim=0).cuda()


# 输入：起始时间戳、视频fps、视频总帧数
# 输出：各片段持续时长、各片段持续时间比例
def get_dura_info_visual(segs, fps, total_frame):
    duration_frames = []
    duration_time = []
    for seg in segs:
        if seg[0] == -1 and seg[1] == -1:
            continue
        if seg[0] == 0 and seg[1] == 0:
            continue
        else:
            duration_frames.append(seg[1]-seg[0]+1)
            duration_time.append((seg[1]-seg[0]+1)/fps)
    duration_ratio = [min(dura/total_frame, 1) for dura in duration_frames]
    return torch.tensor(duration_time).cuda(), torch.tensor(duration_ratio).cuda()


#
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
        self.mlp_ocr_pattern=nn.Sequential(
          nn.Linear(4096, 2048),                  # 线性层，输出4096，输出2048
          nn.ReLU(),                              # 激活函数，引入非线性
          nn.Dropout(0.1),                        # dropout，随机丢弃 10%的神经元
          nn.Linear(2048, 512),                   # 线性映射，输入2048，输出512
          nn.ReLU(),                              # 后续同理
          nn.Dropout(0.1),
          nn.Linear(512, 128),
          nn.ReLU())

        # ocr语义特征图降维
        self.proj_t = nn.Linear(512, 128)

        # 基于多头注意力机制 提取全局依赖特征：时间戳特征
        self.t_interseg_attention = Attention(128, heads=4, dim_head=64)

        # 视觉特征图降维
        self.proj_v = nn.Linear(512,128)

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
          nn.Linear(128*2, 128),
          nn.ReLU(),
          nn.Dropout(0.1),
          nn.Linear(128, 2))

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
                frames = F.pad(frames, (0, 0, 0, pad_amount), "constant", 0)
            padded_seg_frames.append(frames)

        # 堆叠所有片段特征，并基于片段内注意力机制，提取全局的依赖特征，最终进行平局池化
        padded_seg_frames = torch.stack(padded_seg_frames).cuda()
        aggregated_seg_fea = self.intraseg_att_v(padded_seg_frames)
        return torch.mean(aggregated_seg_fea, 1)

    def forward(self, **kwargs):
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
        v_temporal=[]
        narrative_v_fea=self.proj_v(visual_frames_fea)

        # 聚合各视频帧片段特征
        for v_idx in range(len(narrative_v_fea)):
            v_seg_fea = self.segment_feature_aggregation_att(narrative_v_fea[v_idx], visual_frames_seg_indicator[v_idx])
            v_ab_value, v_re_value = get_dura_info_visual(visual_seg_paded[v_idx], fps[v_idx], total_frames[v_idx])
            v_ab_emb = self.dura_encoder(v_ab_value, 'natural_ab')
            v_re_emb = self.dura_encoder(v_re_value, 'natural_re')
            dura_emd = torch.cat([v_ab_emb,v_re_emb], dim=1)
            seg_general_fea = v_seg_fea+dura_emd

            # 为每个片段添加位置编码
            seg_index = torch.tensor([i for i in range(v_seg_fea.shape[0])]).cuda()
            seg_position_embedding = self.position_encoder(seg_index)
            seg_general_fea = v_seg_fea+seg_position_embedding

            # 填充片段维度，至统一长度
            if seg_general_fea.shape[0]<self.pad_seg_count:
                pad_seg=torch.zeros((self.pad_seg_count-seg_general_fea.shape[0],128)).cuda()
                seg_general_fea=torch.cat([seg_general_fea,pad_seg],dim=0)
            v_temporal.append(seg_general_fea)

        # 堆叠所有片段特征
        v_temporal = torch.stack(v_temporal,dim=0)

        # 处理OCR 短语特征
        t_temporal = []
        for v_idx in range(len(ocr_phrases_fea)):
            ocr_phrase_fea = self.proj_t(ocr_phrases_fea[v_idx])
            ocr_ab_value, ocr_re_value = get_dura_info_visual(ocr_time_region[v_idx], fps[v_idx], total_frames[v_idx])
            ocr_ab_emb = self.dura_encoder(ocr_ab_value, 'ocr_ab')
            ocr_re_emb = self.dura_encoder(ocr_re_value, 'ocr_re')
            ocr_dura_emb = torch.cat([ocr_ab_emb,ocr_re_emb], dim=1)
            ocr_phrase_fea = ocr_phrase_fea[:ocr_dura_emb.shape[0]]
            ocr_word_fea = ocr_phrase_fea+ocr_dura_emb

            # 填充位置编码
            phrase_index = torch.tensor([i for i in range(ocr_re_emb.shape[0])]).cuda()
            phrase_position_embedding = self.position_encoder(phrase_index)
            ocr_word_fea = ocr_word_fea + phrase_position_embedding

            # 填充ocr短语 至统一长度
            if ocr_word_fea.shape[0] < self.pad_ocr_phrase_count:
                pad_phrase = torch.zeros((self.pad_ocr_phrase_count-ocr_word_fea.shape[0], 128)).cuda()
                ocr_word_fea = torch.cat((ocr_word_fea, pad_phrase), dim=0)
            t_temporal.append(ocr_word_fea)

        # 堆叠OCR短语特征
        t_temporal=torch.stack(t_temporal,dim=0)

        # 跨片段注意力计算
        narative_t = self.t_interseg_attention(t_temporal)
        ocr_seg_count = torch.tensor([len(ocr_time_region[i]) for i in range(len(ocr_time_region))]).cuda()
        narative_t = torch.sum(narative_t, dim=1)/ocr_seg_count.unsqueeze(1)

        # 视觉特征的跨片段注意力计算
        narrative_v = self.v_interseg_attention(v_temporal)
        v_seg_count = torch.tensor([len(visual_seg_paded[i]) for i in range(len(visual_seg_paded))]).cuda()
        narrative_v = torch.sum(narrative_v, dim=1)/v_seg_count.unsqueeze(1)

        # OCR + 视觉多模态 特征融合
        narrative_multimodal_segs_fea = torch.cat((narative_t.unsqueeze(1), narrative_v.unsqueeze(1)), 1)
        narrative_multimodal_segs_fea = self.narative_interact_trm(narrative_multimodal_segs_fea)
        narrative_temporal_fea = torch.mean(narrative_multimodal_segs_fea, dim=1)

        # 最终实现二分类
        meam_fea = torch.cat((ocr_layout_pattern, narrative_temporal_fea), 1)
        output_meam=self.narative_classifier(meam_fea)
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
        output = output_msam*self.tanh(output_meam)
        return output, output_msam, output_meam
