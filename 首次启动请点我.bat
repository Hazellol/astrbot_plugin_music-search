@echo off
chcp 65001
echo 正在检查是否已安装 requests 库...

python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo 未安装 requests 库，正在安装...
    python -m pip install requests
    echo requests 库安装完成
) else (
    echo requests 库已安装，跳过安装。
)

pause