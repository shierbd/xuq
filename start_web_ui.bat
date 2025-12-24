@echo off
echo ========================================
echo 词根聚类需求挖掘系统 - Web UI
echo ========================================
echo.

cd /d "%~dp0"

echo 正在启动Web UI...
echo.
echo 启动后请访问: http://localhost:8501
echo 按 Ctrl+C 可以停止服务
echo.
echo ========================================

streamlit run web_ui.py

pause
