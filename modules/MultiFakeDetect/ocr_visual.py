import cv2
import torch
from segment_anything import sam_model_registry, SamPredictor

def ocr_visual(checkpoint, model_type, video_path, frame_stride=30):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    sam = sam_model_registry[model_type](checkpoint=checkpoint).to(device)
    sam.eval()  # 评估模式
    predictor = SamPredictor(sam)

    cap = cv2.VideoCapture(video_path)
    frame_idx = 0
    feat_sum = None
    n = 0

    autocast_ctx = (
        torch.autocast(device_type="cuda", dtype=torch.float16)
        if device == "cuda" else torch.no_grad()
    )

    with torch.inference_mode():  # 关闭梯度
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # 抽帧
            if frame_idx % frame_stride != 0:
                frame_idx += 1
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            with (autocast_ctx if device == "cuda" else torch.no_grad()):
                predictor.set_image(frame_rgb)
                # 更稳妥：用 API 而不是直接访问内部属性
                features = predictor.get_image_embedding()  # [1, 256, 64, 64]
                features = features.squeeze(0).detach()     # [256, 64, 64]

            # 在线累加做平均，不保存列表
            if feat_sum is None:
                feat_sum = features.clone()
            else:
                feat_sum += features
            n += 1
            frame_idx += 1

    cap.release()

    if n == 0:
        raise ValueError("没有有效帧被处理（可能视频打不开或采样率太高）。")

    pooled_features = feat_sum / n  # [256, 64, 64]
    print(pooled_features.shape)
    return pooled_features
