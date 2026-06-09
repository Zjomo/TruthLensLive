@echo off
set "PYTHON_PATH=F:\0_MyProject\Anaconda\envs\MondayV2\python.exe"
set "PYTHON_PATH_2=F:\0_MyProject\Anaconda\envs\Movies\python.exe"

REM 系统启动
cd /d "F:\0_My_Project\BambooMuseum"
start "pnpm_dev" cmd /k "pnpm dev"

REM 启动 -- 主页模块
cd /d "F:\0_My_Project\BambooMuseum\utils\index"
start "Index" cmd /k "%PYTHON_PATH% app.py"

REM 启动 -- 人脸识别模块
cd /d "E:\0_My_Project\Face_recognition"
start "Face_recognition" cmd /k "%PYTHON_PATH% main.py"

REM 启动 --  智能交互助手模块
cd /d "E:\0_My_Project\AI_History_Server\py-xiaozhi-main"
start "Xiaozhi" cmd /k "%PYTHON_PATH% app.py"

REM 启动 -- 展品文件上传模块
cd /d "E:\0_My_Project\AI_History_Server\Exhibit_Intr"
start "Exhibit_Introduce" cmd /k "%PYTHON_PATH% app.py"

REM 启动 -- 数据库模块
cd /d "E:\0_My_Project\Mysql_API"
start "Mysql_API" cmd /k "%PYTHON_PATH% main.py"

REM 启动 -- 数据库模块
cd /d "F:\0_My_Project\BambooMuseum\utils\exhitbitshow"
start "Exhitibit_Show" cmd /k "%PYTHON_PATH% app.py"


echo All scripts have been started.
pause
