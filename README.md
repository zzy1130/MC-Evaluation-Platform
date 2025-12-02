# 🔗 CTMC Analyser and Recovery Planner

**Robust Stability Evaluation of Perturbed Continuous-Time Markov Chains**

一个用于分析连续时间马尔可夫链（CTMC）鲁棒性的可视化工具。可以检测网络的可行性、计算状态转移的鲁棒性指标，并为不可行网络生成最小恢复方案。

---

## 📋 目录

1. [环境准备（从零开始）](#-环境准备从零开始)
2. [启动应用](#-启动应用)
3. [使用指南](#-使用指南)
4. [命令行工具](#-命令行工具)
5. [常见问题](#-常见问题)

---

## 🔧 环境准备（从零开始）

假设你拿到一台全新的电脑，按以下步骤操作：

### Step 1: 安装 Python

#### Mac 用户

**方法 A：使用 Homebrew（推荐）**

1. 打开 **终端**（Terminal）
   - 按 `Command + 空格`，输入 `Terminal`，按回车

2. 安装 Homebrew（Mac 的包管理器）：
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
   - 按提示输入电脑密码（输入时不会显示）
   - 等待安装完成（可能需要几分钟）

3. 安装 Python：
   ```bash
   brew install python
   ```

4. 验证安装：
   ```bash
   python3 --version
   ```
   应该显示 `Python 3.x.x`

**方法 B：官网下载**

1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点击黄色的 **Download Python 3.x.x** 按钮
3. 下载完成后，双击打开 `.pkg` 文件
4. 按照安装向导操作：点击 **继续** → **继续** → **同意** → **安装**
5. 输入电脑密码，等待安装完成
6. 打开终端，输入 `python3 --version` 验证

#### Windows 用户

1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点击 **Download Python 3.x.x**
3. 下载完成后，**右键点击安装程序** → **以管理员身份运行**
4. ⚠️ **重要**：在安装界面底部，**勾选 "Add Python to PATH"**
5. 点击 **Install Now**
6. 等待安装完成，点击 **Close**
7. 打开 **命令提示符**（按 `Win + R`，输入 `cmd`，回车）
8. 输入 `python --version` 验证安装

### Step 2: 下载项目

确保你已经下载或克隆了本项目：

```bash
git clone https://github.com/zzy1130/MC-Evaluation-Platform.git
```

或者直接下载 ZIP 文件并解压。

### Step 3: 安装项目依赖

1. 打开终端/命令提示符

2. 进入项目目录：
   ```bash
   # Mac
   cd ~/Downloads/MC-Evaluation-Platform/webapp/backend
   
   # Windows
   cd C:\Users\你的用户名\Downloads\MC-Evaluation-Platform\webapp\backend
   ```

3. 创建虚拟环境（隔离项目依赖）：
   ```bash
   # Mac
   python3 -m venv venv
   
   # Windows
   python -m venv venv
   ```

4. 激活虚拟环境：
   ```bash
   # Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```
   
   激活成功后，命令行前面会出现 `(venv)`

5. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```
   
   如果遇到 SSL 错误，使用：
   ```bash
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

---

## 🚀 启动应用

### Mac 用户（推荐使用启动脚本）

```bash
cd ~/Downloads/MC-Evaluation-Platform/webapp
chmod +x start.sh
./start.sh
```

等待看到：
```
✅ Backend started!
🌐 Open your browser at: http://localhost:8080
```

打开浏览器访问 **http://localhost:8080**

### Windows 用户（手动启动）

**终端 1 - 启动后端：**
```cmd
cd C:\Users\你的用户名\Downloads\MC-Evaluation-Platform\webapp\backend
venv\Scripts\activate
python app.py
```

**浏览器：**
直接双击打开 `webapp/index.html` 文件

或者使用 Python 启动一个简单的 HTTP 服务器：
```cmd
cd C:\Users\你的用户名\Downloads\MC-Evaluation-Platform\webapp
python -m http.server 8080
```
然后访问 **http://localhost:8080**

### 停止应用

在终端中按 `Ctrl + C`

---

## 🖥 使用指南

### 界面概览

```
┌─────────────────────────────────────────────────────────────────┐
│  CTMC Analyser and Recovery Planner                             │
├────────────────┬────────────────────────────────────────────────┤
│                │                                                 │
│  CTMC Config   │         State Space / Analysis                 │
│  ┌──────────┐  │         ┌─────────────────────────────────┐   │
│  │ JSON输入  │  │         │                                 │   │
│  │          │  │         │      网络可视化图                 │   │
│  └──────────┘  │         │                                 │   │
│                │         └─────────────────────────────────┘   │
│  Target: [0]   │                                                │
│                │         ┌─────────────────────────────────┐   │
│  [Visualize]   │         │      分析结果表格                 │   │
│  [Analyze]     │         │                                 │   │
│                │         └─────────────────────────────────┘   │
│  Statistics    │                                                │
│  ├ Feasibility │                                                │
│  ├ States      │                                                │
│  └ Transitions │                                                │
└────────────────┴────────────────────────────────────────────────┘
```

### 基本操作流程

#### 1️⃣ 输入网络结构

在左侧 **CTMC Configurations** 文本框中输入 JSON 格式的邻接表：

```json
{
  "0": [],
  "1": [0],
  "2": [0, 1],
  "3": [1, 2],
  "4": [2, 3]
}
```

**格式说明：**
- 键（`"0"`, `"1"`, ...）是节点编号
- 值是该节点可以转移到的目标节点列表
- `"0": []` 表示节点 0 是吸收态（目标状态），没有出边

#### 2️⃣ 设置目标状态

在 **Target State α** 输入框中输入目标节点编号（通常是 `0`）

#### 3️⃣ 点击 Visualize

- 显示网络的可视化图
- 检查网络的 **Feasibility**（可行性）
- 显示基本统计信息

**结果解读：**
- ✅ **Feasible**: 所有节点都能到达目标状态
- ❌ **Not Feasible**: 存在无法到达目标的节点

#### 4️⃣ 分析或恢复

**如果网络 Feasible：**
- 按钮显示为 **Analyze**
- 点击后计算每条边的鲁棒性指标 ρ(i,j)
- 红色边 = 关键边（移除后会产生不变子集）

**如果网络 Not Feasible：**
- 按钮显示为 **Recover**
- 点击后显示：
  - 不同颜色标记的不变子集（无法到达目标的节点组）
  - 最小恢复方案（需要添加的边）

### 核心概念

| 概念 | 说明 |
|------|------|
| **目标状态 α** | 吸收态，所有节点最终应该能到达的状态 |
| **不变子集 O(i,j)** | 移除边 (i,j) 后，无法到达目标状态的节点集合 |
| **鲁棒性 ρ(i,j)** | `ρ = 1 - |O(i,j)| / (|S| - 1)`，值越高表示该边越不关键 |
| **Feasible** | 所有节点都能到达目标状态 |
| **Recovery** | 为不可行网络添加最少的边使其变为可行 |

---

## 📊 命令行工具

`invariant_subset.py` 是一个独立的 Python 脚本，可以在命令行中进行分析。

### 安装额外依赖

```bash
pip install matplotlib networkx numpy
```

### 运行示例

```bash
cd ~/Downloads/MC-Evaluation-Platform
python3 invariant_subset.py
```

### 在代码中使用

```python
from invariant_subset import (
    find_invariant_subset,
    find_all_invariant_subsets,
    visualize_network_hierarchical
)

# 定义网络
graph = {
    0: [],           # 目标状态
    1: [0],
    2: [0, 1],
    3: [1, 2],
}

target = 0

# 计算移除某条边后的不变子集
edge = (1, 0)
invariant = find_invariant_subset(graph, target, edge)
print(f"移除边 {edge} 后的不变子集: {invariant}")

# 分析所有边
all_results = find_all_invariant_subsets(graph, target)
for edge, inv_set in all_results.items():
    rho = 1 - len(inv_set) / (len(graph) - 1) if inv_set else 1.0
    print(f"边 {edge}: O = {inv_set or '∅'}, ρ = {rho:.3f}")

# 生成可视化图
visualize_network_hierarchical(
    graph, target,
    title="CTMC Structure",
    save_path="network.png"
)
```

---

## ❓ 常见问题

### Q: 提示 "python3: command not found"
**A**: Python 没有正确安装或没有添加到 PATH。请重新按照 [Step 1](#step-1-安装-python) 安装。

### Q: pip install 失败，提示网络错误
**A**: 尝试使用国内镜像源：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### Q: 启动时提示 "port already in use"
**A**: 端口被占用。运行以下命令释放端口：
```bash
# Mac
lsof -ti:5001 | xargs kill -9
lsof -ti:8080 | xargs kill -9

# Windows
netstat -ano | findstr :5001
taskkill /PID <PID号> /F
```

### Q: 浏览器显示空白或报错
**A**: 
1. 确保后端正在运行（终端显示 Flask 启动信息）
2. 检查浏览器控制台（按 F12）是否有错误
3. 尝试刷新页面或点击 Reset 按钮

### Q: 图形加载很慢
**A**: 大型网络的物理模拟需要时间。等待几秒钟让图形稳定。

---

## 📁 项目结构

```
MC-Evaluation-Platform/
├── README.md                 # 本文件
├── invariant_subset.py       # 命令行分析工具
└── webapp/
    ├── start.sh              # 一键启动脚本 (Mac/Linux)
    ├── index.html            # 前端页面
    └── backend/
        ├── app.py            # Flask 后端 API
        ├── requirements.txt  # Python 依赖列表
        └── venv/             # Python 虚拟环境（自动生成）
```

---

## 📄 License

MIT License

---

## 🤝 Contributing

欢迎提交 Issue 和 Pull Request！
