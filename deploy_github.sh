#!/bin/bash
# GitHub 仓库部署脚本
# 用法: ./deploy_github.sh <仓库名称>

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   GitHub 仓库部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否安装了 gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ 未安装 GitHub CLI (gh)${NC}"
    echo "请先安装: https://cli.github.com/"
    exit 1
fi

# 检查是否登录
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  需要先登录 GitHub${NC}"
    gh auth login
fi

# 获取仓库名称
if [ -z "$1" ]; then
    # 尝试从当前目录名获取
    REPO_NAME=$(basename "$SCRIPT_DIR")
    echo -e "${YELLOW}未指定仓库名，使用当前目录名: ${REPO_NAME}${NC}"
    read -p "是否使用此名称? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        read -p "请输入仓库名称: " REPO_NAME
        if [ -z "$REPO_NAME" ]; then
            echo -e "${RED}❌ 仓库名称不能为空${NC}"
            exit 1
        fi
    fi
else
    REPO_NAME="$1"
fi

# 获取仓库描述
DEFAULT_DESC="通用试题ETL处理工具 - 支持多学科的试卷分析系统"
read -p "请输入仓库描述 (默认: ${DEFAULT_DESC}): " REPO_DESC
REPO_DESC="${REPO_DESC:-$DEFAULT_DESC}"

# 确认信息
echo ""
echo -e "${GREEN}仓库信息:${NC}"
echo "  名称: ${REPO_NAME}"
echo "  描述: ${REPO_DESC}"
echo "  可见性: public"
echo ""
read -p "确认创建并推送? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z "$REPLY" ]]; then
    echo "取消操作"
    exit 0
fi

# 创建仓库
echo ""
echo -e "${YELLOW}📦 正在创建 GitHub 仓库...${NC}"
gh repo create "${REPO_NAME}" \
    --public \
    --description "${REPO_DESC}" \
    --source="$SCRIPT_DIR" \
    --remote=origin \
    --push 2>/dev/null || {
    # 如果仓库已存在，只添加远程
    echo -e "${YELLOW}⚠️  仓库可能已存在，尝试添加远程...${NC}"
    gh repo view "${REPO_NAME}" &> /dev/null || true
    git remote add origin "https://github.com/huyuming/${REPO_NAME}.git" 2>/dev/null || true
    git remote set-url origin "https://github.com/huyuming/${REPO_NAME}.git" 2>/dev/null || true
}

# 推送代码
echo ""
echo -e "${YELLOW}📤 正在推送代码到 GitHub...${NC}"
git push -u origin master

# 等待 GitHub 处理
sleep 2

# 获取仓库 URL
REPO_URL=$(gh repo view "${REPO_NAME}" --json url -q .url)

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "仓库地址: ${REPO_URL}"
echo ""
echo -e "后续操作:"
echo -e "  git push                    # 推送更新"
echo -e "  gh repo view                # 查看仓库信息"
echo -e "  gh issue create             # 创建 Issue"
echo ""
