import torch
import warnings
import os
import json
import shutil

from fakesv_segment_duration import compute_exposure, build_segment_duration_json
from visual import extract_video_features
from ocr_visual import ocr_visual
from ocr_phase import extract_keyframes, ocr_extract, OCRBERTFeaturizer
from text_emo import text_emo
from text_phase import BERTFeaturizer
from audio_emo import extract_framewise_audio_embeddings_from_mp4, extract_audio_from_mp4, predict
from src.models import Wav2Vec2ForSpeechClassification, HubertForSpeechClassification
from transformers import AutoConfig, Wav2Vec2FeatureExtractor
from inference.transnetv2 import TransNetV2
from time import time

warnings.filterwarnings('ignore')


def Process(video_path, news_text, news_text_list):
    # 设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # News 输入视频+文本

    now = int(time())


    # 1、视频帧视觉特征
    video_features,video_frames = extract_video_features(video_path)
    video_features = torch.from_numpy(video_features)
    # video_features
    print('>>>>>>>>>>>>>>>>>视觉特征--提取完毕')


    # 2、OCR 文本图层特征
    checkpoint = r"./models/sam_vit_h_4b8939.pth"
    model_type = "vit_h"
    pooled_features = ocr_visual(checkpoint, model_type, video_path)
    # pooled_features
    print('>>>>>>>>>>>>>>>>>OCR 文本图层特征--提取完毕')


    # 3、视频图层语义特征
    # 3.1 视频帧 -- 图片提取
    files = extract_keyframes(video_path, out_dir="keyframes", prefix="kf_", ext="jpg")
    print("Extracted keyframe images:")
    for p in files:
        print(p)

    # 3.2 视频帧 -- ocr文本提取
    ocr_texts = []
    for file in files:
        ocr_result = ocr_extract(str(file))
        # 输出识别结果
        if ocr_result:
            print(ocr_result.replace('\n', ''))
            ocr_texts.append(ocr_result)

    # 3.3 视频帧 -- 文本特征
    featurizer = OCRBERTFeaturizer(
        model_name=r"./models/bert-base-uncased",
        max_length=512,
        stride=64,
        use_cls=False,
        remove_punct=False,
        output_dim=512,
        proj_trainable=False
    )

    embs_512, logits_2 = featurizer.encode_texts(ocr_texts, batch_size=8)
    print(embs_512.shape)
    print(logits_2.shape)
    embs_512 = {'%s'%now: embs_512}
    logits_2 = {'%s'%now: logits_2}
    # embs_512,logits_2
    print('>>>>>>>>>>>>>>>>>视频图层语义特征--提取完毕')


    # 4、文本情绪特征
    model_path = r"./models/roberta-base-go_emotions"
    filename = now
    token_embeddings, mean_vec, topk_labels = text_emo(model_path, news_text, filename)
    # token_embeddings, mean_vec
    # 文本情绪分类结果 topk_labels
    print('>>>>>>>>>>>>>>>>>文本情绪特征--提取完毕')


    # 5、文本语义特征
    featurizer = BERTFeaturizer(
        model_name=r"./models/bert-base-uncased",
        max_length=512,
        stride=64,
        use_cls=False,
        remove_punct=False,
        output_dim=512,      # 句向量投影后的维度
        proj_trainable=False
    )
    # 取token级隐藏层 与 池化后的 512 维句向量
    token_hidden, pooled_512 = featurizer.encode_tokens_and_pooled(news_text_list, batch_size=8)
    print("token_hidden:", token_hidden[0].shape)  # => (N, 512, 768)
    print("pooled_512:", pooled_512[0].shape)      # => (N, 512)

    token_hidden = {'%s'% now: token_hidden[0]}
    pooled_512 = {'%s'% now: pooled_512[0]}
    # token_hidden,pooled_512
    print('>>>>>>>>>>>>>>>>>文本语义特征--提取完毕')


    # 6、音频情绪特征
    # 音频情绪分类预训练模型
    Hubert_emotion_model = r"./models/Hubert_emotion"
    config = AutoConfig.from_pretrained(Hubert_emotion_model)

    # 视音频情绪向量提取
    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(Hubert_emotion_model)
    model = HubertForSpeechClassification.from_pretrained(Hubert_emotion_model).to(device)
    sampling_rate = feature_extractor.sampling_rate  # 采样率：16000

    # 特征提取
    framewise_512 = extract_framewise_audio_embeddings_from_mp4(video_path, sampling_rate, model, feature_extractor)
    print("framewise_512 shape:", framewise_512.shape)  # 期望: (视频帧数, 512)
    # framewise_512

    # 音频情绪分类
    tmp_wav = extract_audio_from_mp4(video_path, sampling_rate)
    audio_emo_cls = predict(tmp_wav, sampling_rate, model, config, feature_extractor)
    print('>>>>>>>>>>>>>>>>>音频情绪特征--提取完毕')

    # 7、动态文字持续时间特征（直接导出为文件）
    SAVE_JSON = r"G:\MyDataset\Graduate\FakingRecipe\fea\fakejm\fakesv_segment_duration.json"
    LANG = "eng"                                                                        # 中文： 'chi_sim'
    FRAME_STRIDE = 50                                                                   # n帧 1次OCR（1=逐帧，数值越大越快,但段落边界更粗糙）
    SIM_THRESHOLD = 0.90                                                                # 文本相似度阈值（>=该值认为是同一段）

    segs, summary = compute_exposure(video_path, FRAME_STRIDE, SIM_THRESHOLD)
    print("\n=== 文本段曝光时长（前若干条预览）===")
    for i, s in enumerate(segs[:20], 1):
        print(f"[{i}] f{s['begin_f']} -> f{s['end_f']} | "
              f"{s['dura_abs_sec']:.3f}s | {s['dura_rel_ratio']:.5f} | "
              f"\"{s['text_preview']}\"")

    print("\n=== 汇总 ===")
    for k, v in summary.items():
        print(f"{k}: {v}")


    # 8、meta_data.json 视频元文件
    model = TransNetV2()
    video_frames, single_frame_predictions, all_frame_predictions = model.predict_video(video_path)
    transnetv2_segs = model.predictions_to_scenes(single_frame_predictions)

    metainfo_json = []
    news_label = 'real'
    metainfo = {"video_id": "%s" % now,
                "annotation": "%s" % news_label,
                "fps": summary['fps'],
                "frame_count": summary['vframes'],
                "transnetv2_segs": transnetv2_segs.tolist()
                }
    metainfo_json.append(metainfo)

    # 9、文件导出
    operator_type = 'inference'  # or train

    # 9.1 推理 -- 每次覆盖文件
    if operator_type == 'inference':
        data_root_dict = r'G:\MyDataset\Graduate\FakingRecipe\fea\fakejm'
        ocr_sam = 'r0'

        # 数据（假设你已经提前定义了这些变量）
        ocr_phrase_fea = {'ocr_phrase_fea': embs_512, 'ocr_time_region': logits_2}
        emo_text_fea = {'last_hidden_state': token_embeddings, 'pooler_output': mean_vec}
        sem_text_fea = {'last_hidden_state': token_hidden, 'pooler_output': pooled_512}

        variables_to_save = {
            "preprocess_visual": video_features,
            "preprocess_ocr_sam": pooled_features,
            "ocr_phrase_fea": ocr_phrase_fea,
            "emo_text_fea": emo_text_fea,
            "sem_text_fea": sem_text_fea,
            "preprocess_audio": framewise_512
        }

        # 对应的保存路径
        path_to_save = [
            os.path.join(data_root_dict, 'preprocess_visual', f"{now}.pkl"),
            os.path.join(data_root_dict, 'preprocess_ocr', 'sam', f"{now}", f"{ocr_sam}.pkl"),
            os.path.join(data_root_dict, 'preprocess_ocr', 'ocr_phrase_fea.pkl'),
            os.path.join(data_root_dict, 'preprocess_text', 'emo_text_fea.pkl'),
            os.path.join(data_root_dict, 'preprocess_text', 'sem_text_fea.pkl'),
            os.path.join(data_root_dict, 'preprocess_audio', f"{now}.pkl")
        ]

        # 先清空,再创建
        shutil.rmtree(data_root_dict)
        for file_path, (name, value) in zip(path_to_save, variables_to_save.items()):
            dir_path = os.path.dirname(file_path)  # 获取文件夹路径
            os.makedirs(dir_path, exist_ok=True)   # 如果文件夹不存在则创建
            torch.save(value, file_path)
            print(f"已保存 {name} -> {file_path}")


        # metainfo.json 保存
        save_path = r"G:\MyDataset\Graduate\FakingRecipe\fea\fakejm\metainfo.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(metainfo_json[0], f, ensure_ascii=False)
            f.write("\n")

        print(f"保存完成: {save_path}")
        print(f"keys: {metainfo_json}")
        print('meta_data.json文件--提取完毕')

        # fakesv_segment_duration.json 保存
        build_segment_duration_json(video_path, SAVE_JSON, 'w')
        print('动态文字持续时间特征--提取完毕')

        # 视频训练/测试/验证集分割 -- vid -> split 文件
        # 读取meta_data.json文件中的vid,再进行分配即可
        dataset_split_vid = r'./data/FakeJM/data-split'
        test_vid = os.path.join(dataset_split_vid,'vid_time3_test.txt')
        train_vid = os.path.join(dataset_split_vid,'vid_time3_train.txt')
        val_vid = os.path.join(dataset_split_vid,'vid_time3_val.txt')

        with open(r"G:\MyDataset\Graduate\FakingRecipe\fea\fakejm\metainfo.json",'r') as f:
            meta_data = json.load(f)

        for file in [test_vid, train_vid, val_vid]:
            with open(file, 'w') as f:
                f.write(meta_data['video_id'])
                f.write('\n')

        print('由此，所有文件全部处理完毕，并保存至相应的文件夹中')

    # 9.2 构建数据集 -- 一股脑保存
    elif operator_type == 'train':
        data_root_dict = r'G:\MyDataset\Graduate\FakingRecipe\fea\fakejm_tarin'
        ocr_sam = 'r0'

        # 数据
        ocr_phrase_fea = {'ocr_phrase_fea': embs_512, 'ocr_time_region': logits_2}
        emo_text_fea = {'last_hidden_state': token_embeddings, 'pooler_output': mean_vec}
        sem_text_fea = {'last_hidden_state': token_hidden, 'pooler_output': pooled_512}

        variables_to_save = {
            "preprocess_visual": video_features,
            "preprocess_ocr_sam": pooled_features,
            "ocr_phrase_fea": ocr_phrase_fea,
            "emo_text_fea": emo_text_fea,
            "sem_text_fea": sem_text_fea,
            "preprocess_audio": framewise_512
        }

        # 保存路径
        path_to_save = [
            os.path.join(data_root_dict, 'preprocess_visual', f"{now}.pkl"),
            os.path.join(data_root_dict, 'preprocess_ocr', 'sam', f"{now}", f"{ocr_sam}.pkl"),
            os.path.join(data_root_dict, 'preprocess_ocr', 'ocr_phrase_fea.pkl'),
            os.path.join(data_root_dict, 'preprocess_text', 'emo_text_fea.pkl'),
            os.path.join(data_root_dict, 'preprocess_text', 'sem_text_fea.pkl'),
            os.path.join(data_root_dict, 'preprocess_audio', f"{now}.pkl")
        ]

        # 循环保存
        for file_path, (name, value) in zip(path_to_save, variables_to_save.items()):
            dir_path = os.path.dirname(file_path)  # 获取文件夹路径
            os.makedirs(dir_path, exist_ok=True)   # 如果文件夹不存在则创建
            torch.save(value, file_path)
            print(f"已保存 {name} -> {file_path}")

        # metainfo.json 保存
        save_path = r"G:\MyDataset\Graduate\FakingRecipe\fea\fakejm\metainfo.json"
        with open(save_path, "a", encoding="utf-8") as f:
            json.dump(metainfo_json[0], f, ensure_ascii=False)
            f.write("\n")

        print(f"保存完成: {save_path}")
        print(f"keys: {metainfo_json}")
        print('meta_data.json文件--提取完毕')

        # fakesv_segment_duration.json 保存
        build_segment_duration_json(video_path, SAVE_JSON, 'a')
        print('动态文字持续时间特征--提取完毕')

        # 视频训练/测试/验证集分割 -- vid -> split 文件
        # 读取meta_data.json文件中的vid,再进行分配即可
        dataset_split_vid = r'F:\0_My_jupyter\0_TruthLensLive\data\FakeJM_train\data-split'
        test_vid = os.path.join(dataset_split_vid,'vid_time3_test.txt')
        train_vid = os.path.join(dataset_split_vid,'vid_time3_train.txt')
        val_vid = os.path.join(dataset_split_vid,'vid_time3_val.txt')

        with open(r"G:\MyDataset\Graduate\FakingRecipe\fea\fakejm_train\metainfo.json", 'r') as f:
            meta_data = json.load(f)

        for file in [test_vid, train_vid, val_vid]:
            with open(file, 'a') as f:
                f.write(meta_data['video_id'])
                f.write('\n')

        print('由此，所有文件全部处理完毕，并保存至相应的文件夹中')

    return audio_emo_cls, topk_labels


if __name__ == '__main__':
    Video_path = r'E:/0_My_Project/VideoAIClip/AI_new/VideoAIClip/example/demo.mp4'
    News_text = "画面一个人摔了一跤"
    News_text_list = list(News_text)
    audio_emo_cls, topk_labels = Process(Video_path, News_text, News_text_list)


