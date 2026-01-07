#!/usr/bin/env python3
"""
统计分析模块
生成试题数据的统计报告
"""
import logging
import pandas as pd
from typing import List, Dict

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

    def generate(self, df: pd.DataFrame):
        """
        生成统计报表

        Args:
            df: 题目数据框
        """
        print("\n" + "="*70)
        print("📊 统计分析报告")
        print("="*70)

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

        # 标签×难度交叉统计
        print("\n【知识点标签 × 难度 交叉统计】")
        cross_tab = pd.crosstab(tag_df['Tag'], tag_df['Difficulty'], margins=True)
        print(cross_tab)

        # 各分卷统计
        print("\n【各分卷题目分布】")
        paper_stats = df.groupby('Paper_ID').size().sort_index()
        print(paper_stats)

        # 难度分布
        print("\n【难度分布】")
        print(df['Difficulty'].value_counts())

        # 题型分布
        print("\n【题型分布 (Top 10)】")
        print(df['Question_Type'].value_counts().head(10))

        # 各分卷的知识点分布
        print("\n【各分卷的知识点分布】")
        paper_tag = pd.crosstab(tag_df['Paper'], tag_df['Tag'])
        print(paper_tag)
