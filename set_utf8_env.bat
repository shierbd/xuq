@echo off
REM 设置Python环境变量以强制使用UTF-8编码
REM 在运行任何Python脚本之前执行此批处理文件

echo 设置Python UTF-8环境变量...

REM 设置Python强制UTF-8模式（Python 3.7+）
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM 设置Windows控制台代码页为UTF-8
chcp 65001 >nul 2>&1

echo.
echo ========================================
echo  Python UTF-8环境已设置
echo ========================================
echo  PYTHONIOENCODING=%PYTHONIOENCODING%
echo  PYTHONUTF8=%PYTHONUTF8%
echo  控制台代码页: UTF-8 (65001)
echo ========================================
echo.
echo 提示: 这些设置只在当前命令行窗口有效
echo 建议将这些环境变量添加到系统环境变量中
echo.
