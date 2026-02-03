import argparse
from pathlib import Path
import sys
from datetime import datetime

from .analyzer import NumPyMigrationAnalyzer
from .reporter import ReportManager

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='NumPy 2.0+ API 迁移兼容性分析工具'
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
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='reports',
        help='报告输出目录 (默认: reports)'
    )
    parser.add_argument(
        '-f', '--format',
        type=str,
        choices=['markdown', 'html', 'both'],
        default='both',
        help='报告输出格式 (默认: both,即同时生成Markdown和HTML)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细的分析过程信息'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    import logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger = logging.getLogger(__name__)
    
    # 检查规则文件是否存在
    rules_path = Path(args.rules)
    if not rules_path.exists():
        print(f"错误:规则文件 {rules_path} 不存在")
        sys.exit(1)
    
    # 创建分析器实例
    try:
        analyzer = NumPyMigrationAnalyzer(rules_path)
        logger.info(f"分析器初始化完成，已加载 {len(analyzer.api_changes)} 条API变更规则")
    except Exception as e:
        print(f"初始化分析器失败:{e}")
        sys.exit(1)
    
    # 执行分析
    target_path = Path(args.target)
    if not target_path.exists():
        print(f"错误:目标路径 {target_path} 不存在")
        sys.exit(1)
    
    print(f"开始分析 {target_path}...")
    start_time = datetime.now()
    
    issues = analyzer.analyze_directory(target_path)
    summary = analyzer.get_summary()
    
    analysis_time = datetime.now() - start_time
    
    # 输出摘要
    print(f"\n{'='*60}")
    print("分析摘要:")
    print(f"  扫描文件数: {summary['total_files_analyzed']}")
    print(f"  发现问题数: {summary['total_issues']}")
    print(f"  分析用时: {analysis_time.total_seconds():.2f}秒")
    
    if summary['issues_by_type']:
        print(f"  问题类型分布:")
        for issue_type, count in sorted(summary['issues_by_type'].items()):
            print(f"    - {issue_type}: {count}")
    
    if summary['issues_by_severity']:
        print(f"  问题严重性分布:")
        for severity, count in sorted(summary['issues_by_severity'].items()):
            print(f"    - {severity}: {count}")
    
    # 生成报告
    if issues or args.verbose:
        print(f"\n正在生成分析报告...")
        try:
            report_manager = ReportManager(Path(args.output))
            report_results = report_manager.generate_report(
                issues, summary, target_path, args.format
            )
            
            print(f"\n报告生成完成")
            for fmt, files in report_results.items():
                for file_path in files:
                    print(f"  {fmt.upper()}: {file_path}")
            
        except Exception as e:
            logger.error(f"生成报告时发生错误: {e}")
            print(f"报告生成失败，但分析已完成")
    
    print(f"\n{'='*50}")
    if summary['total_issues'] > 0:
        print("发现兼容性问题，请查看生成的分析报告获取详细信息和修复建议")
    else:
        print("未发现明显的兼容性问题")
    
    print(f"{'='*50}")