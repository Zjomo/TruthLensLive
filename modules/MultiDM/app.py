import gradio as gr
import os
from describe import (
    download_youtube_video,
    download_video_from_url,
    encode_video,
    generate_frame_descriptions,
    summarize_with_ollama,
    translate_and_enhance_with_ollama
)
from subtitle import create_subtitled_video
from tts import create_video_with_tts
from video_chat import YouTubeToText
from srt_subtitle import process_video_with_srt
import warnings

# warnings.filterwarnings('ignore')

# 支持语言
LANGUAGES = {
    'Chinese': 'cn',
    'English': 'en',
    'Turkish': 'tr'
}

# 字幕颜色配置
SUBTITLE_COLORS = {
    'Yellow': '#FFFF00',
    'White': '#FFFFFF',
    'Red': '#FF0000',
    'Green': '#00FF00',
    'Blue': '#0080FF',
    'Purple': '#FF00FF',
    'Orange': '#FF8000',
    'Pink': '#FF80C0',
    'Gold': '#FFD700',
    'Silver': '#C0C0C0',
    'Neon Green': '#39FF14',
    'Neon Blue': '#1B03A3',
    'Turquoise': '#40E0D0',
    'Lavender': '#E6E6FA',
    'Lime': '#32CD32'
}

# 字幕效果
SUBTITLE_EFFECTS = {
    'fade': 'Smooth Fade',
    'slide_up': 'Slide Up',
    'slide_down': 'Slide Down',
    'slide_left': 'Slide Left',
    'slide_right': 'Slide Right',
    'zoom': 'Zoom In/Out',
    'zoom_in': 'Zoom In',
    'zoom_out': 'Zoom Out',
    'glow': 'Glow Effect',
    'shake': 'Shake',
    'rotate_cw': 'Rotate Clockwise',
    'rotate_ccw': 'Rotate Counter-Clockwise',
    'wave': 'Wave Motion',
    'pulse': 'Pulse',
    'flip': 'Flip',
    'spiral': 'Spiral',
    'elastic': 'Elastic',
    'bounce': 'Bounce',
    'mixed': 'Mixed (Random)',
    'none': 'No Effect'
}

# 位置配置
SUBTITLE_POSITIONS = {
    'bottom': 'Bottom Center',
    'bottom_left': 'Bottom Left',
    'bottom_right': 'Bottom Right',
    'middle': 'Middle Center',
    'top': 'Top Center',
    'top_left': 'Top Left',
    'top_right': 'Top Right'
}

# 字体动态导入
def get_available_fonts():
    fonts_dir = os.path.join(os.getcwd(), 'fonts')
    fonts = {'Default': None}   # Default font

    # 字体目录，若不存在则新建
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
        print(f"字体路径创建至: {fonts_dir}")
        print("可导入.ttf 文件至此路径")

    if os.path.exists(fonts_dir):
        font_count = 0
        for font_file in os.listdir(fonts_dir):
            if font_file.lower().endswith('.ttf'):
                font_name = os.path.splitext(font_file)[0]
                font_path = os.path.join(fonts_dir, font_file)
                fonts[font_name] = font_path
                font_count += 1

        print(f"从字体目录导入 {font_count} 种字体")
        if font_count == 0:
            print("字体文件夹为空, 请添加你的.tff文件")

    return fonts


SUBTITLE_FONTS = get_available_fonts()

# Global RAG system
rag_system = None
current_transcript = ""


# 1、初始化RAG 系统
def initialize_rag_system():
    """Initialize RAG system"""
    global rag_system
    try:
        # 文本嵌入
        rag_system = YouTubeToText(
            enable_rag=True,
            embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        print("✅ RAG 系统初始化成功")
        return True
    except Exception as e:
        print(f"❌ RAG 系统初始化失败: {e}")
        return False


# 2、仅配置机器人
def setup_chatbot_only(video_input, youtube_url, tiktok_url, selected_lang):
    """Setup chatbot without video processing"""
    global rag_system, current_transcript

    # Determine video URL from inputs
    video_url = None
    if tiktok_url and tiktok_url.strip():
        video_url = tiktok_url.strip()
    elif youtube_url and youtube_url.strip():
        video_url = youtube_url.strip()
    elif isinstance(video_input, str) and (video_input.startswith(('http://', 'https://'))):
        video_url = video_input

    if not video_url:
        return "❌ 请输入有效的视频URL （YouTube或TikTok）", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    if not rag_system:
        if not initialize_rag_system():
            return "❌ RAG 系统初始化失败", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    try:
        # 编码语言切换
        lang_code = LANGUAGES[selected_lang]
        print(f"🤖 配置视频分析机器人: {video_url}")
        print(f"🌍 语言: {selected_lang} ({lang_code})")

        result = rag_system.process_with_rag(video_url, method="whisper", language=lang_code)

        if result.get("transcript") and result.get("rag_ready"):
            current_transcript = result["transcript"]
            status = f"✅ 视频聊天机器人准备好了！语言: {selected_lang}. 可以在下面进行交流."
            return status, gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)
        else:
            return "❌ 创建 RAG系统失败", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    except Exception as e:
        return f"❌ RAG 错误: {str(e)}", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)


# 3、视频摘要+字幕生成
def process_video_with_lang(video_input, youtube_url, tiktok_url, selected_lang, font_size, font_color, text_position, font_family,
                           effect_type, outline_size, shadow_size, opacity, enable_advanced):
    """Process video and generate summary with enhanced subtitles"""
    global current_transcript, rag_system

    try:
        # 1. 视频处理，URL优先级： TikTok > YouTube > Upload
        video_url = None
        if tiktok_url and tiktok_url.strip():
            print("处理 TikTok URL...")
            video_path = download_video_from_url(tiktok_url.strip())
            video_url = tiktok_url.strip()
        elif youtube_url and youtube_url.strip():
            print("处理 YouTube URL...")
            video_path = download_video_from_url(youtube_url.strip())
            video_url = youtube_url.strip()
        elif isinstance(video_input, str) and (video_input.startswith(('http://', 'https://'))):
            print("从输入视频处理 URL...")
            video_path = download_video_from_url(video_input)
            video_url = video_input
        else:
            print("处理 导入视频...")
            video_path = video_input.name if hasattr(video_input, 'name') else video_input

        frames, scene_times = encode_video(video_path)

        # 2. 生成英文描述
        original_descriptions = generate_frame_descriptions(frames, scene_times)

        # 3. 语言检查与翻译
        lang_code = LANGUAGES[selected_lang]
        print(f"[APP] 翻译功能启动 - target_lang: {lang_code}")
        # Translate if not English
        if lang_code != 'en':
            print("翻译描述...")
            scene_descriptions = translate_and_enhance_with_ollama(original_descriptions, lang_code)
            print("\n第一场景 描述:")
            print(f"初始 (EN): {original_descriptions[0]}")
            print(f"处理 ({lang_code.upper()}): {scene_descriptions[0]}")
        else:
            scene_descriptions = original_descriptions

        # 4. Create enhanced subtitled video configuration
        # Position conversion
        position_key = 'bottom'
        for key, value in SUBTITLE_POSITIONS.items():
            if value == text_position:
                position_key = key
                break

        subtitle_config = {
            'font_size': font_size,
            'font_color': SUBTITLE_COLORS[font_color],
            'text_position': position_key,
            'font_family': SUBTITLE_FONTS[font_family]
        }

        # Advanced settings (if enabled)
        advanced_config = None
        if enable_advanced:
            # Find effect key
            effect_key = 'fade'
            for key, value in SUBTITLE_EFFECTS.items():
                if value == effect_type:
                    effect_key = key
                    break

            advanced_config = {
                'font_size': font_size,
                'font_color': SUBTITLE_COLORS[font_color],
                'text_position': position_key,
                'font_family': SUBTITLE_FONTS[font_family] or 'Arial Black',
                'effect_type': effect_key,
                'outline_size': outline_size,
                'shadow_size': shadow_size,
                'opacity': opacity
            }

        print(f"✨ {'Enhanced ' if enable_advanced else 'Basic '}subtitle settings applying...")
        if advanced_config:
            print(f"Effect: {effect_type}, Outline: {outline_size}px, Shadow: {shadow_size}px")

        # 5. Create enhanced subtitled video
        if enable_advanced:
            # Use enhanced subtitle system (subtitle.py needs to be updated)
            subtitled_video = create_subtitled_video(
                video_path=video_path,
                scene_descriptions=scene_descriptions,
                scene_times=scene_times,
                subtitle_config=subtitle_config,
                advanced_config=advanced_config
            )
        else:
            # Use existing system
            subtitled_video = create_subtitled_video(
                video_path=video_path,
                scene_descriptions=scene_descriptions,
                scene_times=scene_times,
                subtitle_config=subtitle_config
            )

        # 6. Create TTS video
        final_video = create_video_with_tts(
            subtitled_video,
            scene_descriptions,
            scene_times,
            lang=lang_code
        )

        # 7. Generate summary in selected language
        summary = summarize_with_ollama(scene_descriptions, lang=lang_code)

        # Add enhanced information
        if enable_advanced:
            summary += f"\n\n✨ Enhanced Subtitle Effects:\n"
            summary += f"- Effect: {effect_type}\n"
            summary += f"- Outline: {outline_size}px, Shadow: {shadow_size}px\n"
            summary += f"- Opacity: {opacity:.1f}\n"
            summary += f"- Position: {text_position}"

        # 8. Create transcript for RAG system (URLs only)
        rag_status = "RAG 系统不可用（仅限url）"
        chat_interface_visible = False

        if video_url and rag_system:
            try:
                print("🤖 为RAG 系统构建内容...")
                result = rag_system.process_with_rag(video_url, method="whisper", language=lang_code)

                if result.get("transcript") and result.get("rag_ready"):
                    current_transcript = result["transcript"]
                    rag_status = f"✅ 视频分析机器人准备好了！语言: {selected_lang}. 你可以在下面提问."
                    chat_interface_visible = True
                else:
                    rag_status = "❌ RAG 系统启动失败"

            except Exception as e:
                rag_status = f"❌ RAG 报错: {str(e)}"

        # 9. Clean up temp files
        try:
            os.remove(video_path)
        except:
            pass

        return final_video, summary, rag_status, gr.update(visible=chat_interface_visible), gr.update(visible=chat_interface_visible), gr.update(visible=chat_interface_visible)

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return None, error_msg, "❌ 错误，RAG 系统不可用", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def ask_question_about_video(question, chat_history):
    """Ask questions about the video"""
    global rag_system, current_transcript

    if not question.strip():
        return chat_history, ""

    if not rag_system or not current_transcript:
        response = "❌ RAG系统启动, 请先处理视频 或 设置聊天机器人."
        chat_history.append([question, response])
        return chat_history, ""

    try:
        # Soru-cevap
        result = rag_system.ask_question(question)

        if result.get("error"):
            response = f"❌ 错误: {result['error']}"
        else:
            response = result["answer"]

        chat_history.append([question, response])
        return chat_history, ""

    except Exception as e:
        response = f"❌ Q&A error: {str(e)}"
        chat_history.append([question, response])
        return chat_history, ""

def clear_chat():
    """Clear chat history"""
    return []

def process_srt_subtitles(video_input, youtube_url, tiktok_url, selected_lang, font_size, font_color, text_position, font_family,
                          effect_type, outline_size, shadow_size, opacity, enable_advanced):
    """Process video with SRT subtitles - Enhanced effects"""
    try:
        # 1. Determine video URL - Priority: TikTok > YouTube > Upload
        video_url = None
        if tiktok_url and tiktok_url.strip():
            video_url = tiktok_url.strip()
        elif youtube_url and youtube_url.strip():
            video_url = youtube_url.strip()
        elif isinstance(video_input, str) and (video_input.startswith(('http://', 'https://'))):
            video_url = video_input

        if not video_url:
            return None, "❌ SRT 字幕生成需要视频 URL (YouTube or TikTok). 请输入有效的URL."

        # 2. Convert language code
        lang_code = LANGUAGES[selected_lang]

        # 3. Prepare basic subtitle settings
        subtitle_config = {
            'font_size': font_size,
            'font_color': SUBTITLE_COLORS[font_color],
            'text_position': text_position.replace(' ', '_').lower() if text_position in SUBTITLE_POSITIONS.values() else list(SUBTITLE_POSITIONS.keys())[list(SUBTITLE_POSITIONS.values()).index(text_position)] if text_position in SUBTITLE_POSITIONS.values() else 'bottom',
            'font_family': SUBTITLE_FONTS[font_family]
        }

        # 4. Prepare advanced settings (if enabled)
        advanced_config = None
        if enable_advanced:
            # Find position key
            position_key = 'bottom'
            for key, value in SUBTITLE_POSITIONS.items():
                if value == text_position:
                    position_key = key
                    break

            # Find effect key
            effect_key = 'fade'
            for key, value in SUBTITLE_EFFECTS.items():
                if value == effect_type:
                    effect_key = key
                    break

            advanced_config = {
                'font_size': font_size,
                'font_color': SUBTITLE_COLORS[font_color],
                'text_position': position_key,
                'font_family': SUBTITLE_FONTS[font_family] or 'Arial Black',
                'effect_type': effect_key,
                'outline_size': outline_size,
                'shadow_size': shadow_size,
                'opacity': opacity
            }

        print(f"🎬 {'Enhanced ' if enable_advanced else ''}SRT Subtitle processing starting...")
        print(f"📹 URL: {video_url}")
        print(f"🌍 Language: {selected_lang} ({lang_code})")
        print(f"🎨 Basic settings: {subtitle_config}")
        if advanced_config:
            print(f"✨ Advanced settings: {advanced_config}")

        # 5. Process video with SRT
        success, output_video_path, srt_path, error_message = process_video_with_srt(
            video_url=video_url,
            subtitle_config=subtitle_config,
            language=lang_code,
            advanced_config=advanced_config
        )

        if success:
            # Create success message
            success_msg = f"✅ {'Enhanced ' if enable_advanced else ''}SRT Subtitled video created successfully!\n\n"
            success_msg += f"📹 Video: {os.path.basename(output_video_path)}\n"
            success_msg += f"📄 SRT file: {os.path.basename(srt_path) if srt_path else 'N/A'}\n"
            success_msg += f"🌍 Language: {selected_lang}\n"
            success_msg += f"🎨 Font: {font_size}px {font_color} - {text_position}\n"
            if enable_advanced:
                success_msg += f"✨ Effect: {effect_type}\n"
                success_msg += f"🖼️ Outline: {outline_size}px, Shadow: {shadow_size}px\n"
                success_msg += f"🔍 Opacity: {opacity:.1f}"

            if error_message and "successfully" in error_message:
                success_msg += f"\n\n{error_message}"

            return output_video_path, success_msg
        else:
            error_msg = f"❌ {'Enhanced ' if enable_advanced else ''}SRT subtitle creation failed!\n\n"
            if error_message:
                error_msg += f"Error: {error_message}\n\n"
            if srt_path:
                error_msg += f"📄 SRT file created: {os.path.basename(srt_path)}\n"
                error_msg += "💡 您可以手动将 SRT文件加载到 视频播放器中."

            return None, error_msg

    except Exception as e:
        error_msg = f"❌ Unexpected error during {'Enhanced ' if enable_advanced else ''}SRT processing: {str(e)}"
        return None, error_msg

# Gradio interface
def create_interface():
    # 导入RAG类
    initialize_rag_system()

    # 初始化一个前端页面
    with gr.Blocks(
        title="AI-SubtitleSum",
        theme=gr.themes.Soft(),
        css="""
        .main-container { max-width: 1200px; margin: 0 auto; }
        .video-section { border: 2px solid #e1e5e9; border-radius: 10px; padding: 20px; margin: 10px 0; }
        .chat-section { border: 2px solid #d4edda; border-radius: 10px; padding: 20px; margin: 10px 0; background-color: #f8f9fa; }
        .button-section { border: 2px solid #e1e5e9; border-radius: 10px; padding: 20px; margin: 10px 0; background-color: #fffbf0; }
        .status-box { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success-status { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .error-status { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
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
        """
    ) as interface:

        gr.Markdown(
            """
            # 🎥 智能新闻视频分析模块
            ### 人工智能视频字幕生成 & 智能聊天系统
            """,
            elem_classes="main-container"
        )

        with gr.Row():
            # 左-1 容器
            with gr.Column(scale=1):
                with gr.Group(elem_classes="video-section"):
                    gr.Markdown("### 📹 视频导入")

                    # Video input options
                    video_input = gr.Video(label="📁 上传视频文件")

                    with gr.Row():
                        youtube_url = gr.Textbox(
                            label="🎬 YouTube URL",
                            placeholder="https://www.youtube.com/watch?v=example",
                            scale=1
                        )
                        tiktok_url = gr.Textbox(
                            label="📱 TikTok URL",
                            placeholder="https://www.tiktok.com/@user/video/123456789",
                            scale=1
                        )

                    # 语言切换
                    language = gr.Dropdown(
                        choices=list(LANGUAGES.keys()),
                        value="English",
                        label="🌍 描述 & 音频语言"
                    )

                with gr.Group(elem_classes="video-section"):
                    gr.Markdown("### 🎨 字幕设置")

                    # Advanced mode toggle
                    enable_advanced = gr.Checkbox(
                        label="✨ 启用 高级字幕效果",
                        value=False,
                        info="动画,效果,轮廓和阴影设置"
                    )

                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("#### 🔤 基本配置")
                            font_size = gr.Slider(
                                minimum=20,
                                maximum=80,
                                value=40,
                                step=2,
                                label="📏 字体大小"
                            )
                            font_color = gr.Dropdown(
                                choices=list(SUBTITLE_COLORS.keys()),
                                value="Yellow",
                                label="🎨 字体颜色"
                            )
                            font_family = gr.Dropdown(
                                choices=list(SUBTITLE_FONTS.keys()),
                                value="Default",
                                label="🔤 字体类型"
                            )
                            text_position = gr.Dropdown(
                                choices=list(SUBTITLE_POSITIONS.values()),
                                value="Bottom Center",
                                label="📍 文本位置"
                            )

                        with gr.Column(scale=1, visible=False) as advanced_column:
                            gr.Markdown("#### ✨ Advanced Effects")
                            effect_type = gr.Dropdown(
                                choices=list(SUBTITLE_EFFECTS.values()),
                                value="Smooth Fade",
                                label="🎬 Animation Effect"
                            )
                            outline_size = gr.Slider(
                                minimum=0,
                                maximum=8,
                                value=3,
                                step=1,
                                label="🖼️ Outline Thickness (px)"
                            )
                            shadow_size = gr.Slider(
                                minimum=0,
                                maximum=8,
                                value=2,
                                step=1,
                                label="🌆 Shadow Size (px)"
                            )
                            opacity = gr.Slider(
                                minimum=0.1,
                                maximum=1.0,
                                value=1.0,
                                step=0.1,
                                label="🔍 Opacity"
                            )
                    # Control advanced settings visibility
                    enable_advanced.change(
                        fn=lambda x: gr.update(visible=x),
                        inputs=enable_advanced,
                        outputs=advanced_column
                    )



            # 右 - 1 - Outputs and Chat
            with gr.Column(scale=1):
                with gr.Group(elem_classes="video-section"):
                    gr.Markdown("### 📺 视频处理")
                    # Output video
                    output_video = gr.Video(label="处理结果")

                    # Summary text
                    summary_text = gr.Textbox(
                        label="📄 视频总结",
                        lines=4,
                        interactive=False
                    )

                # RAG Status
                rag_status = gr.Markdown(
                    "ℹ️ 请选择：处理视频🧭 或 启动机器人🤖",
                    elem_classes="status-box"
                )

                # Action buttons
                with gr.Group(elem_classes="button-section"):
                    gr.Markdown("### 🚀 启动")
                    gr.Markdown("*对导入视频进行下述操作*")

                    with gr.Row():
                        process_btn = gr.Button(
                            "🎬 处理内容\n(AI 总结 + TTS)",
                            variant="primary",
                            size="lg",
                            scale=1
                        )
                        srt_btn = gr.Button(
                            "📝 SRT字幕生成\n(Whisper 转录)",
                            variant="primary",
                            size="lg",
                            scale=1
                        )
                        setup_chatbot_btn = gr.Button(
                            "🤖 启动机器人\n(视频内容交流)",
                            variant="primary",
                            size="lg",
                            scale=1
                        )

                # Chat Interface
                with gr.Group(elem_classes="chat-section", visible=False) as chat_section:
                    gr.Markdown("### 🤖 Video Chatbot")
                    gr.Markdown("*Ask any questions about the video content*")

                    chatbot = gr.Chatbot(
                        label="Chat History",
                        height=300,
                        show_label=True,
                        visible=False
                    )

                    with gr.Row(visible=False) as chat_input_row:
                        question_input = gr.Textbox(
                            label="Your Question",
                            placeholder="Ask a question about the video...",
                            scale=4,
                            lines=1
                        )
                        ask_btn = gr.Button("📤 Send", scale=1)
                        clear_btn = gr.Button("🗑️ Clear", scale=1)

        # Process button click event
        process_btn.click(
            fn=process_video_with_lang,
            inputs=[
                video_input,
                youtube_url,
                tiktok_url,
                language,
                font_size,
                font_color,
                text_position,
                font_family,
                effect_type,
                outline_size,
                shadow_size,
                opacity,
                enable_advanced
            ],
            outputs=[
                output_video,
                summary_text,
                rag_status,
                chat_section,
                chatbot,
                chat_input_row
            ]
        )

        # Setup chatbot only button click event
        setup_chatbot_btn.click(
            fn=setup_chatbot_only,
            inputs=[video_input, youtube_url, tiktok_url, language],
            outputs=[
                rag_status,
                chat_section,
                chatbot,
                chat_input_row
            ]
        )

        # SRT subtitle button click event
        srt_btn.click(
            fn=process_srt_subtitles,
            inputs=[
                video_input,
                youtube_url,
                tiktok_url,
                language,
                font_size,
                font_color,
                text_position,
                font_family,
                effect_type,
                outline_size,
                shadow_size,
                opacity,
                enable_advanced
            ],
            outputs=[
                output_video,
                summary_text
            ]
        )

        # Chat events
        ask_btn.click(
            fn=ask_question_about_video,
            inputs=[question_input, chatbot],
            outputs=[chatbot, question_input]
        )

        question_input.submit(
            fn=ask_question_about_video,
            inputs=[question_input, chatbot],
            outputs=[chatbot, question_input]
        )

        clear_btn.click(
            fn=clear_chat,
            outputs=chatbot
        )

        # Instructions 按钮 + 弹出说明
        button_text = r'使用说明'
        window_text = r'''
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
        '''

        open_btn = gr.Button(button_text)
        with gr.Group(visible=False, elem_id="modal") as modal:
          # 透明按钮铺满遮罩，用于点击空白处关闭
          backdrop = gr.Button("", elem_id="backdrop")

          # 弹窗内容卡片
          with gr.Column(elem_classes=["modal-card"]):
            gr.Markdown(window_text)
            close_btn = gr.Button("关闭", variant="secondary")

        # 打开/关闭 弹窗
        open_btn.click(lambda: gr.update(visible=True), outputs=modal)
        close_btn.click(lambda: gr.update(visible=False), outputs=modal)
        backdrop.click(lambda: gr.update(visible=False), outputs=modal)

    return interface


if __name__ == "__main__":
    interface = create_interface()
    interface.launch(share=False, server_port=5019, debug=True)
