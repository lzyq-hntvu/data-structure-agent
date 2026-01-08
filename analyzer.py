#!/usr/bin/env python3
"""
统计分析模块
生成试题数据的统计报告
"""
import logging
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from config import ETLConfig


class StatisticsAnalyzer:
    """统计分析器"""

    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, self.config.log_level))
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _prepare_data(self, df: pd.DataFrame) -> tuple:
        """准备统计数据"""
        # 展开 Tag 列
        all_tags = []
        for _, row in df.iterrows():
            for tag in row['Tag'].split(', '):
                all_tags.append({
                    'Tag': tag.strip(),
                    'Difficulty': row['Difficulty'],
                    'Paper': row['Paper_ID']
                })
        tag_df = pd.DataFrame(all_tags)

        # 计算统计表
        cross_tab = pd.crosstab(tag_df['Tag'], tag_df['Difficulty'], margins=True)
        paper_stats = df.groupby('Paper_ID').size().sort_index()
        difficulty_dist = df['Difficulty'].value_counts()
        question_type_dist = df['Question_Type'].value_counts().head(10)
        paper_tag = pd.crosstab(tag_df['Paper'], tag_df['Tag'])

        return cross_tab, paper_stats, difficulty_dist, question_type_dist, paper_tag

    def generate(self, df: pd.DataFrame, export: bool = True):
        """
        生成统计报表

        Args:
            df: 题目数据框
            export: 是否导出报告文件
        """
        # 准备数据
        cross_tab, paper_stats, difficulty_dist, question_type_dist, paper_tag = self._prepare_data(df)

        # 打印到终端
        print("\n" + "="*70)
        print("📊 统计分析报告")
        print("="*70)

        print("\n【知识点标签 × 难度 交叉统计】")
        print(cross_tab)

        print("\n【各分卷题目分布】")
        print(paper_stats)

        print("\n【难度分布】")
        print(difficulty_dist)

        print("\n【题型分布 (Top 10)】")
        print(question_type_dist)

        print("\n【各分卷的知识点分布】")
        print(paper_tag)

        # 导出报告文件
        if export:
            self.export_txt(df, cross_tab, paper_stats, difficulty_dist, question_type_dist, paper_tag)
            self.export_html(df, cross_tab, paper_stats, difficulty_dist, question_type_dist, paper_tag)

    def export_txt(self, df: pd.DataFrame, cross_tab, paper_stats, difficulty_dist, question_type_dist, paper_tag):
        """导出为TXT格式报告"""
        output_dir = Path('data/output/reports')
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        txt_file = output_dir / f'statistics_report_{timestamp}.txt'

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("📊 试题统计分析报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"学科: {self.config.get_subject_name()}\n")
            f.write("="*70 + "\n\n")

            f.write("【概览统计】\n")
            f.write(f"总题目数: {len(df)}\n")
            f.write(f"试卷套数: {df['Paper_ID'].nunique()}\n")
            f.write(f"题型数量: {df['Question_Type'].nunique()}\n")
            f.write(f"知识点标签: {df['Tag'].str.split(', ').explode().nunique()}\n\n")

            f.write("【知识点标签 × 难度 交叉统计】\n")
            f.write(cross_tab.to_string())
            f.write("\n\n")

            f.write("【各分卷题目分布】\n")
            f.write(paper_stats.to_string())
            f.write("\n\n")

            f.write("【难度分布】\n")
            f.write(difficulty_dist.to_string())
            f.write("\n\n")

            f.write("【题型分布】\n")
            f.write(question_type_dist.to_string())
            f.write("\n\n")

            f.write("【各分卷的知识点分布】\n")
            f.write(paper_tag.to_string())
            f.write("\n")

        print(f"\n📄 TXT报告已保存: {txt_file}")

    def export_html(self, df: pd.DataFrame, cross_tab, paper_stats, difficulty_dist, question_type_dist, paper_tag):
        """导出为HTML格式报告（带样式）"""
        output_dir = Path('data/output/reports')
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = output_dir / f'statistics_report_{timestamp}.html'

        # 生成HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>试题统计分析报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2em;
        }}
        .header .meta {{
            opacity: 0.9;
            font-size: 0.9em;
        }}
        .overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-card .label {{
            color: #666;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .tag-badge {{
            display: inline-block;
            padding: 4px 10px;
            background: #667eea;
            color: white;
            border-radius: 15px;
            font-size: 0.85em;
            margin: 2px;
        }}
        .difficulty-easy {{ background: #28a745; }}
        .difficulty-medium {{ background: #ffc107; color: #333; }}
        .difficulty-hard {{ background: #dc3545; }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 试题统计分析报告</h1>
        <div class="meta">
            生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
            学科: {self.config.get_subject_name()}
        </div>
    </div>

    <div class="overview">
        <div class="stat-card">
            <div class="number">{len(df)}</div>
            <div class="label">总题目数</div>
        </div>
        <div class="stat-card">
            <div class="number">{df['Paper_ID'].nunique()}</div>
            <div class="label">试卷套数</div>
        </div>
        <div class="stat-card">
            <div class="number">{df['Question_Type'].nunique()}</div>
            <div class="label">题型数量</div>
        </div>
        <div class="stat-card">
            <div class="number">{df['Tag'].str.split(', ').explode().nunique()}</div>
            <div class="label">知识点标签</div>
        </div>
    </div>

    <div class="section">
        <h2>知识点标签 × 难度 交叉统计</h2>
        {cross_tab.to_html(classes='data-table')}
    </div>

    <div class="section">
        <h2>各分卷题目分布</h2>
        {paper_stats.to_frame('题目数').to_html(classes='data-table')}
    </div>

    <div class="section">
        <h2>难度分布</h2>
        {difficulty_dist.to_frame('题目数').to_html(classes='data-table')}
    </div>

    <div class="section">
        <h2>题型分布 (Top 10)</h2>
        {question_type_dist.to_frame('题目数').to_html(classes='data-table')}
    </div>

    <div class="section">
        <h2>各分卷的知识点分布</h2>
        {paper_tag.to_html(classes='data-table')}
    </div>

    <div class="footer">
        <p>由 通用试题ETL处理系统 自动生成</p>
    </div>
</body>
</html>"""

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"📄 HTML报告已保存: {html_file}")
        print(f"🔗 在浏览器中打开: file://{html_file.absolute()}")
