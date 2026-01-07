#!/usr/bin/env python3
"""
OCR引擎模块（性能优化版）
使用PaddleOCR处理扫描版PDF和手写内容

优化特性：
- 结果缓存：避免重复处理相同页面
- GPU加速：支持CUDA加速
- 并行处理：多页同时OCR
- 进度显示：实时显示处理进度
"""
import logging
import hashlib
import pickle
from typing import List, Dict, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import numpy as np
from PIL import Image
import io

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

from config import ETLConfig


class OCRCache:
    """OCR结果缓存管理器"""

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path('.cache/ocr')
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, page, resolution: int = 200) -> str:
        """生成页面缓存键"""
        # 使用页面内容和分辨率生成哈希
        img = page.to_image(resolution=resolution)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # 计算哈希
        hash_obj = hashlib.md5(img_bytes.read())
        return f"ocr_{hash_obj.hexdigest()}"

    def get(self, page) -> Optional[str]:
        """从缓存获取OCR结果"""
        try:
            cache_key = self._get_cache_key(page)
            cache_file = self.cache_dir / f"{cache_key}.pkl"

            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception:
            pass
        return None

    def set(self, page, text: str):
        """保存OCR结果到缓存"""
        try:
            cache_key = self._get_cache_key(page)
            cache_file = self.cache_dir / f"{cache_key}.pkl"

            with open(cache_file, 'wb') as f:
                pickle.dump(text, f)
        except Exception:
            pass

    def clear(self):
        """清空缓存"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)


class OCREngine:
    """PaddleOCR引擎（性能优化版）"""

    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.ocr = None

        # 性能优化配置
        self.cache = OCRCache(Path('.cache/ocr'))
        self.use_gpu = self._get_gpu_available()
        self.max_workers = 4  # 并行处理线程数

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, self.config.log_level, 'INFO'))
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _get_gpu_available(self) -> bool:
        """检测GPU是否可用"""
        try:
            import paddle
            return paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0
        except Exception:
            return False

    def _init_ocr_engine(self):
        """延迟初始化OCR引擎"""
        if not PADDLEOCR_AVAILABLE:
            raise RuntimeError("PaddleOCR未安装，请运行: pip install paddleocr")

        if self.ocr is None:
            # 尝试GPU模式，失败则回退到CPU模式
            if self.use_gpu:
                try:
                    self.logger.info("初始化PaddleOCR引擎 (GPU模式)...")
                    self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=True)
                    self.logger.info("已启用GPU加速")
                except Exception as e:
                    self.logger.warning(f"GPU模式失败: {e}，回退到CPU模式")
                    self.use_gpu = False
                    self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
                    self.logger.info("OCR引擎初始化完成 (CPU模式)")
            else:
                self.logger.info("初始化PaddleOCR引擎 (CPU模式)...")
                self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
                self.logger.info("OCR引擎初始化完成")

    def extract_text_from_page(self, page, use_cache: bool = True) -> str:
        """
        从pdfplumber的page对象提取OCR文本（带缓存）

        Args:
            page: pdfplumber的page对象
            use_cache: 是否使用缓存

        Returns:
            str: OCR识别的文本
        """
        # 检查缓存
        if use_cache:
            cached = self.cache.get(page)
            if cached:
                self.logger.debug("使用缓存的OCR结果")
                return cached

        try:
            # 优化：降低分辨率以提高速度
            img = page.to_image(resolution=200)  # 从300降到200
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            pil_img = Image.open(img_bytes)

            # 调用PaddleOCR
            self._init_ocr_engine()
            result = self.ocr.ocr(np.array(pil_img))

            # 提取文本
            if result and result[0]:
                texts = []
                for line in result[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]
                        texts.append(text)
                text = '\n'.join(texts)

                # 保存到缓存
                if use_cache and text:
                    self.cache.set(page, text)

                return text

            return ""

        except Exception as e:
            self.logger.error(f"OCR提取失败: {e}")
            return ""

    def extract_text_from_pages_batch(self, pages: List, use_cache: bool = True,
                                      show_progress: bool = True) -> List[str]:
        """
        批量并行处理多个页面

        Args:
            pages: pdfplumber的page对象列表
            use_cache: 是否使用缓存
            show_progress: 是否显示进度

        Returns:
            List[str]: OCR识别的文本列表
        """
        if not pages:
            return []

        # 检查缓存
        cached_results = []
        remaining_indices = []

        if use_cache:
            for i, page in enumerate(pages):
                cached = self.cache.get(page)
                if cached:
                    cached_results.append((i, cached))
                else:
                    remaining_indices.append(i)

            if cached_results:
                self.logger.info(f"从缓存加载 {len(cached_results)} 页")

        # 如果全部命中缓存
        if not remaining_indices:
            return [r[1] for r in sorted(cached_results, key=lambda x: x[0])]

        # 并行处理剩余页面
        results = [None] * len(pages)

        # 填入缓存结果
        for i, text in cached_results:
            results[i] = text

        # 并行OCR
        remaining_pages = [pages[i] for i in remaining_indices]

        if show_progress:
            print(f"\n   OCR处理中: 0/{len(remaining_pages)}", end='', flush=True)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(self.extract_text_from_page, page, False): idx
                for page, idx in zip(remaining_pages, remaining_indices)
            }

            completed = 0
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()

                    # 保存到缓存
                    if results[idx] and use_cache:
                        self.cache.set(pages[idx], results[idx])

                    completed += 1
                    if show_progress:
                        print(f"\r   OCR处理中: {completed}/{len(remaining_pages)}", end='', flush=True)

                except Exception as e:
                    self.logger.error(f"页面{idx+1} OCR失败: {e}")
                    results[idx] = ""

        if show_progress:
            print()  # 换行

        return results

    def assess_text_quality(self, text: str) -> Dict[str, float]:
        """
        评估文本质量（用于判断是否需要OCR回退）

        Args:
            text: 提取的文本

        Returns:
            Dict: 质量指标
        """
        if not text:
            return {'char_count': 0, 'chinese_ratio': 0, 'score': 0}

        lines = text.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]

        # 计算中文字符比例
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        chinese_ratio = chinese_chars / len(text) if text else 0

        # 检测试卷结构关键词
        structure_keywords = ['卷', '题', '选择', '填空', '应用', '设计', '简答', '计算']
        has_structure = any(keyword in text for keyword in structure_keywords)

        # 质量评分（0-1）
        score = 0
        score += min(chinese_chars / 500, 0.4)
        score += chinese_ratio * 0.3
        score += 0.3 if has_structure else 0

        return {
            'char_count': len(text),
            'chinese_ratio': chinese_ratio,
            'avg_line_length': sum(len(l) for l in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0,
            'has_structure': has_structure,
            'score': score
        }

    def clear_cache(self):
        """清空OCR缓存"""
        self.cache.clear()
        self.logger.info("OCR缓存已清空")
