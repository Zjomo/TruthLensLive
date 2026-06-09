@echo off
set "PYTHON_PATH=F:/0_MyProject/Anaconda/envs/xtuner-env/python.exe"


REM 系统启动
cd /d "F:/0_MyProject/TruthLensLive"
start "pnpm_dev" cmd /k "pnpm dev"


REM 单模态虚假新闻检测（主页）
cd /d "F:/0_MyProject/TruthLensLive/modules/Index"
start "Index" cmd /k "%PYTHON_PATH% app.py"


REM RAG单模态虚假新闻检测
cd /d "F:/0_MyProject/TruthLensLive/modules/RagDetect"
start "RagDetect" cmd /k "%PYTHON_PATH% main.py"


REM 智能视频分析模块
cd /d "F:/0_MyProject/TruthLensLive/modules/MultiDM"
start "MultiDM" cmd /k "%PYTHON_PATH% app.py"


REM 多模态虚假新闻视频检测
cd /d "F:/0_MyProject/TruthLensLive/modules/MultiFakeDetect"
start "MultiFakeDetect" cmd /k "%PYTHON_PATH% app.py"
