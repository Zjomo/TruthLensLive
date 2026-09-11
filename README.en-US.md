# TruthLensLive V2.0

[🇨🇳 中文](README.zh-CN.md) | [🇬🇧 English](README.en-US.md)

A comprehensive full-stack application for real-time rumor detection and news verification. Built with modern web technologies and AI-powered analysis to combat misinformation.

![License](https://img.shields.io/github/license/Zjomo/TruthLensLive?style=flat-square)
![Language](https://img.shields.io/github/languages/top/Zjomo/TruthLensLive?style=flat-square)

## 🌟 Features

- **Real-Time News Feed**: Live streaming of news updates using Server-Sent Events (SSE)
- **Rumor Detection**: AI-powered heuristic scoring system to identify potentially misleading content
- **RAG + Multimodal Fusion**: Text / image / audio / video detection with evidence-chain explanations
- **Multi-Source Aggregation**: RSS feed integration with automatic subscription conversion
- **Interactive Dashboards**: Visual analytics with charts and statistics
- **Admin Panel**: Comprehensive management interface with Element Plus UI
- **Multi-Language Support**: Internationalization support for global users
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Docker Support**: Containerized deployment for easy scaling

## 🎬 Demo Showcase

### RAG Real-time Fake News Detection

Input a news headline and content; the system returns a credibility score, BERT detection result, AI analysis and a downloadable full log in seconds.

![RAG detection UI](docs/images/rag-detect-ui.png)

### Multimodal Video Detection

End-to-end pipeline from "news video + text" to "classification result, text emotion and audio emotion", with light / dark themes.

<table>
  <tr>
    <td width="50%"><img src="docs/images/multimodal-input-light.jpeg" alt="Multimodal detection - input (light)"/></td>
    <td width="50%"><img src="docs/images/multimodal-video-dark.jpeg" alt="Multimodal detection - video processing (dark)"/></td>
  </tr>
  <tr>
    <td colspan="2"><img src="docs/images/multimodal-result.jpeg" alt="Multimodal detection - results & analysis"/></td>
  </tr>
</table>

### Detection Case Examples

Real-world multimodal fake-news samples used in evaluation (video + multilingual captions):

<table>
  <tr>
    <td width="50%"><img src="docs/images/example-video-zh.png" alt="Case: staged breaking-news video"/></td>
    <td width="50%"><img src="docs/images/example-video-multilingual.png" alt="Case: multilingual edited video"/></td>
  </tr>
</table>

### Project Demo Video

Full system walkthrough (screen recording, ~91 MB, in-repo path):

> 🎥 [`Material/我的刀盾_TruthLensLive—基于RAG-多模态融合的虚假新闻实时检测系统_项目视频.mp4`](Material/我的刀盾_TruthLensLive—基于RAG-多模态融合的虚假新闻实时检测系统_项目视频.mp4)
>
> 💡 Tip: GitHub renders large videos poorly. Upload to GitHub Releases / Bilibili / YouTube and replace with an online playback link.

## 🏗️ Model Architecture & Performance

### FakingRecipe Multimodal Framework

Material selection-aware + editing-aware modeling over audio, title/transcript and key frames.

<table>
  <tr>
    <td width="60%"><img src="docs/images/architecture-fakingrecipe.png" alt="FakingRecipe framework"/></td>
    <td width="40%"><img src="docs/images/llm-label-propagation.png" alt="LLM label propagation"/></td>
  </tr>
</table>

### Benchmark Results

EQ-Former / EQFFG-Trans reach state-of-the-art F1 on both Weibo and Tweet datasets.

<table>
  <tr>
    <td width="50%"><img src="docs/images/metrics-weibo-multimodal.png" alt="Weibo multimodal sentiment fusion"/></td>
    <td width="50%"><img src="docs/images/metrics-tweet-multimodal.png" alt="Tweet multimodal sentiment fusion"/></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/metrics-weibo-fuzzy-transformer.png" alt="Weibo fuzzy Transformer"/></td>
    <td width="50%"><img src="docs/images/metrics-tweet-fuzzy-transformer.png" alt="Tweet fuzzy Transformer"/></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/radar-weibo-fuzzy-transformer.png" alt="Weibo radar chart"/></td>
    <td width="50%"><img src="docs/images/radar-tweet-fuzzy-transformer.png" alt="Tweet radar chart"/></td>
  </tr>
</table>

## 🏗️ Tech Stack

### Frontend (49.5% Vue)
- **Vue 3**: Modern reactive UI framework
- **TypeScript**: Type-safe development
- **Vite**: Lightning-fast build tool
- **Element Plus**: Enterprise UI component library
- **Chart.js**: Data visualization
- **Tailwind CSS**: Utility-first styling
- **Pinia**: State management
- **Vue Router**: Client-side routing

### Backend (17.6% Python)
- **Flask**: Lightweight web framework
- **SQLite**: Lightweight database
- **RSS Feeds**: News source aggregation
- **RSSHub**: Subscription conversion layer

### Additional Technologies
- **HTML/SCSS**: Styling and markup
- **Jupyter Notebooks**: Data analysis and experimentation

## 📦 Project Structure

```
TruthLensLive/
├── src/                      # Vue 3 frontend source
├── public/                   # Static assets
├── modules/                  # Feature modules
│   ├── Index/               # Real-time rumor detection system
│   └── ClashLinux/          # Linux proxy setup module
├── mock/                    # Mock data for development
├── locales/                 # i18n translations
├── types/                   # TypeScript type definitions
├── utils/                   # Utility functions
├── package.json             # Node dependencies
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript configuration
├── Dockerfile              # Container configuration
└── requirements_.txt       # Python dependencies
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18.18.0 or higher
- pnpm 9.0 or higher
- Python 3.7+ (for backend services)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Zjomo/TruthLensLive.git
cd TruthLensLive
```

2. **Install frontend dependencies**
```bash
pnpm install
```

3. **Install Python dependencies**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements_.txt
```

### Development

1. **Start the frontend development server**
```bash
pnpm dev
```
The application will be available at `http://localhost:5173`

2. **Start the backend services**
```bash
python modules/Index/app.py
# Backend will run on http://127.0.0.1:5000
```

### Production Build

```bash
pnpm build
pnpm preview
```

## 🐳 Docker Deployment

```bash
docker build -t truthlenslive:latest .
docker run -p 5173:5173 -p 5000:5000 truthlenslive:latest
```

## 📋 Available Scripts

```bash
# Development
pnpm dev              # Start dev server with debug logging
pnpm serve           # Alias for dev

# Building
pnpm build           # Production build
pnpm build:staging   # Staging build
pnpm report          # Build with visualization report
pnpm preview         # Preview production build

# Code Quality
pnpm lint            # Run all linters (ESLint, Prettier, Stylelint)
pnpm lint:eslint     # Run ESLint
pnpm lint:prettier   # Format code with Prettier
pnpm lint:stylelint  # Check styles

# Type Checking
pnpm typecheck       # TypeScript type checking

# Maintenance
pnpm clean:cache     # Clear all caches and reinstall dependencies
```

## 🔄 Real-Time Rumor Detection

The backend uses a Flask-based system with RSS feed integration:

```bash
# Configuration through environment variables
export DB_PATH=sqlite:///rumor.db
export POLL_INTERVAL=60  # seconds
export MAX_ITEMS_PER_FEED=30
```

**Key Features:**
- Automated RSS feed polling
- Local subscription conversion via RSSHub
- Heuristic rumor tendency scoring
- Server-Sent Events for real-time updates
- Multiple data source support

For detailed backend documentation, see [modules/Index/README.md](modules/Index/README.md)

## 🔧 Configuration

### Frontend Environment Variables

Create `.env.local` file:
```env
VITE_API_BASE_URL=http://localhost:5000
VITE_ENABLE_DEBUG=true
```

### Backend Configuration

Supported environment variables:
- `DB_PATH`: SQLite database connection string
- `POLL_INTERVAL`: RSS feed polling interval in seconds
- `MAX_ITEMS_PER_FEED`: Maximum items to fetch per feed

## 📊 Features Overview

### Dashboard
- Real-time news feed display
- Rumor detection metrics
- Source distribution charts
- Rumor ratio visualization

### Admin Panel
- News source management
- Feed configuration
- Detection rule adjustment
- User management

### API
- RESTful endpoints for news retrieval
- WebSocket support for real-time updates
- Rumor scoring endpoints
- Analytics data export

## 🌐 Internationalization

The application supports multiple languages through i18n:
- English (en-US)
- Chinese Simplified (zh-CN)

To add a new language, update the locale files in the `locales/` directory.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚠️ Important Notes

1. **Educational Purpose**: This project is primarily for learning and research on real-time data processing and AI applications.

2. **Rumor Detection**: The current heuristic-based scoring is for demonstration purposes. For production use, integrate trained ML models with labeled datasets.

3. **RSS Feed Sources**: For domestic (Chinese) users, it's recommended to set up a self-hosted RSSHub instance as the aggregation layer for reliable feed access.

4. **Multi-Instance Deployment**: For production with multiple instances, replace SSE with a message broker (Redis pub/sub) for proper event broadcasting.

## 🐛 Troubleshooting

### Development Server Issues
```bash
# Clear cache and reinstall
pnpm clean:cache

# Check Node version
node --version  # Should be 18.18.0 or higher
```

### RSS Feed Connection Issues
- Verify RSSHub URL is accessible
- Check internet connectivity
- Review `FEED_URLS` configuration
- Monitor polling interval settings

### Port Already in Use
```bash
# Change frontend port
PORT=3000 pnpm dev

# Change backend port
python -c "import os; os.environ['FLASK_PORT'] = '5001'; exec(open('modules/Index/app.py').read())"
```

## 📚 Additional Resources

- [Vue 3 Documentation](https://vuejs.org)
- [Element Plus](https://element-plus.org)
- [Flask Documentation](https://flask.palletsprojects.com)
- [RSSHub Documentation](https://docs.rsshub.app/)
- [Vite Documentation](https://vitejs.dev)

## 📞 Support

For issues, questions, or suggestions:
1. Check existing [Issues](https://github.com/Zjomo/TruthLensLive/issues)
2. Create a new issue with detailed information
3. Include error logs and reproduction steps

---

**Made with ❤️ by [Zjomo](https://github.com/Zjomo)**
