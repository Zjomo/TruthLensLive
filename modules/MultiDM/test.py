import gradio as gr

css = """
.button-section {
    background: #ffffff;
    color: #ffffff !important;
    border-radius: 8px;
    padding: 16px;

/* 处理内容按钮：红色 */
#process-btn {
    background: #e74c3c !important;
    border-color: #c0392b !important;
    color: #fff !important;
}

/* SRT 字幕按钮：绿色 */
#srt-btn {
    background: #27ae60 !important;
    border-color: #1e8449 !important;
    color: #fff !important;
}

/* 启动机器人按钮：蓝色 */
#setup-chatbot-btn {
    background: #3498db !important;
    border-color: #2980b9 !important;
    color: #fff !important;
}
"""

with gr.Blocks(css=css) as demo:
    with gr.Group(elem_classes="button-section"):
        gr.Markdown("### 🚀 启动")
        gr.Markdown("*对导入视频进行下述操作*")

        with gr.Row():
            process_btn = gr.Button(
                "🎬 处理内容\n(AI 总结 + TTS)",
                variant="primary", size="lg", scale=1,
                elem_id="process-btn"          # 👈 对应 CSS
            )
            srt_btn = gr.Button(
                "📝 SRT字幕生成\n(Whisper 转录)",
                variant="primary", size="lg", scale=1,
                elem_id="srt-btn"
            )
            setup_chatbot_btn = gr.Button(
                "🤖 启动机器人\n(视频内容交流)",
                variant="primary", size="lg", scale=1,
                elem_id="setup-chatbot-btn"
            )

demo.launch(debug=True)
