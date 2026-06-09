'''
CLS向量   表示(512,768)内,直接取第一个token向量的权重(,768),作为代表
mean_vec 表示(512,768)内，取所有token向量的平均池化后的权重(,768),作为代表
'''

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification


def text_emo(model_path, news_text, filename, topk=5):
    # 分词
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)  # 关键改动
    model.to("cuda").eval()

    # 编码（固定 512）
    inputs = tokenizer(
        news_text,
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=512
    )
    inputs = {k: v.to("cuda") for k, v in inputs.items()}

    # 前向传播
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)  # 让模型把 hidden_states 也吐出来
        logits = outputs.logits                               # (1, 28)  直接就是 28 类情感分数
        last_hidden_state = outputs.hidden_states[-1]         # 同上，(1, 512, 768)

    # 句子向量（CLS 或均值池化）
    cls_vec   = last_hidden_state[:, 0, :]        # (1, 768)
    mask      = inputs["attention_mask"]          # mask 筛除value为0 的"滥竽充数" 的填充内容
    mean_vec  = (last_hidden_state * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True)
    token_embeddings = last_hidden_state[0]

    print("28 类情感 logits:", logits)
    print("CLS 向量 shape:", cls_vec.shape)
    print("均值池化向量 shape:", mean_vec.shape)

    print('----------------------------')
    print(token_embeddings.shape)
    print(mean_vec.shape)

    token_embeddings = {'%s'%filename: token_embeddings}
    mean_vec = {'%s'%filename: mean_vec}

    # 情绪分类
    # 读取标签映射（由微调权重写入）
    id2label = getattr(model.config, "id2label", None)
    if id2label is None:
        # 兜底：构造编号标签
        id2label = {i: f"LABEL_{i}" for i in range(model.config.num_labels)}

    # 判断是否为多标签任务（优先依据 config.problem_type）
    problem_type = getattr(model.config, "problem_type", None)
    IS_MULTILABEL = (problem_type == "multi_label_classification")

    # 可调参数
    THRESHOLD = 0.30  # 多标签阈值；可按验证集调整
    TOPK = min(topk, model.config.num_labels)

    with torch.no_grad():
        if IS_MULTILABEL:
            # 多标签：sigmoid + 阈值
            probs = torch.sigmoid(logits)[0].detach().float().cpu()  # (num_labels,)
            # 按阈值选择
            idxs = (probs >= THRESHOLD).nonzero(as_tuple=True)[0].tolist()
            # 若一个都没有超过阈值，就兜底取top1
            if not idxs:
                idxs = [int(torch.argmax(probs).item())]

            # 同时给出按概率排序的topK，便于观察
            topk_probs, topk_idxs = torch.topk(probs, k=TOPK)
            pred_labels = [(id2label[int(i)], float(probs[int(i)])) for i in idxs]
            topk_labels = [(id2label[int(i)], float(p)) for i, p in zip(topk_idxs, topk_probs)]

            print("【多标签】预测情绪：", pred_labels)
            print(f"Top{TOPK} 候选：", topk_labels)

        else:
            # 单标签：softmax
            probs = F.softmax(logits, dim=-1)[0].detach().float().cpu()  # (num_labels,)
            top_prob, top_idx = torch.max(probs, dim=-1)
            topk_probs, topk_idxs = torch.topk(probs, k=TOPK)

            pred_label = id2label[int(top_idx)]
            print("【单标签】预测情绪：", (pred_label, float(top_prob)))
            print(f"Top{TOPK} 候选：", [(id2label[int(i)], float(p)) for i, p in zip(topk_idxs, topk_probs)])

    return token_embeddings, mean_vec, topk_labels
