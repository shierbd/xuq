#!/bin/bash
# 推送前的数据安全检查脚本
# 使用方法: bash check_before_push.sh

echo "=========================================="
echo "   Git 推送前数据安全检查"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_passed=true

# 1. 检查暂存区是否有CSV文件
echo "1. 检查 CSV/Excel 文件..."
csv_files=$(git diff --cached --name-only | grep -E '\.(csv|xlsx|xls)$')
if [ -z "$csv_files" ]; then
    echo -e "${GREEN}✓ 没有CSV/Excel文件将被推送${NC}"
else
    echo -e "${RED}✗ 发现CSV/Excel文件:${NC}"
    echo "$csv_files"
    check_passed=false
fi
echo ""

# 2. 检查数据目录
echo "2. 检查数据目录..."
data_files=$(git diff --cached --name-only | grep -E '^(data|原始词)/')
if [ -z "$data_files" ]; then
    echo -e "${GREEN}✓ 没有数据目录文件将被推送${NC}"
else
    echo -e "${RED}✗ 发现数据目录文件:${NC}"
    echo "$data_files"
    check_passed=false
fi
echo ""

# 3. 检查 .env 文件
echo "3. 检查环境变量文件..."
env_files=$(git diff --cached --name-only | grep -E '^\.env$')
if [ -z "$env_files" ]; then
    echo -e "${GREEN}✓ .env 文件不会被推送${NC}"
else
    echo -e "${RED}✗ 发现 .env 文件将被推送！${NC}"
    check_passed=false
fi
echo ""

# 4. 检查数据库文件
echo "4. 检查数据库文件..."
db_files=$(git diff --cached --name-only | grep -E '\.(db|sqlite|sqlite3)$')
if [ -z "$db_files" ]; then
    echo -e "${GREEN}✓ 没有数据库文件将被推送${NC}"
else
    echo -e "${RED}✗ 发现数据库文件:${NC}"
    echo "$db_files"
    check_passed=false
fi
echo ""

# 5. 显示将要推送的文件
echo "5. 将要推送的文件列表:"
echo "----------------------------------------"
git diff --cached --name-only
echo "----------------------------------------"
echo ""

# 最终结果
echo "=========================================="
if [ "$check_passed" = true ]; then
    echo -e "${GREEN}✓ 安全检查通过！可以安全推送。${NC}"
    echo ""
    echo "执行以下命令推送:"
    echo "  git push"
else
    echo -e "${RED}✗ 安全检查失败！发现敏感数据。${NC}"
    echo ""
    echo "请执行以下命令移除敏感文件:"
    echo "  git reset HEAD <文件路径>"
    echo ""
    echo "或者重置所有暂存区:"
    echo "  git reset HEAD"
fi
echo "=========================================="
