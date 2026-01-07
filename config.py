#!/usr/bin/env python3
"""
配置管理模块
管理ETL处理的所有配置参数，支持多学科动态配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional

from subject_detector import SubjectDetector

# 加载环境变量
load_dotenv()


class ETLConfig:
    """ETL配置管理类（支持多学科）"""

    # 默认路径
    DEFAULT_PDF_PATH = "data/input/转 Word_数据结构卷一.pdf"
    DEFAULT_OUTPUT_CSV = "data/output/exam_analysis.csv"

    # 通用数据验证规则
    MIN_CONTENT_LENGTH = 10
    MAX_CONTENT_LENGTH = 800

    # 学科特定配置（运行时加载）
    _subject_config: Dict = None
    _subject_id: str = None

    def __init__(
        self,
        pdf_path: str = None,
        output_csv: str = None,
        subject_id: str = None,
        auto_detect: bool = True
    ):
        """
        初始化配置

        Args:
            pdf_path: PDF文件路径
            output_csv: 输出CSV路径
            subject_id: 手动指定学科ID（如 'comp_org', 'data_structure'）
            auto_detect: 是否自动检测学科（默认True）
        """
        self.pdf_path = Path(pdf_path or os.getenv('PDF_PATH', self.DEFAULT_PDF_PATH))
        self.output_csv = Path(output_csv or os.getenv('OUTPUT_CSV', self.DEFAULT_OUTPUT_CSV))

        # 处理配置
        self.min_content_length = int(os.getenv('MIN_CONTENT_LENGTH', self.MIN_CONTENT_LENGTH))
        self.max_content_length = int(os.getenv('MAX_CONTENT_LENGTH', self.MAX_CONTENT_LENGTH))

        # 日志配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # 学科配置
        self.auto_detect = auto_detect
        self.subject_detector = SubjectDetector()
        self._subject_id = subject_id
        self._subject_config = None

    @property
    def subject_id(self) -> str:
        """获取当前学科ID"""
        if self._subject_id is None and self.auto_detect:
            self._subject_id = self.subject_detector.detect(self.pdf_path)
        return self._subject_id or 'default'

    @property
    def subject_config(self) -> Dict:
        """获取当前学科配置"""
        if self._subject_config is None:
            self._subject_config = self.subject_detector.load_config(self.subject_id)
        return self._subject_config

    @property
    def PAPER_PATTERN(self) -> str:
        """试卷卷名识别模式"""
        return self.subject_config.get('paper_pattern', r'卷([一二三四五六七])')

    @property
    def TYPE_PATTERN(self) -> str:
        """题型识别模式"""
        return self.subject_config.get('type_pattern', r'^([一二三四五六七八九十])、\s*([^、\n]{2,15})(?:题|$)')

    @property
    def QUESTION_PATTERNS(self) -> List[str]:
        """题目提取模式列表"""
        return self.subject_config.get('question_patterns', [
            r'(\d+)[.．、]\s*([^A-D\s][^A-D]*?)(?=\n\d+\.|\n[A-D]\.|$)',
            r'(\d+)[.．、]\s*([^\n]+(?:\n[A-D]\.[^\n]+)*)',
        ])

    @property
    def TAG_KEYWORDS(self) -> Dict[str, List[str]]:
        """知识点标签关键词字典"""
        return self.subject_config.get('tags', {'Other': []})

    @property
    def DIFFICULTY_MAP(self) -> Dict[str, str]:
        """题型到难度的映射"""
        return self.subject_config.get('difficulty_map', {
            '选择': 'Simple',
            '填空': 'Simple',
            '应用': 'Medium',
            '设计': 'Hard',
        })

    def get_subject_name(self) -> str:
        """获取当前学科名称"""
        return self.subject_config.get('subject_name', '通用')

    def list_available_subjects(self) -> Dict[str, str]:
        """获取所有支持的学科"""
        return self.subject_detector.get_available_subjects()

    def validate(self) -> tuple[bool, str]:
        """验证配置有效性"""
        # 检查PDF文件是否存在
        if not self.pdf_path.exists():
            return False, f"PDF文件不存在: {self.pdf_path}"

        # 检查输出目录是否可创建
        output_dir = self.output_csv.parent
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"无法创建输出目录: {e}"

        return True, ""

    def __repr__(self) -> str:
        return (
            f"ETLConfig("
            f"subject={self.get_subject_name()}, "
            f"pdf_path={self.pdf_path}, "
            f"output_csv={self.output_csv})"
        )
