"""
测试文件 - 包含NumPy旧API的使用
用于验证分析器是否能正确检测问题
"""
import numpy as np
import os

def legacy_function():
    """使用多个旧版NumPy API的函数"""
    # 1. 使用已移除的API
    err_obj = np.geterrobj()
    
    # 2. 使用已弃用的API
    float_val = np.float(3.14)
    str_val = np.string_("test")
    
    # 3. 正常使用（不应被标记）
    normal_array = np.array([1, 2, 3])
    result = np.sum(normal_array)
    
    return err_obj, float_val, str_val, result

# 类中的使用
class LegacyProcessor:
    def __init__(self):
        self.value = np.float(1.0)  # 类属性中的使用
    
    def process(self):
        """处理方法"""
        # 嵌套调用
        return np.string_("processed")

# 条件语句中的使用
if __name__ == "__main__":
    x = 10
    if x > 5:
        temp = np.float(x)  # 条件块中的使用
    else:
        temp = np.float(0)
    
    print(legacy_function())