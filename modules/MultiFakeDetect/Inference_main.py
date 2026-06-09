import argparse
import os
import random
import warnings
import numpy as np
import pandas as pd
import torch
from Inference_run import Run
from VideoProcess import Process


'''
# 设定命令参数
parser = argparse.ArgumentParser()
parser.add_argument('--dataset', default='fakett', help='fakett/fakesv/fakejm')
parser.add_argument('--mode', default='inference_test', help='train/inference_test')
parser.add_argument('--epoches', type=int, default=30)
parser.add_argument('--batch_size', type = int, default=128)
parser.add_argument('--early_stop', type=int, default=5)
parser.add_argument('--seed', type=int, default=2025)
parser.add_argument('--gpu', default='0')
parser.add_argument('--lr', type=float)
parser.add_argument('--alpha',type=float)
parser.add_argument('--beta',type=float)
parser.add_argument('--inference_ckp', help='input path of inference checkpoint when mode is inference')
parser.add_argument('--path_ckp', default= './checkpoints/')
parser.add_argument('--path_tb', default= './tensorboard/')
args = parser.parse_args()
'''

# 设定环境变量 + 随机种子
os.environ['CUDA_VISIBLE_DEVICES'] = str(0)
os.environ['CUDA_LAUNCH_BLOCKING']='1'
seed = 2025
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed(seed)
torch.backends.cudnn.benchmark = False      # 关闭Cudnn 对硬件的优化，每次训练结果一致
torch.backends.cudnn.deterministic = True   # GPU不因浮点数影响，每次输出都一致


config = {
    'dataset': 'fakejm',
    'mode': 'inference_test',
    'epoches': 1,
    'batch_size': 1,
    'early_stop': 5,
    'device': '0',
    'seed': 2025,
    'lr': 0.001,
    'alpha': 0,
    'beta': 255,
    'inference_ckp': './provided_ckp/FakingRecipe_fakesv',
    'path_ckp': './checkpoints/',
    'path_tb': './tensorboard/'
}


# 传递命令参数 到run.py 中的main 函数
if __name__ == '__main__':
    # 视频导入 + 特征提取
    Video_path = r'E:/0_My_Project/VideoAIClip/AI_new/VideoAIClip/example/demo.mp4'
    News_text = "画面一个人摔了一跤"
    audio_emo_cls, topk_labels = Process(Video_path, News_text, list(News_text))

    # 推理 + 生成预测文件夹 ./predict_result/FakeJM/FakingRecipe.csv
    Run(config=config).main()
    News_pred = pd.read_csv(r'./predict_result/FakeJM/FakingRecipe.csv')


