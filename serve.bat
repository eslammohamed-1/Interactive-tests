@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo فتح المتصفح على: http://127.0.0.1:8080
echo اضغط Ctrl+C لإيقاف السيرفر
python -m http.server 8080
