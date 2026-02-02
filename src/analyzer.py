import ast
from pathlib import Path
from typing import List, Dict, Any
import logging

from .utils import load_api_changes, find_py_files

logger = logging.getLogger(__name__)

class NumPyMigrationAnalyzer:
    """NumPy 2.0+ API 迁移分析器主类"""
    
    def __init__(self, rules_path: Path):
        """
        初始化分析器
        
        Args:
            rules_path: api_changes.json 文件的路径
        """
        self.rules_path = Path(rules_path)
        self.api_changes: List[Dict[str, Any]] = []
        self.detected_issues: List[Dict[str, Any]] = []
        
        self._load_rules()
        self._create_rule_map()
    
    def _load_rules(self) -> None:
        """加载API变更规则"""
        try:
            self.api_changes = load_api_changes(self.rules_path)
        except Exception as e:
            logger.error(f"初始化失败：加载规则时发生错误 - {e}")
            raise
    
    def _create_rule_map(self) -> None:
        """创建API名称到变更规则的快速查找字典"""
        self.rule_map = {}
        for rule in self.api_changes:
            api_key = rule['api_name'].replace('np.', '', 1) if rule['api_name'].startswith('np.') else rule['api_name']
            self.rule_map[api_key] = rule
        logger.debug(f"规则映射表创建完成，共 {len(self.rule_map)} 个唯一API")
    
    def analyze_directory(self, target_path: Path) -> List[Dict[str, Any]]:
        """
        分析目标目录或文件
        
        Args:
            target_path: 需要分析的目标路径（文件或目录）
            
        Returns:
            检测到的问题列表
        """
        target_path = Path(target_path)
        if not target_path.exists():
            logger.error(f"错误：目标路径 {target_path} 不存在")
            return []
        
        self.detected_issues.clear()  # 清空之前的结果
        py_files = find_py_files(target_path)
        
        for file_path in py_files:
            logger.info(f"正在分析文件: {file_path}")
            self._analyze_file(file_path)
        
        logger.info(f"分析完成！共在 {len(py_files)} 个文件中发现 {len(self.detected_issues)} 个潜在问题")
        return self.detected_issues
    
    def _analyze_file(self, file_path: Path) -> None:
        """
        分析单个Python文件
        
        Args:
            file_path: Python文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # 使用ast解析源代码
            tree = ast.parse(source_code, filename=str(file_path))
            
            # 这里要写ast功能，暂时不写
            logger.debug(f"成功解析 {file_path}，共有 {len(source_code.splitlines())} 行代码")
            
        except SyntaxError as e:
            logger.warning(f"文件 {file_path} 存在语法错误，已跳过：{e}")
        except Exception as e:
            logger.error(f"分析文件 {file_path} 时发生未知错误：{e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取分析结果摘要"""
        summary = {
            "total_files_analyzed": len({issue['file_path'] for issue in self.detected_issues}),
            "total_issues": len(self.detected_issues),
            "issues_by_type": {},
            "issues_by_severity": {}
        }
        
        # 按变更类型统计
        for issue in self.detected_issues:
            change_type = issue['change_type']
            summary['issues_by_type'][change_type] = summary['issues_by_type'].get(change_type, 0) + 1
            
            severity = issue.get('severity', 'unknown')
            summary['issues_by_severity'][severity] = summary['issues_by_severity'].get(severity, 0) + 1
        
        return summary