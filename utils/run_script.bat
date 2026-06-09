@echo off
set "PYTHON_PATH_1=F:/0_MyProject/Anaconda/envs/MondayV2/python.exe"
set "PYTHON_PATH_2=F:/0_MyProject/Anaconda/envs/yolov5/python.exe"
set "PYTHON_PATH_3=F:/0_MyProject/Anaconda/envs/llama/python.exe"


REM 系统启动
cd /d "F:/0_MyProject/BambooMuseum"
start "pnpm_dev" cmd /k "pnpm dev"


REM 主页
cd /d "F:/0_MyProject/BambooMuseum/utils/index"
start "Index" cmd /k "%PYTHON_PATH_1% app.py"


REM 电子展厅
cd /d "F:/0_MyProject/BambooMuseum/utils/exhitbitshow"
start "Exihibit" cmd /k "%PYTHON_PATH_1% app.py"


REM 展厅数据库
cd /d "F:/0_MyProject/BambooMuseum/utils/Exhibit_Intr"
start "Mysql" cmd /k "%PYTHON_PATH_1% app.py"


REM 数据库API
cd /d "F:/0_MyProject/BambooMuseum/utils/Mysql_API"
start "MysqlAPI" cmd /k "%PYTHON_PATH_1% main.py"


REM 小智交互助手
cd /d "F:/0_MyProject/BambooMuseum/utils/py-xiaozhi-main"
start "Xiaozhi" cmd /k "%PYTHON_PATH_1% app.py"


REM 火灾检测
cd /d "F:/0_MyProject/BambooMuseum/utils/Fire_Detect"
start "FireDetect" cmd /k "%PYTHON_PATH_2% app.py"


REM 跌倒检测
cd /d "F:/0_MyProject/BambooMuseum/utils/Fall_Detect"
start "FallDetect" cmd /k "%PYTHON_PATH_2% app.py"


REM 人脸检测
cd /d "F:/0_MyProject/BambooMuseum/utils/Face_Detect"
start "FaceDetect" cmd /k "%PYTHON_PATH_2% app.py"


REM 人脸识别
cd /d "F:/0_MyProject/BambooMuseum/utils/Face_recognition"
start "FaceRec" cmd /k "%PYTHON_PATH_3% main.py"










