#!/usr/bin/env python3
"""
题目标签和难度评估模块
为题目分配知识点标签并评估难度
"""
import logging
from typing import List, Dict

from config import ETLConfig


class QuestionTagger:
    """题目标签器"""

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

    def assign_tags(self, content: str) -> List[str]:
        """
        基于关键词打标签

        Args:
            content: 题目内容

        Returns:
            List[str]: 标签列表
        """
        tags = []
        for tag, keywords in self.config.TAG_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    if tag not in tags:
                        tags.append(tag)
                        break  # 找到一个关键词即可
        return tags if tags else ['Other']

    def get_difficulty(self, q_type: str) -> str:
        """
        判断难度

        Args:
            q_type: 题型

        Returns:
            str: 难度等级 (Simple/Medium/Hard)
        """
        for key, diff in self.config.DIFFICULTY_MAP.items():
            if key in q_type:
                return diff
        return 'Medium'

    def tag_all(self, questions: List[Dict]) -> List[Dict]:
        """
        批量打标

        Args:
            questions: 题目列表

        Returns:
            List[Dict]: 已打标的题目列表
        """
        print("\n🏷️  步骤4: 为题目打标签和评估难度...")

        for q in questions:
            tags = self.assign_tags(q['Content'])
            q['Tag'] = ', '.join(tags)
            q['Difficulty'] = self.get_difficulty(q['Question_Type'])

        print(f"   ✅ 完成打标")

        return questions
