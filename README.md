# 数据结构试题ETL处理工具

从PDF试卷中提取题目，自动打标签和难度评估，导出结构化CSV数据。

## 功能特性

- 📖 **PDF提取**: 自动从PDF试卷中提取文本内容
- 🏷️ **智能分类**: 基于关键词自动识别知识点标签
- 📊 **难度评估**: 根据题型自动评估题目难度
- 📈 **统计分析**: 生成多维度统计分析报告
- 🎯 **命令行支持**: 灵活的CLI参数配置

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 基本用法

使用默认配置（需先将PDF放入 `data/input/` 目录）：

```bash
python main.py
```

### 指定文件

```bash
# 指定PDF文件
python main.py --pdf /path/to/exam.pdf

# 指定输出文件
python main.py --output data/output/result.csv

# 同时指定输入和输出
python main.py -p input.pdf -o output.csv
```

### 详细日志

```bash
python main.py --verbose
```

## 项目结构

```
.
├── main.py          # 主入口（命令行接口）
├── config.py        # 配置管理
├── extractor.py     # PDF提取模块
├── parser.py        # 试卷解析模块
├── tagger.py        # 标签和难度评估
├── analyzer.py      # 统计分析模块
├── exporter.py      # CSV导出模块
├── requirements.txt # 依赖列表
├── .env.example     # 环境变量示例
└── data/
    ├── input/       # 输入PDF存放
    └── output/      # 输出CSV存放
```

## 输出说明

### CSV文件格式

| 列名 | 说明 |
|------|------|
| Paper_ID | 试卷编号（卷一、卷二等） |
| Question_Type | 题型（选择题、填空题等） |
| Question_Number | 题号 |
| Content | 题目内容 |
| Tag | 知识点标签（多个标签用逗号分隔） |
| Difficulty | 难度等级（Simple/Medium/Hard） |

### 知识点标签

- **Tree**: 二叉树、遍历、哈夫曼等
- **Graph**: 图、邻接矩阵、最短路径等
- **Sort_Search**: 排序、查找、哈希等
- **Linear**: 链表、栈、队列等
- **Complexity**: 时间复杂度、空间复杂度

## 配置说明

复制 `.env.example` 为 `.env` 并按需修改：

```bash
cp .env.example .env
```

可配置项：
- `PDF_PATH`: 默认PDF文件路径
- `OUTPUT_CSV`: 默认输出CSV路径
- `MIN_CONTENT_LENGTH`: 题目最小字符数
- `MAX_CONTENT_LENGTH`: 题目最大字符数
- `LOG_LEVEL`: 日志级别（INFO/DEBUG/WARNING等）
