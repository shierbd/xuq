@echo off
REM UTF-8环境下运行Phase2聚类脚本
REM 使用方法：run_clustering_utf8.bat [参数]

REM 设置UTF-8环境
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
chcp 65001 >nul 2>&1

REM 运行聚类脚本（传递所有参数）
python scripts\run_phase2_clustering.py %*
