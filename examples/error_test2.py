"""
一个包含NumPy旧版API用法的示例文件，用于测试分析器。
"""
import numpy as np
from numpy import random
import numpy as npy  # 测试不同的别名

def legacy_code_examples():
    """演示各种NumPy旧API的用法。"""
    
    # 1. 使用被移除的 np.geterrobj
    try:
        err_obj = np.geterrobj()
        print(f"Error object: {err_obj}")
    except AttributeError as e:
        print(f"np.geterrobj() 已移除: {e}")
    
    # 2. 使用被弃用的 np.string_
    byte_str = np.string_("hello")
    print(f"String: {byte_str}")
    
    # 3. 使用被移除的 np.msort
    arr = np.array([[3, 1], [4, 2]])
    sorted_arr = np.msort(arr)
    print(f"Sorted array:\n{sorted_arr}")
    
    # 4. 使用被弃用的别名 np.float_(float64)
    scalar = np.float_(3.14)
    print(f"Float scalar: {scalar}")
    
    # 正常调用
    normal_array = np.array([1, 2, 3])
    print(f"Normal array: {normal_array}")
    
    return byte_str, sorted_arr, scalar

if __name__ == "__main__":
    print("=" * 50)
    print("运行NumPy旧API演示...")
    print("=" * 50)
    results = legacy_code_examples()
    print("=" * 50)
    print("演示完成。")