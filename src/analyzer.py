import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import logging

from .utils import load_api_changes, find_py_files

logger = logging.getLogger(__name__)


class NumPyCallVisitor(ast.NodeVisitor):
    """
    AST访问器,用于检测NumPy API调用
    
    这个类会遍历AST,记录所有导入的NumPy别名,
    并检查函数调用是否使用了这些别名
    """
    
    def __init__(self, rule_map: Dict[str, Dict[str, Any]], file_path: Path):
        """
        初始化AST访问器
        
        Args:
            rule_map: API变更规则映射 {api_name: rule}
            file_path: 当前正在分析的文件路径
        """
        self.rule_map = rule_map
        self.file_path = file_path
        self.issues: List[Dict[str, Any]] = []
        self.numpy_aliases: Set[str] = set()
        self.numpy_from_imports: Dict[str, str] = {}  # 记录from导入的函数名->模块路径
        self.current_imports: List[Tuple[int, str]] = []
        
    def visit_Import(self, node: ast.Import) -> None:
        """
        处理普通导入语句,如`import numpy as np`
        """
        for alias in node.names:
            if alias.name == 'numpy':
                # 记录别名,如果没有别名则使用'numpy'
                alias_name = alias.asname if alias.asname else alias.name
                self.numpy_aliases.add(alias_name)
                self.current_imports.append((node.lineno, f"import {alias.name}" + 
                                           (f" as {alias.asname}" if alias.asname else "")))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """
        处理从...导入语句,如 `from numpy import random` 或 `from numpy.random import randint`
        """
        if node.module and 'numpy' in node.module:
            # 记录模块的基础别名
            module_alias = node.module.split('.')[-1]
            self.numpy_aliases.add(module_alias)
            
            # 记录导入的详细信息
            imported_names = []
            for alias in node.names:
                imported_names.append(alias.name)
                # 记录直接导入的函数名和对应的模块路径
                self.numpy_from_imports[alias.name] = node.module
                if alias.asname:
                    # 如果有别名，也记录别名
                    self.numpy_from_imports[alias.asname] = node.module
            
            import_stmt = f"from {node.module} import {', '.join(imported_names[:3])}"
            if len(imported_names) > 3:
                import_stmt += f"... (+{len(imported_names)-3} more)"
            self.current_imports.append((node.lineno, import_stmt))
        
        self.generic_visit(node)
    
    def _extract_attribute_chain(self, node: ast.expr) -> Tuple[Optional[str], str]:
        """
        递归提取属性访问链
        
        Args:
            node: AST节点
            
        Returns:
            (顶层别名, 属性链字符串)
        """
        if isinstance(node, ast.Name):
            # 一个变量名
            return node.id, node.id
        elif isinstance(node, ast.Attribute):
            # 递归属性访问
            base_alias, base_chain = self._extract_attribute_chain(node.value)
            if base_alias and base_chain:
                return base_alias, f"{base_chain}.{node.attr}"
        return None, ""
    
    def visit_Call(self, node: ast.Call) -> None:
        """
        检查函数调用是否使用了NumPy API
        
        处理多种情况:
        1. `np.function_name()` - 属性访问形式
        2. `np.module.submodule.function()` - 多层属性访问
        3. `function_name()` - 直接函数调用(如果是从numpy直接导入的)
        """
        api_name = None
        numpy_alias_used = None
        full_api_path = None
        
        # 情况1: 属性访问形式,如 np.function_name() 或 np.random.randint()
        if isinstance(node.func, ast.Attribute):
            # 提取完整的属性访问链
            base_alias, attribute_chain = self._extract_attribute_chain(node.func)
            
            if base_alias and base_alias in self.numpy_aliases:
                numpy_alias_used = base_alias
                full_api_path = attribute_chain
                # 从完整的属性链中移除别名部分,如: "np.random.randint" -> "random.randint"
                if attribute_chain.startswith(f"{base_alias}."):
                    api_name = attribute_chain[len(base_alias) + 1:]
                else:
                    api_name = attribute_chain
        
        # 情况2: 直接函数调用,如 randint() (当从numpy.random import randint时)
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.numpy_from_imports:
                # 获取完整的模块路径
                module_path = self.numpy_from_imports[func_name]
                # 构建完整的API路径
                full_api_path = f"{module_path}.{func_name}"
                # 移除'numpy.'前缀
                if full_api_path.startswith('numpy.'):
                    api_name = full_api_path[6:]  # 移除'numpy.'
                else:
                    api_name = full_api_path
        
        # 检查API是否在变更规则中
        if api_name:
            # 先尝试完整路径匹配
            if api_name in self.rule_map:
                self._record_issue(node, api_name, numpy_alias_used, full_api_path)
            else:
                # 如果完整路径不匹配，尝试只匹配最后一级
                if '.' in api_name:
                    simple_name = api_name.split('.')[-1]
                    if simple_name in self.rule_map:
                        self._record_issue(node, simple_name, numpy_alias_used, full_api_path)
        
        self.generic_visit(node)
    
    def _record_issue(self, node: ast.AST, api_name: str, 
                      numpy_alias: Optional[str], full_api_path: Optional[str] = None) -> None:
        """
        记录检测到的问题
        """
        rule = self.rule_map[api_name]
        
        # 构建实际的调用字符串
        if numpy_alias and full_api_path:
            # 如果有别名和完整路径，构建完整的调用字符串
            actual_call = full_api_path.replace(api_name, f"{numpy_alias}.{api_name}")
        elif numpy_alias:
            # 只有别名
            actual_call = f"{numpy_alias}.{api_name}"
        else:
            # 直接导入的函数
            actual_call = api_name
        
        issue = {
            'file_path': str(self.file_path),
            'line': node.lineno,
            'column': node.col_offset if hasattr(node, 'col_offset') else 0,
            'api_name': f"np.{api_name}" if not api_name.startswith('np.') else api_name,
            'actual_call': actual_call,
            'full_api_path': full_api_path,
            'change_type': rule.get('change_type', 'unknown'),
            'severity': rule.get('severity', 'medium'),
            'description': rule.get('description', ''),
            'suggestion': rule.get('suggestion', ''),
            'since_version': rule.get('since_version', '2.0'),
        }
        
        self.issues.append(issue)
        
        logger.debug(f"发现API兼容性问题: {issue['api_name']} at {self.file_path}:{node.lineno}")
    
    def get_issues(self) -> List[Dict[str, Any]]:
        """获取检测到的问题列表"""
        return self.issues
    
    def get_import_info(self) -> List[Tuple[int, str]]:
        """获取导入信息"""
        return self.current_imports


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
        self.file_imports: Dict[str, List[Tuple[int, str]]] = {}  # 文件路径 -> 导入信息
        
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
            # 规则中的 api_name 是 'np.xxx' 格式,提取 'xxx' 作为键
            api_key = rule['api_name']
            if api_key.startswith('np.'):
                # 移除 'np.' 前缀,保留剩余部分
                api_key = api_key[3:]
            
            # 对于有子模块的API,如 'random.randint',保留完整路径
            self.rule_map[api_key] = rule
            
            # 添加API路径的每一部分作为键
            if '.' in api_key:
                parts = api_key.split('.')
                for i in range(len(parts)):
                    # 从位置i开始的所有部分
                    partial_key = '.'.join(parts[i:])
                    if partial_key not in self.rule_map:
                        self.rule_map[partial_key] = rule
        
        logger.debug(f"规则映射表创建完成,共 {len(self.rule_map)} 个唯一API键")
    
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
        self.file_imports.clear()     # 清空导入信息
        
        py_files = find_py_files(target_path)
        
        for file_path in py_files:
            logger.info(f"正在分析文件: {file_path}")
            file_issues, imports = self._analyze_file(file_path)
            self.detected_issues.extend(file_issues)
            if imports:
                self.file_imports[str(file_path)] = imports
        
        logger.info(f"分析完成！共在 {len(py_files)} 个文件中发现 {len(self.detected_issues)} 个潜在问题")
        return self.detected_issues
    
    def _analyze_file(self, file_path: Path) -> Tuple[List[Dict[str, Any]], List[Tuple[int, str]]]:
        """
        分析单个Python文件
        
        Args:
            file_path: Python文件路径
            
        Returns:
            (问题列表, 导入信息列表)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # 使用ast解析源代码
            tree = ast.parse(source_code, filename=str(file_path))
            
            # 创建访问器并遍历AST
            visitor = NumPyCallVisitor(self.rule_map, file_path)
            visitor.visit(tree)
            
            issues = visitor.get_issues()
            imports = visitor.get_import_info()
            
            if issues:
                logger.info(f"在 {file_path} 中发现 {len(issues)} 个问题")
            
            return issues, imports
            
        except SyntaxError as e:
            logger.warning(f"文件 {file_path} 存在语法错误,已跳过：{e}")
            return [], []
        except Exception as e:
            logger.error(f"分析文件 {file_path} 时发生未知错误：{e}")
            return [], []
    
    def get_summary(self) -> Dict[str, Any]:
        """获取分析结果摘要"""
        summary = {
            "total_files_analyzed": len(self.file_imports),
            "total_issues": len(self.detected_issues),
            "issues_by_type": {},
            "issues_by_severity": {},
            "files_with_issues": set(),
        }
        
        # 按变更类型和严重性统计
        for issue in self.detected_issues:
            change_type = issue['change_type']
            summary['issues_by_type'][change_type] = summary['issues_by_type'].get(change_type, 0) + 1
            
            severity = issue.get('severity', 'unknown')
            summary['issues_by_severity'][severity] = summary['issues_by_severity'].get(severity, 0) + 1
            
            summary['files_with_issues'].add(issue['file_path'])
        
        summary['files_with_issues'] = list(summary['files_with_issues'])
        
        return summary
    
    def get_imports_by_file(self) -> Dict[str, List[Tuple[int, str]]]:
        """获取每个文件的导入信息"""
        return self.file_imports