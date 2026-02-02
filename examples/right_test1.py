"""
测试文件 - 完全使用2.0+兼容的API
用于验证分析器不会误报
"""
import numpy as np

def modern_function():
    """使用现代NumPy API的函数"""
    # 使用正确的API
    arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    result = np.sum(arr)
    
    # 使用正确的字符串类型
    bytes_data = np.bytes_("hello")
    str_data = np.str_("world")
    
    # 使用错误处理的现代方式
    with np.errstate(invalid='ignore'):
        calc = np.sqrt([-1, 0, 1])
    
    return result, bytes_data, str_data, calc

if __name__ == "__main__":
    print("All modern APIs used correctly")
    print(modern_function())