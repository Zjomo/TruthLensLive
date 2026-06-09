import gradio as gr


button_text = '使用说明'
window_text = '''
### 📖 使用流程:
  #### 📹 Step 1 - 视频输入:
  - **上传视频文件 或 输入 YouTube / TikTok 视频链接**
  - **选择语音识别和描述语言**
  - **自定义字幕设置**（字体、颜色、位置）
  - **✨ 启用高级字幕特效** （动画、描边、阴影、透明度）

  #### 🚀 Step 2 - 选择操作:
  - **🎬 处理视频**: 生成 AI 描述字幕 + 语音合成（TTS）+ 可选高级特效
  - **📝 生成SRT字幕**: 基于 Whisper 的精准字幕 + 动态字幕样式
  - **🤖 仅设置聊天机器人**: 跳过视频处理，快速建立问答机器人

  #### 💬 Step 3 - 视频问答:
  - 视频处理完成后或设置聊天机器人后，聊天功能启用
  - 可以对视频内容提问
  - AI 会分析视频音频内容并智能回答

  #### ⚠️  重要提示:
  - SRT 字幕和问答机器人仅支持 URL 输入（YouTube 或 TikTok）
  - TikTok 视频适合短视频内容分析
  - AI 处理包括：画面描述 + 语音合成 + 聊天机器人 + 字幕特效
  - SRT 生成基于 Whisper 模型，支持动态样式字幕
  - “仅聊天机器人”模式是最快捷的问答方案

  #### 🎨 字幕功能详细说明:
  **🔤 基础设置:**
  - **动态字体大小**: 可调节范围 20~80 像素
  - **丰富色彩选择**: 15 种颜色（含荧光色、金属色）
  - **字体选择**: 自动导入 fonts 文件夹下的 .ttf 字体
  - **位置选择**: 支持7个位置（顶部、中部、底部、左中右）

  **✨ 高级字幕特效（启用后）：**
  - **动画效果**: 淡入、滑动（上下左右）、缩放、波动、脉冲、旋转等
  - **特殊效果**: 发光、旋转、翻转、螺旋、弹跳、混合动画
  - **混合模式**: 随机组合多种动画
  - **描边控制**: 自定义 0~8px 外描边厚度
  - **阴影效果**: 0~8px 深度，提升可读性
  - **透明度调节**: 0.1~1.0 自由控制字幕透明度

  **🎬 效果示例:**
  - **滑动上升**: 字幕从底部平滑出现
  - **脉冲**: 有节奏地放大缩小，突出重点
  - **发光**: 模糊过渡到清晰，视觉吸引
  - **混合模式**: 多效果交替播放，动感十足

  #### 🔧 使用前提（依赖环境）:
  - **Ollama** 安装 `phi4:latest` & `gemma3:4b`
  - **Whisper** （用于字幕识别）
  - **FFmpeg** （视频音频处理）
  - **PIL/Pillow** （高级字幕渲染）
  - **网络环境** 可访问 YouTube / TikTok 资源
        '''

with gr.Blocks(css=r"""
/* 遮罩层：不再设置 display，由 Gradio 控制 */
#modal {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 9999;
}

/* 居中卡片：用绝对定位 + transform 居中 */
#modal .modal-card {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    padding: 20px;
    border-radius: 12px;
    min-width: 320px;
    max-width: 520px;
    width: min(90vw, 520px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}

/* 让“遮罩点击区”铺满整个屏幕（透明按钮） */
#backdrop {
    position: absolute;
    inset: 0;
    background: transparent;
    border: none;
    cursor: default;
}
""") as demo:
    open_btn = gr.Button(button_text)

    # 模态容器：默认隐藏，打开/关闭用 gr.update(visible=True/False)
    with gr.Group(visible=False, elem_id="modal") as modal:
        # 透明按钮铺满遮罩，用于点击空白处关闭
        backdrop = gr.Button("", elem_id="backdrop")

        # 弹窗内容卡片
        with gr.Column(elem_classes=["modal-card"]):
            gr.Markdown(window_text)
            close_btn = gr.Button("关闭", variant="secondary")

    # 打开弹窗
    open_btn.click(lambda: gr.update(visible=True), outputs=modal)

    # 关闭弹窗（按钮）
    close_btn.click(lambda: gr.update(visible=False), outputs=modal)

    # 关闭弹窗（点击遮罩）
    backdrop.click(lambda: gr.update(visible=False), outputs=modal)

demo.launch()
