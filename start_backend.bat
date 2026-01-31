@echo off
set DEEPSEEK_API_KEY=sk-fb8318ee2b3c45a39ba642843ed8a287
cd /d "D:\xiangmu\词根聚类需求挖掘"
python -m uvicorn backend.main:app --reload --port 8002
