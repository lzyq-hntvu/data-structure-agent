# Data Structure Agent - Claude 开发指南

## 项目概述

数据结构试题ETL处理工具，用于从PDF试卷中提取题目并进行结构化处理。

## 架构设计

### 模块职责

| 模块 | 职责 | 关键类/函数 |
|------|------|------------|
| `config.py` | 配置管理 | `ETLConfig` |
| `extractor.py` | PDF文本提取 | `PDFExtractor.extract()` |
| `parser.py` | 试卷结构解析 | `ExamParser.identify_sections()`, `ExamParser.extract_questions()` |
| `tagger.py` | 标签和难度评估 | `QuestionTagger.assign_tags()`, `QuestionTagger.get_difficulty()` |
| `analyzer.py` | 统计分析 | `StatisticsAnalyzer.generate()` |
| `exporter.py` | CSV导出 | `CSVExporter.save()` |
| `main.py` | 主入口和CLI | `main()` |

### 数据流

```
PDF文件 → PDFExtractor → 页面文本列表
                           ↓
                    ExamParser → sections → questions
                           ↓
                    QuestionTagger → tagged_questions
                           ↓
                    CSVExporter → CSV文件
                           ↓
                    StatisticsAnalyzer → 统计报告
```

## 开发规范

### 添加新标签

编辑 `config.py` 中的 `TAG_KEYWORDS` 字典：

```python
TAG_KEYWORDS = {
    'NewTag': ['关键词1', '关键词2', ...],
    # ... 其他标签
}
```

### 添加新难度映射

编辑 `config.py` 中的 `DIFFICULTY_MAP` 字典：

```python
DIFFICULTY_MAP = {
    '新题型': 'Hard',  # 或 'Simple', 'Medium'
    # ... 其他映射
}
```

### 调整题目提取模式

编辑 `config.py` 中的 `QUESTION_PATTERNS` 列表，按优先级添加正则表达式。

### 扩展分析功能

在 `analyzer.py` 的 `StatisticsAnalyzer` 类中添加新方法，然后在 `main.py` 中调用。

## 测试

### 运行测试

```bash
# 基本功能测试
python main.py

# 指定PDF测试
python main.py --pdf data/input/转\ Word_数据结构卷一.pdf --verbose
```

### 验证输出一致性

对比新旧输出确保重构没有破坏功能：

```bash
# 运行原脚本（如果已备份）
python ~/exdata_etl_processor.py.bak

# 运行新脚本
python main.py

# 对比CSV输出
diff ~/data_structure_exam_analysis.csv data/output/exam_analysis.csv
```

## 已知限制

1. PDF格式依赖：需要PDF具有清晰的文本结构
2. 试卷格式依赖：依赖特定的试卷格式（卷、题型标识）
3. 标签准确性：基于关键词匹配，可能存在误判

## 后续优化方向

1. **单元测试**: 使用pytest为每个模块编写测试
2. **数据验证**: 使用pydantic进行数据模型验证
3. **批量处理**: 支持多个PDF文件同时处理
4. **可视化报告**: 使用matplotlib生成统计图表
5. **配置文件**: 支持YAML/JSON配置文件
