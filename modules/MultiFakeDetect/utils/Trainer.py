import os
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import tqdm
from sklearn.metrics import *
from tqdm import tqdm
from .metrics import *
import copy
import torch.nn.functional as F


class Trainer():
    def __init__(self,model,device,lr,dataloaders,save_param_path,writer,early_stop,epoches,model_name,save_predict_result_path,beta_c,beta_n,scheduler_option=False,save_threshold = 0.7, start_epoch = 0):
        self.model = model
        self.device = device
        self.model_name = model_name
        self.dataloaders = dataloaders
        self.start_epoch = start_epoch
        self.num_epochs = epoches
        self.early_stop = early_stop
        self.save_threshold = save_threshold
        self.writer = writer
        self.scheduler_option=scheduler_option
        self.beta_c=beta_c
        self.beta_n=beta_n
        if os.path.exists(save_param_path):
            self.save_param_path = save_param_path
        else:
            self.save_param_path = os.makedirs(save_param_path)
            self.save_param_path= save_param_path

        if os.path.exists(save_predict_result_path):
            self.save_predict_result_path = save_predict_result_path
        else:
            self.save_predict_result_path = os.makedirs(save_predict_result_path)
            self.save_predict_result_path= save_predict_result_path

        self.lr = lr

        self.CEloss = nn.CrossEntropyLoss()

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=5e-5)
        if scheduler_option:
            self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                    self.optimizer,
                    mode='min',
                    patience=1,
                    min_lr=1e-6,
                    verbose=True)


    def train(self):
        since = time.time()

        self.model.cuda()

        best_model_wts_test = copy.deepcopy(self.model.state_dict())
        best_f1_test = 0.0
        best_epoch_test = 0
        is_earlystop = False

        for epoch in range(self.start_epoch, self.start_epoch+self.num_epochs):
            if is_earlystop:
                break
            print('-' * 50)
            print('Epoch {}/{}'.format(epoch, self.start_epoch+self.num_epochs - 1))
            print('-' * 50)

            #train phase
            self.model.train()
            print('-' * 10)
            print ('TRAIN')
            print('-' * 10)
            running_loss = 0.0
            tpred = []
            tlabel = []


            for batch in tqdm(self.dataloaders['train']):
                self.optimizer.zero_grad()
                batch_data=batch
                for k,v in batch_data.items():
                    if k!='vid':
                        batch_data[k]=v.cuda()
                labels = batch_data['label']
                outputs,output_content,output_narative = self.model(**batch_data)

                loss=self.CEloss(outputs, labels)+self.beta_c*self.CEloss(output_content, labels)+self.beta_n*self.CEloss(output_narative, labels)

                loss.backward()
                self.optimizer.step()


                running_loss += loss.item() * labels.size(0)
                tpred.extend(torch.max(outputs, 1)[1].tolist())


                tlabel.extend(labels.tolist())

            epoch_loss = running_loss / len(self.dataloaders['train'].dataset)
            print('Train Loss: {:.4f} '.format(epoch_loss))
            results = metrics(tlabel, tpred)
            print (results)


            self.writer.add_scalar('Loss/train', epoch_loss, epoch)
            self.writer.add_scalar('Acc/train', results['acc'], epoch)
            self.writer.add_scalar('F1/train', results['f1'], epoch)

            #val phase
            self.model.eval()
            print('-' * 10)
            print ('VAL')
            print('-' * 10)
            val_loss = 0.0
            val_tpred = []
            val_tlabel = []
            for batch in tqdm(self.dataloaders['val']):
                batch_data=batch
                for k,v in batch_data.items():
                    if k!='vid':
                        batch_data[k]=v.cuda()
                labels = batch_data['label']
                with torch.no_grad():
                    outputs,output_content,output_narative = self.model(**batch_data)

                    loss=self.CEloss(outputs, labels)+self.beta_c*self.CEloss(output_content, labels)+self.beta_n*self.CEloss(output_narative, labels)

                val_loss += loss.item() * labels.size(0)
                val_tpred.extend(torch.max(outputs, 1)[1].tolist())

                val_tlabel.extend(labels.tolist())
            epoch_loss_val = val_loss / len(self.dataloaders['test'].dataset)
            print('Val Loss: {:.4f} '.format(epoch_loss_val))
            results_val = metrics(val_tlabel, val_tpred)
            print (results_val)
            if self.scheduler_option:
                self.scheduler.step(epoch_loss_val)

            if results_val['f1']>best_f1_test:
                best_f1_test = results_val['f1']
                best_epoch_test = epoch
                best_model_wts_test = copy.deepcopy(self.model.state_dict())
                if best_f1_test > self.save_threshold:
                    torch.save(best_model_wts_test, self.save_param_path+self.model_name+"_val_" + str(best_epoch_test) + "_{0:.4f}".format(best_f1_test))
                    print("saved "+self.save_param_path+self.model_name+ "_val_" + str(best_epoch_test) + "_{0:.4f}".format(best_f1_test))
            else:
                if epoch - best_epoch_test >= self.early_stop-1:
                    is_earlystop = True
                    print("early stop at epoch "+str(epoch))

        time_elapsed = time.time() - since

        print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
        print("Best model on val: epoch" + str(best_epoch_test) + "_" + str(best_f1_test))
        ckp_path=self.save_param_path+self.model_name+"_val_" + str(best_epoch_test) + "_{0:.4f}".format(best_f1_test)

        return ckp_path

    def test(self,ckp_path):
        self.model.load_state_dict(torch.load(ckp_path))
        since=time.time()
        self.model.cuda()
        self.model.eval()
        pred = []
        label = []
        vid=[]

        for batch in tqdm(self.dataloaders['test']):
            with torch.no_grad():
                batch_data=batch
                for k,v in batch_data.items():
                    if k!='vid':
                        batch_data[k]=v.cuda()
                labels = batch_data['label']
                outputs,output_content,output_narative = self.model(**batch_data)
                label.extend(labels.tolist())
                pred.extend(torch.max(outputs, 1)[1].tolist())

                vid.extend(batch_data['vid'])
        time_elapsed = time.time() - since
        print('Testing complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))

        result=pd.DataFrame({'vid':vid,'label':label,'pred':pred})
        result.to_csv(self.save_predict_result_path+self.model_name+'.csv',sep='\t',index=False)

        print (get_confusionmatrix_fnd(np.array(pred), np.array(label)))
        print (metrics(label, pred))

        return metrics(label, pred)


class Inferencer():
    def __init__(self, model, device, model_name, dataset, dataloader, save_predict_result_path):
        self.model = model
        self.device = device
        self.model_name = model_name
        self.dataset=dataset
        self.dataloader=dataloader
        if os.path.exists(save_predict_result_path):
            self.save_predict_result_path = save_predict_result_path
        else:
            self.save_predict_result_path = os.makedirs(save_predict_result_path)
            self.save_predict_result_path= save_predict_result_path

    def _load_ckpt_compat(self, ckp_path):
        sd = torch.load(ckp_path, map_location='cpu')

        enc = self.model.editing_branch.dura_encoder
        targets = {
            'editing_branch.dura_encoder.ab_duration_embed.weight': enc.ab_duration_embed.num_embeddings,  # 102
            'editing_branch.dura_encoder.re_duration_embed.weight': enc.re_duration_embed.num_embeddings,  # 52
            'editing_branch.dura_encoder.ocr_ab_duration_embed.weight': enc.ocr_ab_duration_embed.num_embeddings,  # 102
            'editing_branch.dura_encoder.ocr_re_duration_embed.weight': enc.ocr_re_duration_embed.num_embeddings,  # 52
        }

        def pad_or_trim(w, target_rows):
            rows = w.shape[0]
            if rows == target_rows - 1:  # 旧ckpt(101/51) -> 新模型(102/52)：复制最后一行补齐
                return torch.cat([w, w[-1:].clone()], dim=0)
            elif rows < target_rows:  # 少得更多：全都用最后一行补齐
                need = target_rows - rows
                return torch.cat([w, w[-1:].repeat(need, 1)], dim=0)
            elif rows > target_rows:  # 万一更多：截断到目标行数
                return w[:target_rows]
            return w

        # 对 4 个嵌入权重做尺寸对齐
        for k, tgt in targets.items():
            if k in sd:
                sd[k] = pad_or_trim(sd[k], tgt)

        missing, unexpected = self.model.load_state_dict(sd, strict=False)
        print('missing:', missing)
        print('unexpected:', unexpected)

    def inference(self,ckp_path):
        # self.model.load_state_dict(torch.load(ckp_path), strict=False)
        # 换成：
        # self._load_ckpt_compat(ckp_path)
        self._load_ckpt_compat(ckp_path)
        since = time.time()
        self.model.cuda()
        self.model.eval()

        label = []
        vid = []
        pred = []
        pred_prob = []

        for batch in tqdm(self.dataloader):
            with torch.no_grad():
                batch_data=batch
                for k,v in batch_data.items():
                    if k!='vid':
                        batch_data[k]=v.cuda()
                labels = batch_data['label']
                outputs, output_content,output_narative = self.model(**batch_data)

                # 预测类别
                pred_idx = torch.max(outputs, 1)[1]  # [B]
                # 预测概率（对数值做 softmax，取对应预测类别的概率）
                probs = F.softmax(outputs, dim=1)  # [B, C]
                conf = probs.gather(1, pred_idx.unsqueeze(1))  # [B, 1]
                conf = conf.squeeze(1)  # [B]




                label.extend(labels.tolist())
                pred.extend(torch.max(outputs, 1)[1].tolist())
                pred_prob.extend(conf.detach().cpu().tolist())
                vid.extend(batch_data['vid'])
        time_elapsed = time.time() - since
        print('Inference complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))

        result = pd.DataFrame({
            'vid': vid,
            'label': label,
            'pred': pred,
            'pred_prob': pred_prob  # 新增
        })

        result.to_csv(self.save_predict_result_path+self.model_name+'.csv',sep='\t',index=False)

        print (get_confusionmatrix_fnd(np.array(pred), np.array(label)))
        print (metrics(label, pred))

        return metrics(label, pred)

