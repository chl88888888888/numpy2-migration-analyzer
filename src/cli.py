import argparse
from pathlib import Path
import sys

from .analyzer import NumPyMigrationAnalyzer

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='NumPy API变化静态分析工具'
    )
    parser.add_argument(
        'target',
        type=str,
        help='需要分析的目标Python文件或目录路径'
    )
    parser.add_argument(
        '-r', '--rules',
        type=str,
        default='data/api_changes.json',
        help='API变更规则JSON文件路径 (默认: data/api_changes.json)'
    )
    
    args = parser.parse_args()
    
    # 检查规则文件是否存在
    rules_path = Path(args.rules)
    if not rules_path.exists():
        print(f"错误：规则文件 {rules_path} 不存在")
        sys.exit(1)
    
    # 创建分析器
    try:
        analyzer = NumPyMigrationAnalyzer(rules_path)
    except Exception as e:
        print(f"初始化分析器失败：{e}")
        sys.exit(1)
    
    # 执行分析
    target_path = Path(args.target)
    if not target_path.exists():
        print(f"错误：目标路径 {target_path} 不存在")
        sys.exit(1)
    
    print(f"开始分析 {target_path}...")
    issues = analyzer.analyze_directory(target_path)#暂时不用
    
    # 输出摘要
    summary = analyzer.get_summary()
    print(f"\n{'='*50}")
    print("分析摘要：")
    print(f"  扫描文件数: {summary['total_files_analyzed']}")
    print(f"  发现问题数: {summary['total_issues']}")
    
    if summary['issues_by_type']:
        print(f"  问题类型分布:")
        for issue_type, count in summary['issues_by_type'].items():
            print(f"    - {issue_type}: {count}")
    
    if summary['total_issues'] > 0:
        print(f"\n详细问题报告请查看生成的分析文档")
    else:
        print(f"\n未发现明显的NumPy 2.0+兼容性问题")