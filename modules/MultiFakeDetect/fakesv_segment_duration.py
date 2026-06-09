# 视频中 -- 动态文字持续时间计算 -- 构建 fakesv_segment_duration.json

import cv2
import pytesseract
from PIL import Image
import numpy as np
from difflib import SequenceMatcher
from statistics import mean, pstdev
from pathlib import Path
import json


def ocr_text_from_frame(frame_bgr, lang="eng"):
    # 转灰度 & 轻微二值化，提升 OCR 稳定性
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    # 自适应阈值可以略微抑制背景
    thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 31, 11)
    pil_img = Image.fromarray(thr)
    txt = pytesseract.image_to_string(pil_img, lang=lang)
    # 规范化：去掉多余空白、小写化
    txt = " ".join(txt.split()).strip().lower()
    return txt


def similar(a, b):
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def compute_exposure(video_path, frame_stride=50, sim_th=0.90):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    vframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

    segments = []  # 每段: dict(text, begin_f, end_f)
    curr_text = None
    curr_begin = None
    curr_end = None

    fidx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if fidx % frame_stride == 0:
            txt = ocr_text_from_frame(frame)

            if curr_text is None:
                # 开启第一段
                curr_text = txt
                curr_begin = fidx
                curr_end = fidx
            else:
                # 与上一段文本比对相似度
                if similar(txt, curr_text) >= sim_th:
                    # 相似 -> 继续同一段
                    curr_end = fidx
                else:
                    # 文本变化 -> 结束上一段，开启新段
                    segments.append({
                        "text": curr_text,
                        "begin_f": curr_begin,
                        "end_f": curr_end
                    })
                    curr_text = txt
                    curr_begin = fidx
                    curr_end = fidx
        fidx += 1

    # 收尾：把最后一段加进去
    if curr_text is not None:
        segments.append({
            "text": curr_text,
            "begin_f": curr_begin,
            "end_f": curr_end
        })

    cap.release()

    # 计算曝光时长（绝对/相对）
    results = []
    abs_durations = []
    rel_durations = []

    for seg in segments:
        begin_f = seg["begin_f"]
        end_f = seg["end_f"]
        # 注意：若 stride>1，这里的 end_f、begin_f 是“被采样的帧”，
        # 为了更接近真实，可以 + (frame_stride-1) 做近似扩张，这里保持简单
        length_frames = (end_f - begin_f + 1)
        dura_abs = length_frames / fps
        dura_rel = length_frames / max(vframes, 1)

        results.append({
            "begin_f": begin_f,
            "end_f": end_f,
            "text_preview": seg["text"][:60],
            "dura_abs_sec": dura_abs,
            "dura_rel_ratio": dura_rel
        })
        abs_durations.append(dura_abs)
        rel_durations.append(dura_rel)

    # 动态性指标（分别基于绝对/相对时长）
    # 用总体标准差 pstdev（避免样本量小不稳定）
    if abs_durations:
        mu_abs = mean(abs_durations)
        sg_abs = pstdev(abs_durations)
        ID_abs = sg_abs * (1 - mu_abs)  # 论文形式；若想无量纲可用 rel 的 ID
    else:
        mu_abs = sg_abs = ID_abs = 0.0

    if rel_durations:
        mu_rel = mean(rel_durations)
        sg_rel = pstdev(rel_durations)
        ID_rel = sg_rel * (1 - mu_rel)
    else:
        mu_rel = sg_rel = ID_rel = 0.0

    summary = {
        "fps": fps,
        "vframes": vframes,
        "num_segments": len(results),
        "mean_abs_sec": mu_abs,
        "std_abs_sec": sg_abs,
        "ID_abs": ID_abs,
        "mean_rel": mu_rel,
        "std_rel": sg_rel,
        "ID_rel": ID_rel
    }
    return results, summary


def build_segment_duration_json(video_path, save_path, save_type='w'):
    segs, summary = compute_exposure(video_path)

    # 提取绝对/相对时长数组
    ocr_abs_list = [s["dura_abs_sec"] for s in segs]
    ocr_rel_list = [s["dura_rel_ratio"] for s in segs]

    # 如果要模拟“all_seg_duration”，可以直接复用 ocr 的值
    all_abs_list = ocr_abs_list.copy()
    all_rel_list = ocr_rel_list.copy()

    seg_dura_info = {
        "all_seg_duration": all_abs_list,  # 所有自然段绝对时长（秒）
        "all_seg_dura_ratio": all_rel_list,  # 所有自然段相对时长（比例）
        "ocr_all_seg_duration": ocr_abs_list,  # OCR 检测到的文本段绝对时长
        "ocr_all_seg_dura_ratio": ocr_rel_list  # OCR 检测到的文本段相对时长
    }

    # 保存成 json
    with open(save_path, save_type, encoding="utf-8") as f:
        json.dump(seg_dura_info, f, ensure_ascii=False, indent=2)

    print(f"保存完成: {save_path}")
    print(f"keys: {seg_dura_info.keys()}")



