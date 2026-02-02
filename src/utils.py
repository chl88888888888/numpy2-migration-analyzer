import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# 配置日志，方便调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_api_changes(json_path: Path) -> List[Dict[str, Any]]:
    """
    从JSON文件加载API变更规则
    
    Args:
        json_path: api_changes.json 文件的路径
        
    Returns:
        包含所有变更规则的字典列表
        
    Raises:
        FileNotFoundError: 如果JSON文件不存在
        json.JSONDecodeError: 如果JSON格式错误
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            changes = json.load(f)
        logger.info(f"成功从 {json_path} 加载了 {len(changes)} 条API变更规则")
        return changes
    except FileNotFoundError:
        logger.error(f"错误：在路径 {json_path} 未找到JSON文件")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"错误:JSON文件格式不正确 - {e}")
        raise

def find_py_files(target_path: Path) -> List[Path]:
    """
    递归查找目标目录下的所有Python文件
    
    Args:
        target_path: 需要扫描的目录或文件路径
        
    Returns:
        找到的所有 .py 文件的Path对象列表
    """
    py_files = []
    
    if target_path.is_file() and target_path.suffix == '.py':
        py_files.append(target_path)
    elif target_path.is_dir():
        # 递归遍历目录，忽略 __pycache__ 等
        for file_path in target_path.rglob("*.py"):
            # 可以在这里添加更多忽略规则，比如跳过 venv
            if "__pycache__" not in str(file_path):
                py_files.append(file_path)
    else:
        logger.warning(f"警告：路径 {target_path} 既不是文件也不是目录，已跳过")
    
    logger.info(f"在 {target_path} 中找到 {len(py_files)} 个Python文件")
    return py_files