NumPy 2.0+ API 迁移兼容性分析工具

一个用于检测 Python 代码中 NumPy 2.0+ 不兼容 API 调用的静态分析工具，帮助开发者平滑迁移到 NumPy 2.0 及以上版本

---

功能特性

1. 静态代码分析：无需运行代码即可检测不兼容的 NumPy API 调用
2. 多格式报告：支持 Markdown、HTML 和 JSON 格式的报告输出
3. 智能检测：识别多种 NumPy 导入方式（import numpy as np、from numpy import ... 等）
4. 详细上下文：显示问题代码行及其上下文，便于定位
5. 严重性分级：按高、中、低三个级别对问题进行分类
6. 修复建议：为每个不兼容 API 提供具体的修复建议
7. 批量处理：支持单个文件或整个目录的分析

---

系统要求

· Python 版本: 3.13
· 支持的操作系统: Windows, macOS, Linux

---

安装与使用

1. 创建虚拟环境

```bash
python -m venv venv
```

2. 激活虚拟环境

· Windows:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
· macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

3. 安装依赖

```bash
pip install -r requirements.txt
```

---

项目结构

```
numpy-migration-analyzer/
├── __main__.py              # 程序入口
├── src/
│   ├── __init__.py
│   ├── cli.py              # 命令行接口
│   ├── analyzer.py         # 核心分析逻辑
│   ├── reporter.py         # 报告生成器
│   └── utils.py            # 工具函数
├── data/
│   └── api_changes.json    # API变更规则数据库
├── reports/                # 报告输出目录（自动创建）
├── requirements.txt        # 项目依赖
└── README.md              # 项目说明
```

---

使用方法

基本命令

1. 分析单个 Python 文件
   ```bash
   python -m src /path/to/your/script.py
   ```
2. 分析整个目录
   ```bash
   python -m src /path/to/your/project/
   ```
3. 指定自定义规则文件
   ```bash
   python -m src /path/to/script.py -r /path/to/custom_rules.json
   ```

命令行选项

选项 缩写 默认值 描述
--rules -r data/api_changes.json API 变更规则文件路径
--output -o reports 报告输出目录
--format -f both 报告格式：markdown, html, both
--verbose  False 显示详细分析过程信息

示例

1. 详细模式分析项目，生成 Markdown 和 HTML 报告
   ```bash
   python -m src ./my_project/ --verbose --format both
   ```
2. 只生成 HTML 报告
   ```bash
   python -m src ./my_project/ -f html -o ./analysis_results/
   ```
3. 使用自定义规则文件
   ```bash
   python -m src ./my_project/ -r ./my_rules.json
   ```

---

API 变更规则格式

工具使用 JSON 格式的规则文件来定义 NumPy API 变更规则

规则文件示例

```json
[
  {
    "api_name": "np.function_name",
    "change_type": "removed",
    "severity": "high",
    "description": "该函数在 NumPy 2.0 中已被移除",
    "suggestion": "使用 np.new_function 替代",
    "since_version": "2.0"
  },
  {
    "api_name": "np.random.randint",
    "change_type": "deprecated",
    "severity": "medium",
    "description": "参数签名已变更",
    "suggestion": "检查函数参数，按照新版 API 调整",
    "since_version": "2.0"
  }
]
```

规则字段说明

字段 类型 必填 描述
api_name string 是 NumPy API 名称（以 np. 开头）
change_type string 是 变更类型：removed, deprecated, signature_changed, behavior_changed
severity string 否 严重性级别：high, medium, low
description string 是 变更描述
suggestion string 是 修复建议
since_version string 否 从哪个版本开始变更

---

检测能力

支持的 NumPy 导入方式

· import numpy
· import numpy as np
· import numpy as npx
· from numpy import function
· from numpy.random import randint
· from numpy import random

检测的 API 调用模式

· 直接调用：np.function()
· 嵌套调用：np.random.randint()
· 别名调用：npx.function()
· 直接导入函数：function()（当使用 from numpy import function 时）

---

报告示例

控制台输出

```
开始分析 /path/to/project...
正在分析文件: /path/to/project/example.py
在 example.py 中发现 3 个问题
分析完成！共在 5 个文件中发现 12 个潜在问题

============================================================
分析摘要:
  扫描文件数: 5
  发现问题数: 12
  分析用时: 1.23秒
  问题类型分布:
    - removed: 5
    - deprecated: 7
  问题严重性分布:
    - high: 5
    - medium: 4
    - low: 3

正在生成分析报告...
报告生成完成
  MARKDOWN: reports/numpy_migration_report_20240101_120000.md
  HTML: reports/numpy_migration_report_20240101_120000.html
```

HTML 报告内容

报告包含以下部分：

· 摘要部分：总体统计信息
· 详细问题列表：按文件分组显示问题
· 代码上下文：显示问题行及其周围代码
· 修复建议：按优先级排序的修复指导
· 常见修复模式：重复出现的问题模式

---

在项目中的集成

作为开发依赖

```bash
# 将工具添加到开发依赖
pip install -e .

# 在 CI/CD 中集成
python -m src ./src/ --format markdown --output ./ci-reports/
```

预提交钩子

创建 .pre-commit-config.yaml：

```yaml
repos:
  - repo: local
    hooks:
      - id: numpy-migration-check
        name: Check NumPy 2.0+ Compatibility
        entry: python -m src
        args: ["./", "--format", "markdown", "--output", "./pre-commit-reports/"]
        language: system
        files: \.py$
        pass_filenames: false
```

---

高级配置

自定义规则

```bash
# 1. 复制默认规则文件
cp data/api_changes.json my_custom_rules.json

# 2. 编辑规则文件
# 3. 使用自定义规则
python -m src ./project/ -r my_custom_rules.json
```

忽略特定文件或目录

修改 utils.py 中的 find_py_files 函数，添加忽略规则：

```python
# 在 utils.py 中添加忽略逻辑
ignored_patterns = ['venv', '.git', 'build', 'dist', '__pycache__']
if any(pattern in str(file_path) for pattern in ignored_patterns):
    continue
```

---

故障排除

常见问题

"规则文件不存在" 错误

· 确保 data/api_changes.json 文件存在
· 或使用 -r 选项指定正确的规则文件路径

分析速度慢

· 排除大型虚拟环境目录：在 find_py_files 中添加忽略规则
· 使用 --verbose 查看详细进度

报告生成失败

· 确保输出目录有写入权限
· 检查是否有足够的磁盘空间

调试模式

```bash
# 启用详细日志
python -m src ./project/ --verbose

# 或直接设置环境变量
export PYTHONPATH=.
python -m src ./project/ --verbose
```

---

开发指南

扩展检测能力

要添加新的检测规则：

1. 在 api_changes.json 中添加新的规则
2. 规则会自动被加载和匹配

添加新的报告格式

1. 在 reporter.py 中创建新的报告类，继承 BaseReporter
2. 实现 generate() 方法
3. 在 ReportManager 中注册新格式

运行测试

```bash
# 创建测试目录
mkdir -p test_project
echo "import numpy as np\nx = np.removed_function()" > test_project/test.py

# 运行分析
python -m src test_project/ --verbose
```

---

注意：本工具仅进行静态代码分析，不能保证检测到所有运行时问题，建议在实际迁移前进行全面的测试