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


class HybridExtractor(PDFExtractor):
    """混合提取器：优先使用pdfplumber，失败时回退到OCR（性能优化版）"""

    def __init__(self, config: ETLConfig, ocr_engine=None):
        super().__init__(config)
        from ocr_engine import OCREngine
        self.ocr_engine = ocr_engine or OCREngine(config)
        self.quality_threshold = 0.3  # 质量阈值
        self.batch_ocr = True  # 启用批量并行OCR

    def extract(self) -> List[Dict]:
        """
        智能提取：pdfplumber + 批量并行OCR回退

        Returns:
            List[Dict]: 页面列表，每项包含页码、文本和来源标记
        """
        print("\n📖 步骤1: 智能提取PDF文本（混合模式 + 并行OCR）...")

        if not self.config.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {self.config.pdf_path}")

        pages = []
        ocr_pages_indices = []  # 需要OCR的页面索引
        ocr_pages = []  # 需要OCR的页面对象

        try:
            with pdfplumber.open(self.config.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   检测到 {total_pages} 页")

                # 第一遍：快速评估，收集需要OCR的页面
                print(f"   分析页面质量...", end='', flush=True)
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    quality = self.ocr_engine.assess_text_quality(text or "")

                    needs_ocr = (
                        quality['score'] < self.quality_threshold or
                        quality['char_count'] < 50
                    )

                    if needs_ocr:
                        ocr_pages_indices.append(i)
                        ocr_pages.append(page)
                        # 先放占位符
                        pages.append({
                            'page_num': i + 1,
                            'text': text or '',
                            'source': 'pending_ocr'
                        })
                    else:
                        pages.append({
                            'page_num': i + 1,
                            'text': text or '',
                            'source': 'pdfplumber'
                        })

                    if (i + 1) % 10 == 0:
                        print(f"\r   分析页面质量: {i+1}/{total_pages}", end='', flush=True)

                print()  # 换行

                # 批量并行处理需要OCR的页面
                if ocr_pages:
                    print(f"   发现 {len(ocr_pages)} 页需要OCR处理")
                    ocr_texts = self.ocr_engine.extract_text_from_pages_batch(
                        ocr_pages,
                        use_cache=True,
                        show_progress=True
                    )

                    # 更新OCR结果
                    for idx, (page_idx, ocr_text) in enumerate(zip(ocr_pages_indices, ocr_texts)):
                        if ocr_text:
                            pages[page_idx]['text'] = ocr_text
                            pages[page_idx]['source'] = 'ocr'
                        else:
                            pages[page_idx]['source'] = 'pdfplumber_fallback'
                else:
                    print("   所有页面质量良好，无需OCR处理")

                # 统计提取来源
                source_stats = {}
                for p in pages:
                    src = p['source']
                    source_stats[src] = source_stats.get(src, 0) + 1

                print(f"   ✅ 共提取 {len(pages)} 页")
                print(f"   来源分布:")
                for src, count in source_stats.items():
                    print(f"      {src}: {count} 页")

        except Exception as e:
            self.logger.error(f"PDF提取失败: {e}")
            raise

        return pages
