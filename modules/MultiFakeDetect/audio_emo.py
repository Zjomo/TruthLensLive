import os
import tempfile
import uuid
import numpy as np
import torch
import torch.nn.functional as F
import torchaudio
import cv2
import subprocess
import shutil
import tempfile
import uuid
import os
import torch.nn as nn

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def _require_ffmpeg():
    """检查系统是否能找到 ffmpeg 可执行文件。"""
    exe = shutil.which("ffmpeg")
    if exe is None:
        raise RuntimeError(
            "未找到 ffmpeg。请安装后确保其在 PATH 中（Windows 可用 choco 安装：choco install ffmpeg）。"
        )
    return exe


def extract_audio_from_mp4(mp4_path: str, target_sr: int) -> str:
    """
    用 ffmpeg 从 mp4 抽取音频到临时 wav（单声道、16-bit PCM、采样率=target_sr）。
    返回临时 wav 路径。
    """
    ffmpeg_bin = _require_ffmpeg()
    wav_tmp = os.path.join(tempfile.gettempdir(), f"aud_{uuid.uuid4().hex}.wav")

    cmd = [
        ffmpeg_bin,
        "-y",  # 覆盖输出
        "-i", mp4_path,  # 输入视频
        "-vn",  # 不要视频轨
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ac", "1",  # 单声道
        "-ar", str(target_sr),  # 目标采样率
        wav_tmp
    ]
    # 在 Windows 上带空格路径也能正常处理（subprocess 列表参数自动处理）
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0 or (not os.path.exists(wav_tmp)):
        raise RuntimeError(f"ffmpeg 抽取音频失败：\n{proc.stderr.decode('utf-8', errors='ignore')}")
    return wav_tmp


def get_video_meta(mp4_path: str):
    cap = cv2.VideoCapture(mp4_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{mp4_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_cnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_cnt / fps if fps > 0 else 0.0
    cap.release()
    return fps, frame_cnt, duration


def speech_file_to_array_fn(path, sampling_rate):
    # torchaudio 支持 wav；这里假定 extract_audio_from_mp4 已经给到目标采样率
    speech_array, _sr = torchaudio.load(path)  # (channels, time)
    if _sr != sampling_rate:
        resampler = torchaudio.transforms.Resample(_sr, sampling_rate)
        speech_array = resampler(speech_array)
    speech = speech_array.mean(dim=0, keepdim=True)  # 转单声道（如需保留立体声，改这里）
    return speech.squeeze().numpy()


# ====== 抽取卷积特征（时间序列）======
def _get_backbone_and_fe(model, feature_extractor):
    if hasattr(model, "hubert"):
        backbone = model.hubert
    elif hasattr(model, "wav2vec2"):
        backbone = model.wav2vec2
    else:
        raise AttributeError("未找到 backbone（hubert / wav2vec2）。")
    if hasattr(backbone, "feature_extractor"):
        fe = backbone.feature_extractor
    else:
        raise AttributeError("未找到 feature_extractor。")
    return backbone, fe


@torch.no_grad()
def extract_conv_feature_sequence(wav_path, sampling_rate, model, feature_extractor,return_step_hz=False):
    """
    返回 shape: (T_feat, 512) 的时间序列卷积特征（不做时间平均）。
    同时可返回特征帧率（可选）。
    """
    speech = speech_file_to_array_fn(wav_path, sampling_rate)
    inputs = feature_extractor(speech, sampling_rate=sampling_rate,
                               return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # 注册 hook 捕获卷积特征 (B, C=512, T_feat)
    _, fe = _get_backbone_and_fe(model, feature_extractor)
    cache = {}

    def _hook(module, inp, out):
        cache["conv_feat"] = out

    handle = fe.register_forward_hook(_hook)

    _ = model(**inputs)  # 前向一次
    handle.remove()

    if "conv_feat" not in cache:
        raise RuntimeError("未捕获到卷积特征（hook 失败）。")

    conv_feat = cache["conv_feat"]  # (B, 512, T_feat)
    conv_feat = conv_feat.squeeze(0).detach().cpu().numpy()  # (512, T_feat)
    conv_feat = conv_feat.transpose(1, 0)  # -> (T_feat, 512)

    if return_step_hz:
        # 对于 wav2vec2/Hubert，卷积总步长基本为 320 samples（16kHz 下约 50Hz）
        # 直接用长度关系估算更稳妥：步频 = T_feat / 秒数
        # 秒数 = 输入样本长度 / 采样率
        # 由于我们输入是整段音频，下面在主流程用视频 duration 来对齐，因此这里先返回 None
        return conv_feat, None
    return conv_feat


# ====== 时间对齐到视频逐帧 ======
def time_align_feat_to_frames(feat_seq: np.ndarray, audio_duration: float, frame_count: int, fps: float) -> np.ndarray:
    """
    feat_seq: (T_feat, 512)
    将音频特征在 [0, audio_duration] 线性插值到逐帧时间戳 t_k = k / fps, k=0..frame_count-1
    返回 (frame_count, 512)
    """
    T_feat = feat_seq.shape[0]
    if T_feat < 2 or audio_duration <= 0 or frame_count <= 0:
        # 退路：直接重复/截断到帧数
        return np.resize(feat_seq, (frame_count, feat_seq.shape[1]))

    # 特征时间网格（等间隔）
    t_feat = np.linspace(0.0, audio_duration, num=T_feat, endpoint=False)
    # 视频帧时间戳
    t_frames = np.arange(frame_count) / max(fps, 1e-6)

    # 逐通道插值
    out = np.empty((frame_count, feat_seq.shape[1]), dtype=np.float32)
    for c in range(feat_seq.shape[1]):
        out[:, c] = np.interp(t_frames, t_feat, feat_seq[:, c],
                              left=feat_seq[0, c], right=feat_seq[-1, c])
    return out


# ====== 端到端：从 MP4 到 (帧数, 512) ======
def extract_framewise_audio_embeddings_from_mp4(mp4_path, sampling_rate, model, feature_extractor):
    fps, frame_cnt, vid_duration = get_video_meta(mp4_path)
    if frame_cnt == 0:
        raise RuntimeError("未能获取视频帧数。")
    # 抽取音频（重采样到模型采样率）
    tmp_wav = extract_audio_from_mp4(mp4_path, sampling_rate)

    try:
        # (T_feat, 512)
        feat_seq = extract_conv_feature_sequence(tmp_wav, sampling_rate, model, feature_extractor)
        # 对齐到逐帧
        framewise = time_align_feat_to_frames(feat_seq, vid_duration, frame_cnt, fps)

        # 线性映射 -> (frame_cnt, 768)
        proj = nn.Linear(512, 768).to(device)
        framewise_768 = proj(
            torch.from_numpy(framewise).to(device)
        )

    finally:
        # 清理临时文件（如需保留音频，注释掉）
        if os.path.exists(tmp_wav):
            try:
                os.remove(tmp_wav)
            except Exception:
                pass

    return framewise_768  # (frame_cnt, 512)


@torch.no_grad()
def predict(path, sampling_rate, model, config, feature_extractor):
    speech = speech_file_to_array_fn(path, sampling_rate)
    inputs = feature_extractor(speech, sampling_rate=sampling_rate, return_tensors="pt", padding=True)
    inputs = {key: inputs[key].to(device) for key in inputs}
    logits = model(**inputs).logits
    scores = F.softmax(logits, dim=1).detach().cpu().numpy()[0]
    outputs = [{"Emotion": config.id2label[i], "Score": f"{round(score * 100, 3):.1f}%"} for i, score in
               enumerate(scores)]
    return outputs

