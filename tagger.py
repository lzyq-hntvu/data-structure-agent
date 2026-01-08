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

    def get_difficulty(self, q_type: str, content: str = None) -> str:
        """
        判断难度（增强版：支持子串匹配和内容推断）

        Args:
            q_type: 题型
            content: 题目内容（可选，用于推断题型）

        Returns:
            str: 难度等级 (Simple/Medium/Hard)
        """
        # 1. 首先尝试通过题型名称匹配（使用子串匹配）
        for key, diff in self.config.DIFFICULTY_MAP.items():
            if key in q_type:
                return diff

        # 2. 如果题型是Unknown或未匹配到，尝试通过内容推断
        if q_type == 'Unknown' or content:
            return self._infer_difficulty_from_content(content or '')

        # 3. 默认返回Medium
        return 'Medium'

    def _infer_difficulty_from_content(self, content: str) -> str:
        """
        从题目内容推断难度（回退逻辑）

        Args:
            content: 题目内容

        Returns:
            str: 推断的难度等级
        """
        import re

        # 1. 首先检查是否包含编程/算法相关关键词（最高优先级）
        algorithm_keywords = ['算法', '程序', '代码', '函数', '编程', '实现', 'void', 'int ', 'return']
        if any(keyword in content for keyword in algorithm_keywords):
            return 'Hard'

        # 2. 检查是否包含计算/推导相关关键词
        calc_keywords = ['计算', '求解', '推导', '证明', '分析', '设计']
        if any(keyword in content for keyword in calc_keywords):
            return 'Medium'

        # 3. 检查是否包含选择题选项标记（A. B. C. D. 或 (A) (B) (C) (D)）
        choice_patterns = [
            r'\n[A-D]\.',           # A. B. C. D.
            r'\n\([A-D]\)',         # (A) (B) (C) (D)
            r'[A-D]\.[\u4e00-\u9fff]',  # A.中文
            r'^[A-D]\.',            # 行首是 A.
        ]
        for pattern in choice_patterns:
            if re.search(pattern, content):
                return 'Simple'  # 包含选项标记，推测为选择题

        # 4. 检查题目长度（较短的题目通常是填空或选择）
        if len(content) < 30:
            return 'Simple'
        elif len(content) < 80:
            return 'Medium'

        # 默认返回Medium
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
            # 传递题目内容以支持基于内容的难度推断
            q['Difficulty'] = self.get_difficulty(q['Question_Type'], q['Content'])

        print(f"   ✅ 完成打标")

        return questions
