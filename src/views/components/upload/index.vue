<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">乐器图片识别服务</div>
    </template>
    <!-- 上传组件 -->
    <el-upload
      v-model:file-list="fileList"
      drag
      multiple
      class="pure-upload"
      list-type="picture-card"
      accept="image/jpeg,image/png,image/gif"
      :http-request="customRequest"
      :limit="5"
      :on-success="onSuccess"
      :on-exceed="onExceed"
      :before-upload="onBefore"
    >
      <template #file="{ file }">
        <div>
          <img class="el-upload-list__item-thumbnail" :src="file.url" />
        </div>
        <div v-if="file.response">
          <p>识别结果：</p>
          <p>乐器名称：{{ file.response.name }}</p>
          <p>置信度：{{ file.response.confidence }}%</p>
        </div>
      </template>
    </el-upload>
    <el-divider />
    <!-- 历史记录表格 -->
    <el-table :data="historyList" style="width: 100%">
      <el-table-column prop="fileName" label="文件名" />
      <el-table-column prop="name" label="乐器名称" />
      <el-table-column prop="confidence" label="置信度" />
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { message } from "@/utils/message";
import axios from "axios";

// 响应式变量
const fileList = ref([]); // 上传的文件列表
const historyList = ref([]); // 历史记录列表

// 上传前校验
const onBefore = file => {
  if (!["image/jpeg", "image/png", "image/gif"].includes(file.type)) {
    message("只能上传图片文件");
    return false;
  }
  if (file.size / 1024 / 1024 > 5) {
    message("文件大小不能超过5MB");
    return false;
  }
  return true; // 校验通过
};

// 超出文件限制时提示
const onExceed = () => {
  message("最多上传5个文件，请先删除再上传");
};

// 自定义上传逻辑
const customRequest = async options => {
  const { file, onSuccess, onError } = options;

  try {
    const formData = new FormData();
    formData.append("image", file);

    const response = await axios.post(
      "http://127.0.0.1:5010/predict",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      }
    );

    // 调用成功回调
    if (
      response.data &&
      Array.isArray(response.data) &&
      response.data.length > 0
    ) {
      onSuccess(response.data, file);
    } else {
      throw new Error("后端返回数据为空或格式不正确");
    }
  } catch (error) {
    // 调用失败回调
    onError(error);
    message("识别失败，请重试");
  }
};

// 上传成功处理
const onSuccess = (response, file) => {
  if (Array.isArray(response) && response.length > 0) {
    file.response = response[0]; // 假设后端返回的结果是数组
    historyList.value.push({
      fileName: file.name,
      name: response[0].name,
      confidence: response[0].confidence
    });
  } else {
    message("识别结果为空，请检查后端服务");
  }
};
</script>

<style lang="scss" scoped>
.card-header {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
}

.pure-upload {
  .el-upload-dragger {
    background-color: #f9f9f9;
    border: 2px dashed #d9d9d9;
  }
}
</style>
