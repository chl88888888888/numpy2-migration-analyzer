# NumPy 2.0+ 迁移兼容性分析报告

**生成时间**: 2026-02-03 20:58:37  
**分析目标**: `examples`  
**目标名称**: examples  

---
## 摘要

- **扫描文件总数**: 3
- **发现问题总数**: 11
- **存在问题的文件**: 2

### 问题类型分布

- **removed**: 11 个

### 问题严重性分布

- **high**: 8 个
- **low**: 2 个
- **medium**: 1 个

---
## 详细问题列表

### 文件: `examples\error_test1.py`

**问题统计**: 共 7 个问题

#### 问题 1: `np.float_`

- **位置**: 第 13 行
- **类型**: removed
- **严重性**: high
- **描述**: np.float64 的别名已被移除
- **建议修复**: 使用 np.float64

**代码上下文**:

**文件**: `examples\error_test1.py` (第 13 行)

```python
  11 |     
  12 |     # 2. 使用已弃用的API
  13 |     float_val = np.float_(3.14)  # <<< 问题所在
  14 |     str_val = np.string_("test")
  15 |     
```

---
#### 问题 2: `np.string_`

- **位置**: 第 14 行
- **类型**: removed
- **严重性**: high
- **描述**: np.bytes_ 的别名已被移除
- **建议修复**: 使用 np.bytes_(针对字节数据)或 np.str_(针对Unicode字符串)

**代码上下文**:

**文件**: `examples\error_test1.py` (第 14 行)

```python
  12 |     # 2. 使用已弃用的API
  13 |     float_val = np.float_(3.14)
  14 |     str_val = np.string_("test")  # <<< 问题所在
  15 |     
  16 |     # 3. 正常使用（不应被标记）
```

---
#### 问题 3: `np.float_`

- **位置**: 第 25 行
- **类型**: removed
- **严重性**: high
- **描述**: np.float64 的别名已被移除
- **建议修复**: 使用 np.float64

**代码上下文**:

**文件**: `examples\error_test1.py` (第 25 行)

```python
  23 | class LegacyProcessor:
  24 |     def __init__(self):
  25 |         self.value = np.float_(1.0)  # 类属性中的使用  # <<< 问题所在
  26 |     
  27 |     def process(self):
```

---
#### 问题 4: `np.string_`

- **位置**: 第 30 行
- **类型**: removed
- **严重性**: high
- **描述**: np.bytes_ 的别名已被移除
- **建议修复**: 使用 np.bytes_(针对字节数据)或 np.str_(针对Unicode字符串)

**代码上下文**:

**文件**: `examples\error_test1.py` (第 30 行)

```python
  28 |         """处理方法"""
  29 |         # 嵌套调用
  30 |         return np.string_("processed")  # <<< 问题所在
  31 | 
  32 | # 条件语句中的使用
```

---
#### 问题 5: `np.float_`

- **位置**: 第 36 行
- **类型**: removed
- **严重性**: high
- **描述**: np.float64 的别名已被移除
- **建议修复**: 使用 np.float64

**代码上下文**:

**文件**: `examples\error_test1.py` (第 36 行)

```python
  34 |     x = 10
  35 |     if x > 5:
  36 |         temp = np.float_(x)  # 条件块中的使用  # <<< 问题所在
  37 |     else:
  38 |         temp = np.float_(0)
```

---
#### 问题 6: `np.float_`

- **位置**: 第 38 行
- **类型**: removed
- **严重性**: high
- **描述**: np.float64 的别名已被移除
- **建议修复**: 使用 np.float64

**代码上下文**:

**文件**: `examples\error_test1.py` (第 38 行)

```python
  36 |         temp = np.float_(x)  # 条件块中的使用
  37 |     else:
  38 |         temp = np.float_(0)  # <<< 问题所在
  39 |     
  40 |     print(legacy_function())
```

---
#### 问题 7: `np.geterrobj`

- **位置**: 第 10 行
- **类型**: removed
- **严重性**: low
- **描述**: 获取当前浮点错误处理对象的函数与 np.seterrobj 一同被移除
- **建议修复**: 使用上下文管理器 with np.errstate(): 作为替代方案

**代码上下文**:

**文件**: `examples\error_test1.py` (第 10 行)

```python
   8 |     """使用多个旧版NumPy API的函数"""
   9 |     # 1. 使用已移除的API
  10 |     err_obj = np.geterrobj()  # <<< 问题所在
  11 |     
  12 |     # 2. 使用已弃用的API
```

---

### 文件: `examples\error_test2.py`

**问题统计**: 共 4 个问题

#### 问题 1: `np.string_`

- **位置**: 第 19 行
- **类型**: removed
- **严重性**: high
- **描述**: np.bytes_ 的别名已被移除
- **建议修复**: 使用 np.bytes_(针对字节数据)或 np.str_(针对Unicode字符串)

**代码上下文**:

**文件**: `examples\error_test2.py` (第 19 行)

```python
  17 |     
  18 |     # 2. 使用被弃用的 np.string_
  19 |     byte_str = np.string_("hello")  # <<< 问题所在
  20 |     print(f"String: {byte_str}")
  21 |     
```

---
#### 问题 2: `np.float_`

- **位置**: 第 28 行
- **类型**: removed
- **严重性**: high
- **描述**: np.float64 的别名已被移除
- **建议修复**: 使用 np.float64

**代码上下文**:

**文件**: `examples\error_test2.py` (第 28 行)

```python
  26 |     
  27 |     # 4. 使用被弃用的别名 np.float_(float64)
  28 |     scalar = np.float_(3.14)  # <<< 问题所在
  29 |     print(f"Float scalar: {scalar}")
  30 |     
```

---
#### 问题 3: `np.msort`

- **位置**: 第 24 行
- **类型**: removed
- **严重性**: medium
- **描述**: 沿第一个轴排序的便捷函数已过期的弃用,最终被移除
- **建议修复**: 使用 np.sort(a, axis=0) 替代

**代码上下文**:

**文件**: `examples\error_test2.py` (第 24 行)

```python
  22 |     # 3. 使用被移除的 np.msort
  23 |     arr = np.array([[3, 1], [4, 2]])
  24 |     sorted_arr = np.msort(arr)  # <<< 问题所在
  25 |     print(f"Sorted array:\n{sorted_arr}")
  26 |     
```

---
#### 问题 4: `np.geterrobj`

- **位置**: 第 13 行
- **类型**: removed
- **严重性**: low
- **描述**: 获取当前浮点错误处理对象的函数与 np.seterrobj 一同被移除
- **建议修复**: 使用上下文管理器 with np.errstate(): 作为替代方案

**代码上下文**:

**文件**: `examples\error_test2.py` (第 13 行)

```python
  11 |     # 1. 使用被移除的 np.geterrobj
  12 |     try:
  13 |         err_obj = np.geterrobj()  # <<< 问题所在
  14 |         print(f"Error object: {err_obj}")
  15 |     except AttributeError as e:
```

---

## 修复建议

### HIGH 优先级问题 (8 个)

**主要问题类型**:

- removed: 8 个

**示例问题及修复**:

1. **`np.float_`** (第 13 行)
   - 问题: np.float64 的别名已被移除
   - 建议: 使用 np.float64

1. **`np.string_`** (第 14 行)
   - 问题: np.bytes_ 的别名已被移除
   - 建议: 使用 np.bytes_(针对字节数据)或 np.str_(针对Unicode字符串)

### MEDIUM 优先级问题 (1 个)

**主要问题类型**:

- removed: 1 个

**示例问题及修复**:

1. **`np.msort`** (第 24 行)
   - 问题: 沿第一个轴排序的便捷函数已过期的弃用,最终被移除
   - 建议: 使用 np.sort(a, axis=0) 替代

### LOW 优先级问题 (2 个)

**主要问题类型**:

- removed: 2 个

**示例问题及修复**:

1. **`np.geterrobj`** (第 10 行)
   - 问题: 获取当前浮点错误处理对象的函数与 np.seterrobj 一同被移除
   - 建议: 使用上下文管理器 with np.errstate(): 作为替代方案

1. **`np.geterrobj`** (第 13 行)
   - 问题: 获取当前浮点错误处理对象的函数与 np.seterrobj 一同被移除
   - 建议: 使用上下文管理器 with np.errstate(): 作为替代方案

### 常见修复模式

以下修复建议在代码中多次出现：

- **模式 (5 次出现)**: 使用 np.float64
- **模式 (3 次出现)**: 使用 np.bytes_(针对字节数据)或 np.str_(针对Unicode字符串)
- **模式 (2 次出现)**: 使用上下文管理器 with np.errstate(): 作为替代方案
- **模式 (1 次出现)**: 使用 np.sort(a, axis=0) 替代

## 结论与下一步

**需要重点关注**

检测到 11 个兼容性问题,建议优先处理高优先级问题

### 建议操作:
1. 优先修复 **high** 严重性问题
2. 检查 **removed** 类型的API调用,这些在NumPy 2.0中已不可用
3. 测试修改后的代码,确保功能正常
4. 考虑更新NumPy版本要求

---
*报告由 NumPy 2.0+ 迁移兼容性分析工具生成*