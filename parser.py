#!/usr/bin/env python3
"""
试卷解析模块
识别试卷结构（卷、题型）并提取题目
"""
import re
import logging
from typing import List, Dict

from config import ETLConfig


class ExamParser:
    """试卷解析器"""

    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = self._setup_logger()

        # 编译正则模式
        self.paper_pattern = re.compile(config.PAPER_PATTERN)
        self.type_pattern = re.compile(config.TYPE_PATTERN)

        # OCR友好的正则模式（更宽松）
        self.ocr_question_patterns = [
            re.compile(p) for p in config.OCR_QUESTION_PATTERNS
        ]

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

    def identify_sections(self, pages_text: List[Dict]) -> List[Dict]:
        """
        识别试卷各部分（卷、题型）

        Args:
            pages_text: 页面文本列表，包含source标记

        Returns:
            List[Dict]: 识别出的部分列表，包含source标记
        """
        print("\n📋 步骤2: 识别试卷结构...")

        sections = []
        current_paper = None
        current_type = None
        current_content = []
        current_source = 'pdfplumber'  # 跟踪当前内容的来源

        for page in pages_text:
            lines = page['text'].split('\n')
            # 记录此页的来源
            page_source = page.get('source', 'pdfplumber')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 检测是否是新的"卷"
                paper_match = self.paper_pattern.search(line)
                if paper_match and line.startswith('卷'):
                    # 保存之前的section
                    if current_paper and current_content:
                        sections.append({
                            'paper': current_paper,
                            'type': current_type or 'Unknown',
                            'content': '\n'.join(current_content),
                            'source': current_source
                        })

                    current_paper = f"卷{paper_match.group(1)}"
                    current_type = None
                    current_content = []
                    current_source = page_source
                    continue

                # 检测是否是新的题型
                type_match = self.type_pattern.match(line)
                if type_match:
                    # 保存之前的section
                    if current_paper and current_content:
                        sections.append({
                            'paper': current_paper,
                            'type': current_type or 'Unknown',
                            'content': '\n'.join(current_content),
                            'source': current_source
                        })

                    current_type = type_match.group(1)
                    current_content = []
                    current_source = page_source
                    continue

                # 收集题目内容
                if current_paper:
                    current_content.append(line)

        # 保存最后一个section
        if current_paper and current_content:
            sections.append({
                'paper': current_paper,
                'type': current_type or 'Unknown',
                'content': '\n'.join(current_content),
                'source': current_source
            })

        # 打印识别结果
        paper_section_count = {}
        for sec in sections:
            if sec['paper'] not in paper_section_count:
                paper_section_count[sec['paper']] = 0
            paper_section_count[sec['paper']] += 1

        for paper, count in sorted(paper_section_count.items()):
            print(f"   {paper}: {count} 个题型部分")

        return sections

    def extract_questions_from_section(self, section: Dict) -> List[Dict]:
        """
        从section中提取题目（支持OCR容错）

        Args:
            section: 试卷部分，包含source标记

        Returns:
            List[Dict]: 题目列表
        """
        questions = []
        content = section['content']

        # 检测是否为OCR文本
        is_ocr_text = section.get('source') == 'ocr'

        # 选择合适的正则模式
        patterns_to_use = self.config.QUESTION_PATTERNS
        if is_ocr_text:
            # OCR文本：先尝试OCR专用模式，再尝试常规模式
            patterns_to_use = self.config.OCR_QUESTION_PATTERNS + self.config.QUESTION_PATTERNS

        for pattern in patterns_to_use:
            matches = re.finditer(pattern, content, re.MULTILINE)

            for match in matches:
                q_num = match.group(1)
                q_content = match.group(2).strip()

                # OCR容错处理
                if is_ocr_text:
                    q_content = self._clean_ocr_content(q_content)

                # 清理内容
                q_content = re.sub(r'\s+', ' ', q_content)
                q_content = q_content.strip()

                # 过滤太短或无效内容
                if len(q_content) < self.config.min_content_length:
                    continue

                # 过滤纯数字或字母
                if re.match(r'^[\dA-D\s()]+$', q_content):
                    continue

                questions.append({
                    'Paper_ID': section['paper'],
                    'Question_Type': section['type'],
                    'Question_Number': q_num,
                    'Content': q_content[:self.config.max_content_length]
                })

            if questions:
                break

        return questions

    def _clean_ocr_content(self, content: str) -> str:
        """
        清理OCR识别的题目内容，修正常见OCR错误

        Args:
            content: OCR识别的内容

        Returns:
            str: 清理后的内容
        """
        if not content:
            return content

        # 常见OCR错误修正
        corrections = {
            'O ': '0 ',  # 题号中的O可能是0
            ' l ': ' 1 ',  # 选项中的l可能是1
            '⑴': '(1)',
            '⑵': '(2)',
            '⑶': '(3)',
            '⑷': '(4)',
            '⑸': '(5)',
            '⑹': '(6)',
            '⑺': '(7)',
            '⑻': '(8)',
            '⑼': '(9)',
            '⑽': '(10)',
            '①': '(1)',
            '②': '(2)',
            '③': '(3)',
            '④': '(4)',
            '⑤': '(5)',
        }

        for wrong, correct in corrections.items():
            content = content.replace(wrong, correct)

        return content

    def extract_questions(self, sections: List[Dict]) -> List[Dict]:
        """
        从所有部分提取题目

        Args:
            sections: 试卷部分列表

        Returns:
            List[Dict]: 所有题目列表
        """
        print("\n🏷️  步骤3: 提取题目...")

        all_questions = []
        for section in sections:
            questions = self.extract_questions_from_section(section)
            all_questions.extend(questions)

        print(f"   ✅ 共提取 {len(all_questions)} 道题目")

        # 按分卷统计
        paper_stats = {}
        for q in all_questions:
            p = q['Paper_ID']
            paper_stats[p] = paper_stats.get(p, 0) + 1

        print(f"\n   各分卷题目数:")
        for paper, count in sorted(paper_stats.items()):
            print(f"      {paper}: {count} 道")

        return all_questions
