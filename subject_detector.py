#!/usr/bin/env python3
"""
学科检测模块
从文件名或内容中自动识别学科类型
"""
import re
from pathlib import Path
from typing import Optional, Dict
import yaml


class SubjectDetector:
    """学科检测器"""

    # 学科关键词映射
    SUBJECT_KEYWORDS = {
        'data_structure': ['数据结构', 'Data Structure', 'DS'],
        'comp_org': ['计算机组成', '组成原理', 'Computer Organization', 'CO', '计算机组织'],
        'os': ['操作系统', 'Operating System', 'OS'],
        'network': ['计算机网络', '网络', 'Computer Network', 'Network'],
        'database': ['数据库', 'Database', 'DB'],
    }

    # 文件名模式映射
    FILENAME_PATTERNS = {
        'data_structure': [
            r'.*数据结构.*',
            r'.*data.*structure.*',
            r'.*DS.*',
        ],
        'comp_org': [
            r'.*计算机组成.*',
            r'.*组成原理.*',
            r'.*computer.*organization.*',
            r'.*comp.*org.*',
        ],
        'os': [
            r'.*操作系统.*',
            r'.*operating.*system.*',
            r'.*OS.*',
        ],
        'network': [
            r'.*计算机网络.*',
            r'.*网络.*',
            r'.*network.*',
        ],
        'database': [
            r'.*数据库.*',
            r'.*database.*',
        ],
    }

    def __init__(self, config_dir: Path = None):
        """
        初始化学科检测器

        Args:
            config_dir: 配置文件目录
        """
        if config_dir is None:
            config_dir = Path(__file__).parent / 'configs'
        self.config_dir = Path(config_dir)

    def detect_from_filename(self, pdf_path: Path) -> Optional[str]:
        """
        从文件名检测学科

        Args:
            pdf_path: PDF文件路径

        Returns:
            学科ID (如 'data_structure', 'comp_org')，未识别返回 None
        """
        filename = pdf_path.name.lower()

        # 按优先级匹配文件名模式
        for subject_id, patterns in self.FILENAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    return subject_id

        return None

    def detect_from_content(self, content: str) -> Optional[str]:
        """
        从内容检测学科（基于关键词频率）

        Args:
            content: 文本内容

        Returns:
            学科ID，未识别返回 None
        """
        scores = {}

        for subject_id, keywords in self.SUBJECT_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # 简单统计关键词出现次数
                score += content.count(keyword)
            if score > 0:
                scores[subject_id] = score

        if not scores:
            return None

        # 返回分数最高的学科
        return max(scores.items(), key=lambda x: x[1])[0]

    def detect(self, pdf_path: Path, content: str = "") -> str:
        """
        综合检测学科

        Args:
            pdf_path: PDF文件路径
            content: PDF文本内容（可选）

        Returns:
            学科ID，默认返回 'default'
        """
        # 优先从文件名检测
        subject_id = self.detect_from_filename(pdf_path)

        # 如果文件名检测失败，尝试从内容检测
        if subject_id is None and content:
            subject_id = self.detect_from_content(content)

        # 默认返回
        return subject_id or 'default'

    def load_config(self, subject_id: str) -> Dict:
        """
        加载学科配置

        Args:
            subject_id: 学科ID

        Returns:
            配置字典
        """
        # 配置文件映射
        config_files = {
            'data_structure': 'data_structure.yaml',
            'comp_org': 'computer_organization.yaml',
            'os': 'default.yaml',  # 如果没有专门配置，使用默认
            'network': 'default.yaml',
            'database': 'default.yaml',
            'default': 'default.yaml',
        }

        config_file = self.config_dir / config_files.get(subject_id, 'default.yaml')

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 配置文件不存在时使用默认配置
            with open(self.config_dir / 'default.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

    def get_available_subjects(self) -> Dict[str, str]:
        """
        获取所有支持的学科列表

        Returns:
            {学科ID: 学科名称} 字典
        """
        subjects = {}

        for config_file in self.config_dir.glob('*.yaml'):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    subject_id = config.get('subject_id', 'default')
                    subject_name = config.get('subject_name', 'Unknown')
                    subjects[subject_id] = subject_name
            except Exception:
                continue

        return subjects
