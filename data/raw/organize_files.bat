@echo off
REM 数据文件整理脚本
REM 将混合的数据文件分类到对应目录

echo 开始整理数据文件...

REM 创建目录
mkdir "D:\xiangmu\词根聚类需求挖掘\data\raw\dropdown" 2>nul
mkdir "D:\xiangmu\词根聚类需求挖掘\data\raw\related_search" 2>nul

echo.
echo 请按照以下步骤操作：
echo.
echo 1. SEMRUSH数据 - 保留在当前目录
echo    路径：D:\xiangmu\词根聚类需求挖掘\data\raw\semrush\
echo.
echo 2. 下拉词数据 - 移动到：
echo    路径：D:\xiangmu\词根聚类需求挖掘\data\raw\dropdown\
echo.
echo 3. 相关搜索数据 - 移动到：
echo    路径：D:\xiangmu\词根聚类需求挖掘\data\raw\related_search\
echo.
echo 如果所有文件都是SEMRUSH数据，无需移动。
echo.
echo 完成后，程序会自动读取每个目录的第一个CSV文件。
echo.
pause
