import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import markdown

logger = logging.getLogger(__name__)


class BaseReporter:
    """报告生成器类"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化报告生成器
        
        Args:
            output_dir: 报告输出目录,默认为当前目录的'reports'文件夹
        """
        self.output_dir = Path(output_dir) if output_dir else Path("reports")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 报告数据
        self.report_data: Dict[str, Any] = {}
        self.generated_files: List[Path] = []
    
    def _extract_code_snippet(self, file_path: Path, line_number: int, context_lines: int = 2) -> Dict[str, Any]:
        """
        从文件中提取代码片段,包括问题行及其上下文
        
        Args:
            file_path: 源文件路径
            line_number: 问题行号(从1开始)
            context_lines: 上下文的行数
            
        Returns:
            包含代码片段信息的字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 调整行号为0基索引
            line_index = line_number - 1
            
            if line_index < 0 or line_index >= len(lines):
                return {
                    'success': False,
                    'error': f'行号 {line_number} 超出文件范围 (共 {len(lines)} 行)'
                }
            
            # 计算上下文范围
            start_line = max(0, line_index - context_lines)
            end_line = min(len(lines), line_index + context_lines + 1)
            
            # 提取代码片段
            snippet_lines = lines[start_line:end_line]
            
            # 计算问题行在片段中的索引
            issue_line_in_snippet = line_index - start_line
            
            # 为每一行添加行号信息
            numbered_lines = []
            for i, line in enumerate(snippet_lines):
                actual_line_num = start_line + i + 1
                numbered_lines.append({
                    'line_number': actual_line_num,
                    'content': line.rstrip('\n'),
                    'is_issue_line': (i == issue_line_in_snippet)
                })
            
            return {
                'success': True,
                'file_path': str(file_path),
                'issue_line': line_number,
                'context_lines': context_lines,
                'snippet': numbered_lines,
                'issue_line_index': issue_line_in_snippet,
                'start_line': start_line + 1,
                'end_line': end_line
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'读取文件失败: {str(e)}'
            }
    
    def prepare_report_data(self, 
                          issues: List[Dict[str, Any]], 
                          summary: Dict[str, Any],
                          target_path: Path,
                          analysis_time: datetime) -> Dict[str, Any]:
        """
        准备报告数据
        
        Args:
            issues: 检测到的问题列表
            summary: 分析摘要
            target_path: 分析的目标路径
            analysis_time: 分析时间
            
        Returns:
            组织好的报告数据字典
        """
        # 按文件分组问题
        issues_by_file = {}
        for issue in issues:
            file_path = issue['file_path']
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            
            # 为每个问题添加代码片段
            snippet_info = self._extract_code_snippet(
                Path(issue['file_path']),
                issue['line']
            )
            issue['code_snippet'] = snippet_info
            
            issues_by_file[file_path].append(issue)
        
        # 按严重性排序问题
        severity_order = {'high': 0, 'medium': 1, 'low': 2, 'unknown': 3}
        for file_issues in issues_by_file.values():
            file_issues.sort(key=lambda x: severity_order.get(x.get('severity', 'unknown'), 3))
        
        # 按变更类型统计每个文件的问题
        file_stats = {}
        for file_path, file_issues in issues_by_file.items():
            stats = {
                'total': len(file_issues),
                'by_type': {},
                'by_severity': {}
            }
            for issue in file_issues:
                change_type = issue['change_type']
                severity = issue.get('severity', 'unknown')
                stats['by_type'][change_type] = stats['by_type'].get(change_type, 0) + 1
                stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            file_stats[file_path] = stats
        
        report_data = {
            'metadata': {
                'generated_at': analysis_time.isoformat(),
                'generated_at_formatted': analysis_time.strftime('%Y-%m-%d %H:%M:%S'),
                'target_path': str(target_path),
                'target_name': target_path.name,
            },
            'summary': {
                'total_files': summary.get('total_files_analyzed', 0),
                'total_issues': summary.get('total_issues', 0),
                'files_with_issues': len(summary.get('files_with_issues', [])),
                'issues_by_type': summary.get('issues_by_type', {}),
                'issues_by_severity': summary.get('issues_by_severity', {}),
            },
            'issues': {
                'all_issues': issues,
                'by_file': issues_by_file,
                'file_stats': file_stats,
            },
            'recommendations': self._generate_recommendations(summary, issues),
        }
        
        self.report_data = report_data
        return report_data
    
    def _generate_recommendations(self, summary: Dict[str, Any], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成修复建议摘要"""
        recommendations = {
            'priority_order': ['high', 'medium', 'low'],
            'by_severity': {},
            'common_fixes': {},
        }
        
        # 按严重性分组建议
        severity_groups = {}
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(issue)
        
        for severity, group_issues in severity_groups.items():
            # 提取最常见的几种问题类型
            change_types = {}
            for issue in group_issues:
                change_type = issue['change_type']
                change_types[change_type] = change_types.get(change_type, 0) + 1
            
            top_change_types = sorted(change_types.items(), key=lambda x: x[1], reverse=True)[:3]
            
            recommendations['by_severity'][severity] = {
                'count': len(group_issues),
                'top_change_types': top_change_types,
                'example_issues': group_issues[:2] if group_issues else [],  # 取前2个作为示例
            }
        
        suggestion_counter = {}
        for issue in issues:
            suggestion = issue.get('suggestion', '').strip()
            if suggestion and len(suggestion) < 200:
                suggestion_counter[suggestion] = suggestion_counter.get(suggestion, 0) + 1
        
        common_suggestions = sorted(suggestion_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        recommendations['common_fixes'] = dict(common_suggestions)
        
        return recommendations
    
    def generate(self, issues: List[Dict[str, Any]], 
                 summary: Dict[str, Any], 
                 target_path: Path) -> List[Path]:
        """
        生成报告
        
        Args:
            issues: 检测到的问题列表
            summary: 分析摘要
            target_path: 分析的目标路径
            
        Returns:
            生成的报告文件路径列表
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def save_data_json(self, filename: str = "report_data.json") -> Path:
        """将报告数据保存为JSON文件"""
        json_path = self.output_dir / filename
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)
        logger.info(f"报告数据已保存到: {json_path}")
        self.generated_files.append(json_path)
        return json_path


class MarkdownReporter(BaseReporter):
    """Markdown格式报告生成器"""
    
    def _format_code_snippet_md(self, snippet_info: Dict[str, Any]) -> str:
        """
        将代码片段格式化为Markdown
        
        Args:
            snippet_info: 代码片段信息
            
        Returns:
            Markdown格式的代码片段
        """
        if not snippet_info.get('success', False):
            return f"*无法提取代码片段: {snippet_info.get('error', '未知错误')}*"
        
        lines = []
        lines.append(f"**文件**: `{snippet_info['file_path']}` (第 {snippet_info['issue_line']} 行)")
        lines.append("")
        lines.append("```python")
        
        for line_info in snippet_info['snippet']:
            line_num = line_info['line_number']
            content = line_info['content']
            
            # 如果是问题行,添加标记
            if line_info['is_issue_line']:
                lines.append(f"{line_num:4d} | {content}  # <<< 问题所在")
            else:
                lines.append(f"{line_num:4d} | {content}")
        
        lines.append("```")
        lines.append("")
        
        return "\n".join(lines)
    
    def generate(self, issues: List[Dict[str, Any]], 
                 summary: Dict[str, Any], 
                 target_path: Path) -> List[Path]:
        """
        生成Markdown格式报告
        """
        analysis_time = datetime.now()
        self.prepare_report_data(issues, summary, target_path, analysis_time)
        
        # 生成Markdown内容
        md_content = self._generate_markdown()
        
        # 保存Markdown文件
        timestamp = analysis_time.strftime("%Y%m%d_%H%M%S")
        md_filename = f"numpy_migration_report_{timestamp}.md"
        md_path = self.output_dir / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Markdown报告已生成: {md_path}")
        self.generated_files.append(md_path)
        
        # 同时保存JSON数据
        self.save_data_json()
        
        return self.generated_files
    
    def _generate_markdown(self, report_data: Dict[str, Any] = None) -> str:
        """生成Markdown报告内容"""
        data = report_data if report_data is not None else self.report_data
        metadata = data['metadata']
        summary = data['summary']
        issues_data = data['issues']
        recommendations = data['recommendations']
        
        md_lines = []
        
        # 标题和元数据
        md_lines.append(f"# NumPy 2.0+ 迁移兼容性分析报告")
        md_lines.append("")
        md_lines.append(f"**生成时间**: {metadata['generated_at_formatted']}  ")
        md_lines.append(f"**分析目标**: `{metadata['target_path']}`  ")
        md_lines.append(f"**目标名称**: {metadata['target_name']}  ")
        md_lines.append("")
        md_lines.append("---")
        
        # 执行摘要
        md_lines.append("## 摘要")
        md_lines.append("")
        md_lines.append(f"- **扫描文件总数**: {summary['total_files']}")
        md_lines.append(f"- **发现问题总数**: {summary['total_issues']}")
        md_lines.append(f"- **存在问题的文件**: {summary['files_with_issues']}")
        md_lines.append("")
        
        # 问题类型分布
        if summary['issues_by_type']:
            md_lines.append("### 问题类型分布")
            md_lines.append("")
            for issue_type, count in sorted(summary['issues_by_type'].items()):
                md_lines.append(f"- **{issue_type}**: {count} 个")
            md_lines.append("")
        
        # 严重性分布
        if summary['issues_by_severity']:
            md_lines.append("### 问题严重性分布")
            md_lines.append("")
            for severity, count in sorted(summary['issues_by_severity'].items()):
                md_lines.append(f"- **{severity}**: {count} 个")
            md_lines.append("")
        
        md_lines.append("---")
        
        # 详细问题列表
        md_lines.append("## 详细问题列表")
        md_lines.append("")
        
        if not issues_data['all_issues']:
            md_lines.append("未发现NumPy 2.0+兼容性问题")
        else:
            # 按文件分组显示
            for file_path, file_issues in issues_data['by_file'].items():
                file_stat = issues_data['file_stats'].get(file_path, {})
                md_lines.append(f"### 文件: `{file_path}`")
                md_lines.append("")
                md_lines.append(f"**问题统计**: 共 {file_stat.get('total', 0)} 个问题")
                md_lines.append("")
                
                for i, issue in enumerate(file_issues, 1):
                    md_lines.append(f"#### 问题 {i}: `{issue['api_name']}`")
                    md_lines.append("")
                    md_lines.append(f"- **位置**: 第 {issue['line']} 行")
                    md_lines.append(f"- **类型**: {issue['change_type']}")
                    md_lines.append(f"- **严重性**: {issue.get('severity', '未知')}")
                    md_lines.append(f"- **描述**: {issue['description']}")
                    md_lines.append(f"- **建议修复**: {issue['suggestion']}")
                    md_lines.append("")
                    
                    # 添加代码片段
                    md_lines.append("**代码上下文**:")
                    md_lines.append("")
                    md_lines.append(self._format_code_snippet_md(issue['code_snippet']))
                    
                    md_lines.append("---")
                
                md_lines.append("")
        
        # 修复建议
        md_lines.append("## 修复建议")
        md_lines.append("")
        
        # 按优先级排序的修复建议
        for severity in recommendations['priority_order']:
            if severity in recommendations['by_severity']:
                severity_data = recommendations['by_severity'][severity]
                if severity_data['count'] > 0:
                    md_lines.append(f"### {severity.upper()} 优先级问题 ({severity_data['count']} 个)")
                    md_lines.append("")
                    
                    # 显示主要问题类型
                    if severity_data['top_change_types']:
                        md_lines.append("**主要问题类型**:")
                        md_lines.append("")
                        for change_type, count in severity_data['top_change_types']:
                            md_lines.append(f"- {change_type}: {count} 个")
                        md_lines.append("")
                    
                    # 显示示例问题
                    if severity_data['example_issues']:
                        md_lines.append("**示例问题及修复**:")
                        md_lines.append("")
                        for example in severity_data['example_issues']:
                            md_lines.append(f"1. **`{example['api_name']}`** (第 {example['line']} 行)")
                            md_lines.append(f"   - 问题: {example['description']}")
                            md_lines.append(f"   - 建议: {example['suggestion']}")
                            md_lines.append("")
        
        # 常见修复模式
        if recommendations['common_fixes']:
            md_lines.append("### 常见修复模式")
            md_lines.append("")
            md_lines.append("以下修复建议在代码中多次出现：")
            md_lines.append("")
            for suggestion, count in recommendations['common_fixes'].items():
                md_lines.append(f"- **模式 ({count} 次出现)**: {suggestion}")
            md_lines.append("")
        
        # 结论
        md_lines.append("## 结论与下一步")
        md_lines.append("")
        
        total_issues = summary['total_issues']
        if total_issues == 0:
            md_lines.append("**代码兼容性良好**")
            md_lines.append("")
            md_lines.append("您的代码中没有检测到NumPy 2.0+的兼容性问题,可以安全升级")
        elif total_issues < 10:
            md_lines.append("**需要少量修改**")
            md_lines.append("")
            md_lines.append(f"检测到 {total_issues} 个兼容性问题,建议按照上述建议进行修改")
        else:
            md_lines.append("**需要重点关注**")
            md_lines.append("")
            md_lines.append(f"检测到 {total_issues} 个兼容性问题,建议优先处理高优先级问题")
        
        md_lines.append("")
        md_lines.append("### 建议操作:")
        md_lines.append("1. 优先修复 **high** 严重性问题")
        md_lines.append("2. 检查 **removed** 类型的API调用,这些在NumPy 2.0中已不可用")
        md_lines.append("3. 测试修改后的代码,确保功能正常")
        md_lines.append("4. 考虑更新NumPy版本要求")
        
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("*报告由 NumPy 2.0+ 迁移兼容性分析工具生成*")
        
        return "\n".join(md_lines)


class HTMLReporter(BaseReporter):
    """HTML格式报告生成器"""
    
    def _format_code_snippet_html(self, snippet_info: Dict[str, Any]) -> str:
        """
        将代码片段格式化为HTML
        
        Args:
            snippet_info: 代码片段信息
            
        Returns:
            HTML格式的代码片段
        """
        if not snippet_info.get('success', False):
            return f'<div class="code-snippet-error">无法提取代码片段: {snippet_info.get("error", "未知错误")}</div>'
        
        lines_html = []
        lines_html.append(f'<div class="code-snippet-header">')
        lines_html.append(f'<strong>文件</strong>: <code>{snippet_info["file_path"]}</code> (第 {snippet_info["issue_line"]} 行)')
        lines_html.append(f'</div>')
        lines_html.append(f'<div class="code-snippet-container">')
        
        for line_info in snippet_info['snippet']:
            line_num = line_info['line_number']
            content = line_info['content']
            escaped_content = self._escape_html(content)
            
            # 如果是问题行,添加特殊样式
            if line_info['is_issue_line']:
                lines_html.append(f'<div class="code-line issue-line">')
                lines_html.append(f'<span class="line-number">{line_num:4d}</span>')
                lines_html.append(f'<span class="line-content">{escaped_content}</span>')
                lines_html.append(f'<span class="issue-marker"> # &lt;&lt;&lt; 问题所在</span>')
                lines_html.append(f'</div>')
            else:
                lines_html.append(f'<div class="code-line">')
                lines_html.append(f'<span class="line-number">{line_num:4d}</span>')
                lines_html.append(f'<span class="line-content">{escaped_content}</span>')
                lines_html.append(f'</div>')
        
        lines_html.append(f'</div>')
        
        return "\n".join(lines_html)
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def generate(self, issues: List[Dict[str, Any]], 
                summary: Dict[str, Any], 
                target_path: Path) -> List[Path]:
        """
        生成HTML格式报告
        
        通过Markdown转换实现简单的HTML报告
        """
        analysis_time = datetime.now()
        self.prepare_report_data(issues, summary, target_path, analysis_time)
        
        # 生成Markdown内容
        md_reporter = MarkdownReporter(self.output_dir)
        md_content = md_reporter._generate_markdown(self.report_data)
        
        # 转换为HTML
        html_content = markdown.markdown(md_content, extensions=['extra', 'tables'])
        
        # 添加代码片段的CSS样式
        code_snippet_css = """
        .code-snippet-container {
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 12px;
            line-height: 1.5;
            margin: 10px 0;
            overflow: auto;
            padding: 10px;
        }
        .code-snippet-header {
            background-color: #f6f8fa;
            border-bottom: 1px solid #e1e4e8;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            color: #586069;
            font-size: 12px;
            margin: 0;
            padding: 8px 12px;
        }
        .code-line {
            display: flex;
            min-height: 20px;
            padding: 1px 0;
        }
        .code-line:hover {
            background-color: #f0f0f0;
        }
        .issue-line {
            background-color: #fff0f0;
            border-left: 3px solid #ff6b6b;
            padding-left: 9px;
        }
        .line-number {
            color: #6a737d;
            min-width: 50px;
            padding-right: 10px;
            text-align: right;
            user-select: none;
        }
        .line-content {
            flex: 1;
            white-space: pre;
        }
        .issue-marker {
            color: #d73a49;
            font-weight: bold;
            margin-left: 10px;
        }
        .code-snippet-error {
            background-color: #fff0f0;
            border: 1px solid #ffdce0;
            border-radius: 6px;
            color: #86181d;
            padding: 10px;
            margin: 10px 0;
        }
        """
        
        # 创建完整的HTML文档
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NumPy 2.0+ 迁移兼容性分析报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
            margin-bottom: 30px;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
            margin-top: 1.5em;
            padding-bottom: 0.3em;
            border-bottom: 1px solid #eaecef;
        }}
        h1 {{
            color: #1a237e;
            border-bottom: 2px solid #1a237e;
        }}
        code {{
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        .success {{
            color: #28a745;
            font-weight: bold;
        }}
        .warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        .danger {{
            color: #dc3545;
            font-weight: bold;
        }}
        .severity-high {{ color: #dc3545; }}
        .severity-medium {{ color: #ffc107; }}
        .severity-low {{ color: #28a745; }}
        .footer {{
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid #eaecef;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
        .summary-box {{
            background-color: #f8f9fa;
            border-left: 4px solid #1a237e;
            padding: 15px;
            margin: 20px 0;
        }}
        {code_snippet_css}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
    </div>
    <div class="footer">
        <p>报告由 NumPy 2.0+ 迁移兼容性分析工具生成 | {analysis_time.strftime('%Y-%m-%d')}</p>
    </div>
</body>
</html>"""
        
        # 保存HTML文件
        timestamp = analysis_time.strftime("%Y%m%d_%H%M%S")
        html_filename = f"numpy_migration_report_{timestamp}.html"
        html_path = self.output_dir / html_filename
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        logger.info(f"HTML报告已生成: {html_path}")
        self.generated_files.append(html_path)
        
        # 同时保存JSON数据
        self.save_data_json()
        
        return self.generated_files


class ReportManager:
    """报告管理器,统一管理不同格式的报告生成"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else Path("reports")
        self.reporters = {
            'markdown': MarkdownReporter(self.output_dir),
            'html': HTMLReporter(self.output_dir),
            'both': None  # 特殊标识,表示同时生成两种格式
        }
    
    def generate_report(self, 
                       issues: List[Dict[str, Any]], 
                       summary: Dict[str, Any], 
                       target_path: Path,
                       format: str = 'both') -> Dict[str, List[Path]]:
        """
        生成报告
        
        Args:
            issues: 检测到的问题列表
            summary: 分析摘要
            target_path: 分析的目标路径
            format: 报告格式,可选 'markdown', 'html', 'both'
            
        Returns:
            字典格式,键为报告格式,值为生成的文件路径列表
        """
        results = {}
        
        if format == 'both':
            # 生成两种格式
            for fmt in ['markdown', 'html']:
                reporter = self.reporters[fmt]
                files = reporter.generate(issues, summary, target_path)
                results[fmt] = files
        elif format in self.reporters:
            reporter = self.reporters[format]
            files = reporter.generate(issues, summary, target_path)
            results[format] = files
        else:
            raise ValueError(f"不支持的报告格式: {format}可选: 'markdown', 'html', 'both'")
        
        # 打印生成的文件信息
        total_files = sum(len(files) for files in results.values())
        logger.info(f"报告生成完成共生成 {total_files} 个文件")
        
        for fmt, files in results.items():
            for file_path in files:
                logger.info(f"  - {fmt.upper()}: {file_path}")
        
        return results