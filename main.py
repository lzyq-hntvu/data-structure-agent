#!/usr/bin/env python3
"""
数据结构试题ETL处理工具
从PDF试卷中提取题目，自动打标签和难度评估

使用方法:
    python main.py [--pdf PDF路径] [--output CSV路径] [--verbose]
"""
import argparse
import sys
import logging
from pathlib import Path

from config import ETLConfig
from extractor import HybridExtractor
from parser import ExamParser
from tagger import QuestionTagger
from exporter import CSVExporter
from analyzer import StatisticsAnalyzer


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="通用试题ETL处理工具（支持多学科）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                                    # 使用默认配置（自动检测学科）
  python main.py -p input.pdf                       # 指定PDF文件
  python main.py -o output.csv                      # 指定输出文件
  python main.py -p input.pdf -o out.csv            # 指定输入和输出
  python main.py --subject comp_org                 # 手动指定学科
  python main.py --list-subjects                    # 查看支持的学科列表
  python main.py --verbose                          # 显示详细日志

支持学科:
  data_structure  - 数据结构
  comp_org        - 计算机组成原理
  default         - 通用模式
        """
    )
    parser.add_argument(
        "--pdf", "-p",
        type=str,
        help="PDF试卷文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出CSV文件路径"
    )
    parser.add_argument(
        "--subject", "-s",
        type=str,
        choices=['data_structure', 'comp_org', 'default', 'auto'],
        help="手动指定学科 (auto=自动检测, default=通用模式)"
    )
    parser.add_argument(
        "--list-subjects",
        action="store_true",
        help="列出所有支持的学科"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志"
    )
    return parser.parse_args()


def setup_logging(verbose: bool = False):
    """设置全局日志"""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(name)s - %(levelname)s - %(message)s'
    )


def main():
    """主函数"""
    args = parse_args()
    setup_logging(args.verbose)

    # 处理 --list-subjects 参数
    if args.list_subjects:
        print("="*70)
        print("📚 支持的学科列表")
        print("="*70)
        temp_config = ETLConfig()
        subjects = temp_config.list_available_subjects()
        for sid, name in subjects.items():
            print(f"  {sid:15s} - {name}")
        print("="*70)
        return 0

    # 创建配置
    subject_id = None if args.subject == 'auto' else args.subject
    config = ETLConfig(
        pdf_path=args.pdf,
        output_csv=args.output,
        subject_id=subject_id
    )

    # 验证配置
    valid, error_msg = config.validate()
    if not valid:
        print(f"❌ 配置错误: {error_msg}")
        return 1

    print("="*70)
    print("🚀 通用试题ETL处理系统")
    print("="*70)
    print(f"📚 学科: {config.get_subject_name()}")
    print(f"📄 输入: {config.pdf_path}")
    print(f"📁 输出: {config.output_csv}")
    print("="*70)

    # 执行ETL流程
    try:
        # 步骤1: 提取PDF内容（使用混合提取器：pdfplumber + OCR回退）
        extractor = HybridExtractor(config)
        pages = extractor.extract()

        # 步骤2: 识别试卷结构
        parser = ExamParser(config)
        sections = parser.identify_sections(pages)
        questions = parser.extract_questions(sections)

        # 步骤3: 打标签和评估难度
        tagger = QuestionTagger(config)
        tagged_questions = tagger.tag_all(questions)

        # 步骤4: 保存CSV
        exporter = CSVExporter(config)
        df = exporter.save(tagged_questions)

        # 步骤5: 生成统计报告
        analyzer = StatisticsAnalyzer(config)
        analyzer.generate(df)

        print("\n" + "="*70)
        print("✅ 处理完成！")
        print(f"📁 CSV文件: {config.output_csv}")
        print(f"📊 总题目数: {len(df)}")
        print("="*70)

        return 0

    except FileNotFoundError as e:
        print(f"❌ 文件不存在: {e}")
        return 1
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
