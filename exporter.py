#!/usr/bin/env python3
"""
CSV导出模块
将处理后的题目数据导出为CSV文件
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict

from config import ETLConfig


class CSVExporter:
    """CSV导出器"""

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

    def save(self, questions: List[Dict]):
        """
        保存为CSV

        Args:
            questions: 题目列表
        """
        print(f"\n💾 步骤5: 保存到CSV...")

        df = pd.DataFrame(questions)

        # 确保列顺序
        columns = [
            'Paper_ID', 'Question_Type', 'Question_Number',
            'Content', 'Tag', 'Difficulty'
        ]
        df = df[columns]

        # 确保输出目录存在
        self.config.output_csv.parent.mkdir(parents=True, exist_ok=True)

        # 保存
        df.to_csv(self.config.output_csv, index=False, encoding='utf-8-sig')

        print(f"   ✅ 已保存到 {self.config.output_csv}")

        # 预览
        print("\n" + "="*70)
        print("👀 数据预览 (前5行)")
        print("="*70)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        print(df.head())

        return df
