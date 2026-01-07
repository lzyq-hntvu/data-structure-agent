#!/bin/bash
# GitHub 仓库部署脚本 (简化版 - 不需要 gh CLI)
#
# 使用步骤:
# 1. 在 GitHub 上手动创建新仓库 (https://github.com/new)
# 2. 运行此脚本: ./deploy_github_simple.sh <你的用户名>/<仓库名>

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   GitHub 仓库推送脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查参数
if [ -z "$1" ]; then
    echo -e "${YELLOW}用法: $0 <GitHub用户名/仓库名>${NC}"
    echo ""
    echo "示例:"
    echo "  $0 huyuming/exam-etl-tool"
    echo ""
    echo "步骤:"
    echo "  1. 在 GitHub 上创建新仓库: https://github.com/new"
    echo "  2. 运行此脚本推送代码"
    echo ""
    exit 1
fi

REPO_PATH="$1"
REPO_URL="git@github.com:${REPO_PATH}.git"

echo "仓库地址: ${REPO_URL}"
echo ""

# 检查是否已有远程
if git remote get-url origin &> /dev/null; then
    echo -e "${YELLOW}检测到已存在的远程仓库${NC}"
    git remote set-url origin "${REPO_URL}"
else
    git remote add origin "${REPO_URL}"
fi

# 切换到 main 分支（现代标准）
git branch -M main

echo -e "${YELLOW}正在推送到 GitHub...${NC}"
git push -u origin main

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ 推送完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "仓库地址: https://github.com/${REPO_PATH}"
echo ""
