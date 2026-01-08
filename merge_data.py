#!/usr/bin/env python3
"""
合并所有学科的题目数据
将 data/output/ 目录下的所有CSV文件合并为一个主文件
"""
import pandas as pd
from pathlib import Path
from datetime import datetime


def merge_csv_files():
    """合并所有CSV文件"""
    output_dir = Path('data/output')

    # 查找所有CSV文件
    csv_files = list(output_dir.glob('*.csv'))

    # 排除不需要的文件
    exclude_files = ['exam_analysis.csv']
    csv_files = [f for f in csv_files if f.name not in exclude_files]

    if not csv_files:
        print("❌ 未找到CSV文件")
        return

    print("="*70)
    print("🔀 合并题目数据")
    print("="*70)
    print(f"\n📂 输入目录: {output_dir}")
    print(f"📄 找到CSV文件: {len(csv_files)} 个\n")

    # 读取并合并所有CSV
    all_dfs = []
    for csv_file in sorted(csv_files):
        print(f"   读取: {csv_file.name}")
        df = pd.read_csv(csv_file)
        print(f"      - {len(df)} 道题目")
        all_dfs.append(df)

    # 合并数据框
    master_df = pd.concat(all_dfs, ignore_index=True)

    # 保存
    output_file = output_dir / 'exam_analysis.csv'
    master_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"\n{'='*70}")
    print(f"✅ 合并完成！")
    print(f"📁 输出文件: {output_file}")
    print(f"📊 总题目数: {len(master_df)}")
    print(f"{'='*70}")

    # 显示统计
    print(f"\n【各学科题目分布】")
    for df, csv_file in zip(all_dfs, sorted(csv_files)):
        subject_name = csv_file.stem.replace('_ocr', '').replace('_', ' ').title()
        print(f"   {subject_name}: {len(df)} 题")

    print(f"\n【难度分布】")
    print(master_df['Difficulty'].value_counts())

    print(f"\n【知识点分布】")
    tag_counts = {}
    for tags in master_df['Tag']:
        for tag in tags.split(', '):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {tag}: {count}")

    return master_df


if __name__ == "__main__":
    merge_csv_files()
