import cv2
import torch
from segment_anything import sam_model_registry, SamPredictor
import numpy as np

'''
针对视频文件，提取整个视频的特征，再做一个平均池化

'''

def ocr_visual(checkpoint, model_type, video_path):
    # 1️⃣ 加载模型
    device = "cuda" if torch.cuda.is_available() else "cpu"
    sam = sam_model_registry[model_type](checkpoint=checkpoint)
    sam.to(device=device)

    # 2️⃣ 创建 predictor
    predictor = SamPredictor(sam)

    # 3️⃣ 提取视觉特征示例
    def extract_visual_features_from_video(video_path):
        # 读取视频
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        all_features = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1

            # 转换为 RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            predictor.set_image(frame_rgb)

            # 获取当前帧的特征
            features = predictor.features  # shape: [1, 256, 64, 64]
            all_features.append(features)

        cap.release()

        # 将所有帧的特征堆叠并进行池化
        all_features = torch.cat(all_features, dim=0)  # stack features: shape [frame_count, 256, 64, 64]

        # 平均池化处理
        pooled_features = all_features.mean(dim=0)  # shape: [256, 64, 64]

        return pooled_features

    # 提取视频特征并进行平均池化
    pooled_features = extract_visual_features_from_video(video_path)
    print(pooled_features.shape)  # Expected shape: torch.Size([256, 64, 64])

    return pooled_features



