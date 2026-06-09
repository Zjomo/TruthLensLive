import torch
from torchvision import models, transforms
from torch import nn
from PIL import Image
import cv2
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# 基于预训练ResNet50，提取每个视频帧 的图像特征
model = models.resnet50(pretrained=True)
model = torch.nn.Sequential(*list(model.children())[:-2])  # 去掉最后的fc层和AdaptiveAvgPool2d
model.add_module('global_pool', nn.AdaptiveAvgPool2d(1))  # 添加全局池化层，将每个特征图的大小变为(1, 1)
model.add_module('flatten', nn.Flatten())  # 添加Flatten层，将(2048, 1, 1)压平为(2048)
model.add_module('fc', nn.Linear(2048, 512))  # 添加全连接层将输出维度从2048降到512
model.eval()  # 设置为评估模式

# 预处理步骤（图像的归一化与大小调整）
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


# 读取视频并提取每一帧
def extract_video_features(video_path, frame_interval=30, max_frames=None):
    video_capture = cv2.VideoCapture(video_path)

    frame_features = []
    frames = []

    frame_count = 0
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # 控制抽帧间隔
        if frame_count % frame_interval == 0:
            # 转换为PIL图像并进行预处理
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            image = transform(image).unsqueeze(0)
            with torch.no_grad():
                feature = model(image).squeeze().numpy()  # 提取特征

            frame_features.append(feature)
            frames.append(frame)

            # 限制最大帧数
            if max_frames and len(frame_features) >= max_frames:
                break

        frame_count += 1

    video_capture.release()
    return np.array(frame_features), frames







