#!/usr/bin/env python3
"""
数据结构试题ETL处理工具
从PDF试卷中提取题目，自动打标签和难度评估

使用方法:
    python main.py [--pdf PDF路径] [--output CSV路径] [--verbose]
    python main.py --batch [目录路径]                    # 批量处理目录下所有PDF
"""
import argparse
import sys
import logging
import glob
from pathlib import Path
from datetime import datetime

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
  单文件模式:
  python main.py -p input.pdf                       # 处理单个PDF文件
  python main.py -p input.pdf -o out.csv            # 指定输入和输出
  python main.py --subject comp_org -p input.pdf    # 手动指定学科

  批量模式:
  python main.py --batch data/input/                # 批量处理目录下所有PDF
  python main.py --batch --subject data_structure   # 批量处理并指定学科

  其他:
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
        help="PDF试卷文件路径（单文件模式）"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出CSV文件路径（单文件模式）"
    )
    parser.add_argument(
        "--batch", "-b",
        type=str,
        nargs='?',
        const='data/input',
        help="批量处理目录下所有PDF文件（默认: data/input/）"
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


def process_single_pdf(pdf_path: str, output_path: str = None, subject_id: str = None,
                       verbose: bool = False) -> int:
    """
    处理单个PDF文件

    Args:
        pdf_path: PDF文件路径
        output_path: 输出CSV路径（可选）
        subject_id: 学科ID（可选）
        verbose: 是否显示详细日志

    Returns:
        int: 0=成功, 1=失败
    """
    # 创建配置
    config = ETLConfig(
        pdf_path=pdf_path,
        output_csv=output_path,
        subject_id=subject_id
    )

    # 验证配置
    valid, error_msg = config.validate()
    if not valid:
        print(f"❌ 配置错误: {error_msg}")
        return 1

    print(f"\n{'='*70}")
    print(f"📄 处理文件: {Path(pdf_path).name}")
    print(f"{'='*70}")
    print(f"📚 学科: {config.get_subject_name()}")
    print(f"📁 输出: {config.output_csv}")

    # 执行ETL流程
    try:
        # 步骤1: 提取PDF内容
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

        print(f"✅ 完成! 提取 {len(df)} 道题目")

        return 0

    except FileNotFoundError as e:
        print(f"❌ 文件不存在: {e}")
        return 1
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def process_batch(input_dir: str, subject_id: str = None, verbose: bool = False):
    """
    批量处理目录下的所有PDF文件

    Args:
        input_dir: 输入目录路径
        subject_id: 学科ID（可选）
        verbose: 是否显示详细日志
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"❌ 目录不存在: {input_dir}")
        return 1

    # 查找所有PDF文件
    pdf_files = list(input_path.glob("*.pdf")) + list(input_path.glob("**/*.pdf"))

    if not pdf_files:
        print(f"❌ 在目录 {input_dir} 中未找到PDF文件")
        return 1

    print(f"\n{'='*70}")
    print(f"🚀 批量处理模式")
    print(f"{'='*70}")
    print(f"📁 输入目录: {input_dir}")
    print(f"📄 找到PDF文件: {len(pdf_files)} 个")

    # 创建输出目录
    output_base_dir = Path('data/output/batch')
    output_base_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    batch_output_dir = output_base_dir / f'batch_{timestamp}'
    batch_output_dir.mkdir(parents=True, exist_ok=True)

    # 批量处理
    results = {
        'success': [],
        'failed': []
    }

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] 处理: {pdf_file.name}")

        # 生成输出文件名
        output_csv = batch_output_dir / f"{pdf_file.stem}.csv"

        result = process_single_pdf(
            str(pdf_file),
            str(output_csv),
            subject_id,
            verbose
        )

        if result == 0:
            results['success'].append(pdf_file.name)
        else:
            results['failed'].append(pdf_file.name)

    # 打印批量处理总结
    print(f"\n{'='*70}")
    print(f"📊 批量处理总结")
    print(f"{'='*70}")
    print(f"✅ 成功: {len(results['success'])} 个")
    print(f"❌ 失败: {len(results['failed'])} 个")
    print(f"📁 输出目录: {batch_output_dir}")

    if results['failed']:
        print(f"\n失败文件:")
        for name in results['failed']:
            print(f"  - {name}")

    return 0 if not results['failed'] else 1


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

    # 判断处理模式
    if args.batch:
        # 批量处理模式
        subject_id = None if args.subject == 'auto' else args.subject
        return process_batch(args.batch, subject_id, args.verbose)

    else:
        # 单文件模式
        if not args.pdf:
            print("❌ 错误: 请指定 --pdf 参数或使用 --batch 批量处理")
            print("💡 提示: 使用 -h 查看帮助信息")
            return 1

        subject_id = None if args.subject == 'auto' else args.subject
        return process_single_pdf(args.pdf, args.output, subject_id, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
