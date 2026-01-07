#!/usr/bin/env python3
"""
PDF文本提取模块
从PDF文件中提取文本内容
"""
import logging
from typing import List, Dict
import pdfplumber

from config import ETLConfig


class PDFExtractor:
    """PDF文本提取器"""

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

    def extract(self) -> List[Dict]:
        """
        提取PDF内容

        Returns:
            List[Dict]: 页面列表，每项包含页码和文本
        """
        print("\n📖 步骤1: 逐页提取PDF文本...")

        # 检查文件是否存在
        if not self.config.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {self.config.pdf_path}")

        pages = []
        try:
            with pdfplumber.open(self.config.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages.append({
                            'page_num': i + 1,
                            'text': text
                        })
                        self.logger.debug(f"提取第{i+1}页")

        except Exception as e:
            self.logger.error(f"PDF提取失败: {e}")
            raise

        print(f"   ✅ 共提取 {len(pages)} 页")
        return pages
