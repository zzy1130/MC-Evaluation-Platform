# 🤖 Robotic Surgery Plan Certification

基于马尔可夫决策过程（MDP）的机器人手术计划鲁棒性分析工具。

---

## 📋 目录

1. [环境准备](#-环境准备)
2. [启动 Web 应用](#-启动-web-应用)
3. [使用 Web 界面](#-使用-web-界面)
4. [命令行工具](#-命令行工具-invariant_subsetpy)

---

## 🔧 环境准备

### 第一步：检查是否安装了 Python

打开 **终端**（Terminal）：
- **Mac**: 按 `Command + 空格`，输入 `Terminal`，回车
- **Windows**: 按 `Win + R`，输入 `cmd`，回车

在终端中输入以下命令，然后按回车：

```bash
python3 --version
```

✅ 如果显示类似 `Python 3.x.x`，说明已安装，跳到[第三步](#第三步安装项目依赖)。

❌ 如果显示 `command not found` 或错误，请继续第二步安装 Python。

### 第二步：安装 Python（如果没有）

#### Mac 用户：

1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点击黄色的 **Download Python 3.x.x** 按钮
3. 下载完成后，双击打开 `.pkg` 文件
4. 一路点击 **继续** → **同意** → **安装**
5. 安装完成后，关闭终端，重新打开终端
6. 再次输入 `python3 --version` 确认安装成功

#### Windows 用户：

1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点击 **Download Python 3.x.x**
3. 下载完成后，双击运行安装程序
4. ⚠️ **重要**：勾选底部的 **Add Python to PATH**
5. 点击 **Install Now**
6. 安装完成后，重新打开命令提示符
7. 输入 `python --version` 确认安装成功

### 第三步：下载项目

确保你已经下载了本项目到电脑上。假设项目位于：
- Mac: `/Users/你的用户名/Downloads/ctmc`
- Windows: `C:\Users\你的用户名\Downloads\ctmc`

---

## 🚀 启动 Web 应用

### Mac 用户：

1. 打开 **终端**（Terminal）

2. 进入项目目录（把下面的路径改成你的实际路径）：
   ```bash
   cd /Users/你的用户名/Downloads/ctmc/webapp
   ```

3. 给启动脚本添加执行权限：
   ```bash
   chmod +x start.sh
   ```

4. 启动应用：
   ```bash
   ./start.sh
   ```

5. 等待几秒钟，看到类似这样的输出：
   ```
   ✅ Backend started!
   🌐 Open your browser at: http://localhost:8080
   ```

6. 打开浏览器，访问 **http://localhost:8080**

### Windows 用户：

1. 打开 **命令提示符**（cmd）

2. 进入项目目录：
   ```cmd
   cd C:\Users\你的用户名\Downloads\ctmc\webapp\backend
   ```

3. 创建虚拟环境：
   ```cmd
   python -m venv venv
   ```

4. 激活虚拟环境：
   ```cmd
   venv\Scripts\activate
   ```

5. 安装依赖：
   ```cmd
   pip install -r requirements.txt
   ```

6. 启动后端：
   ```cmd
   python app.py
   ```

7. 打开浏览器，访问 **http://localhost:5001**
   
8. 同时打开项目中的 `webapp/index.html` 文件（双击打开即可）

### 如何停止应用？

在终端中按 `Ctrl + C`

---

## 🖥 使用 Web 界面

### 界面介绍

![界面说明](https://via.placeholder.com/800x400?text=Web+Interface)

**左侧面板：**
- **MDP State Transitions**: 输入网络的邻接表（JSON 格式）
- **Target State**: 设置目标节点（吸收态）
- **Visualize**: 可视化网络结构，检查 Feasibility
- **Analyze / Recover**: 分析网络或计算恢复方案

**右侧面板：**
- **State Space**: 显示网络可视化图
- **Analysis / Recovery**: 显示分析结果或恢复方案

### 基本操作流程

1. **输入网络**：在左侧文本框中输入 JSON 格式的邻接表
   ```json
   {
     "0": [],
     "1": [0],
     "2": [0, 1],
     "3": [1, 2]
   }
   ```
   含义：节点 1 可以到达节点 0，节点 2 可以到达节点 0 和 1，以此类推。

2. **设置目标节点**：输入目标状态编号（通常是 0）

3. **点击 Visualize**：
   - 显示网络可视化
   - 检查网络是否 **Feasible**（所有节点都能到达目标）
   - 如果 Feasible ✅，按钮变为 **Analyze**
   - 如果不 Feasible ❌，按钮变为 **Recover**

4. **点击 Analyze**（Feasible 网络）：
   - 计算每条边的鲁棒性指标 ρ(i,j)
   - 红色边 = 关键边（移除后会产生不变子集）
   - 查看 Certification Statistics 了解统计数据

5. **点击 Recover**（不 Feasible 网络）：
   - 自动检测所有不变子集（不同颜色显示）
   - 计算最小恢复方案
   - 显示需要添加的边（红色虚线）

### 重置

点击左上角的 ↺ 图标重置所有内容

---

## 📊 命令行工具 (invariant_subset.py)

这是一个独立的 Python 脚本，可以在命令行中分析网络并生成可视化图片。

### 功能

- 计算网络中每条边的不变子集（Invariant Subset）
- 生成网络可视化图（Spring 布局和层次布局）
- 分析边移除后的影响

### 使用方法

1. 确保已安装依赖：
   ```bash
   pip install matplotlib networkx numpy
   ```

2. 运行脚本：
   ```bash
   cd /Users/你的用户名/Downloads/ctmc
   python3 invariant_subset.py
   ```

3. 脚本会：
   - 打印网络分析结果到终端
   - 生成三张可视化图片保存到指定目录

### 在代码中使用

```python
from invariant_subset import (
    find_invariant_subset,
    find_all_invariant_subsets,
    compute_reachability_layers,
    visualize_network_hierarchical
)

# 定义网络（邻接表）
graph = {
    0: [],           # 目标节点（吸收态）
    1: [0],          # 节点 1 指向节点 0
    2: [0, 1],       # 节点 2 指向节点 0 和 1
    3: [1, 2],       # 节点 3 指向节点 1 和 2
}

target = 0  # 目标节点

# 计算移除某条边后的不变子集
edge_to_remove = (1, 0)
invariant = find_invariant_subset(graph, target, edge_to_remove)
print(f"移除边 {edge_to_remove} 后的不变子集: {invariant}")

# 计算所有边的不变子集
all_results = find_all_invariant_subsets(graph, target)
for edge, inv_set in all_results.items():
    print(f"边 {edge}: 不变子集 = {inv_set if inv_set else '∅'}")

# 生成可视化图
visualize_network_hierarchical(
    graph, 
    target,
    title="Network Analysis",
    save_path="my_network.png"
)
```

### 核心概念

- **不变子集 (Invariant Subset)**: 移除某条边后，无法到达目标节点的节点集合
- **鲁棒性 ρ(i,j)**: `ρ = 1 - |O(i,j)| / (|S| - 1)`，值越高越鲁棒
- **Feasible 网络**: 所有节点都能到达目标节点的网络

---

## ❓ 常见问题

### Q: 启动时提示 "port already in use"
**A**: 端口被占用了。运行 `./start.sh` 会自动清理占用的端口。如果还是不行，手动杀死进程：
```bash
lsof -ti:5001 | xargs kill -9
lsof -ti:8080 | xargs kill -9
```

### Q: pip install 失败，提示 SSL 错误
**A**: 尝试使用以下命令：
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org flask flask-cors pyvis beautifulsoup4
```

### Q: 浏览器显示空白页面
**A**: 
1. 确保后端正在运行（终端显示 Flask 启动信息）
2. 检查浏览器控制台（按 F12）是否有错误
3. 尝试刷新页面

### Q: 图形显示不出来
**A**: 等待几秒钟让图形渲染完成。如果还是不行，点击 Reset 按钮后重新 Visualize。

---

## 📁 项目结构

```
ctmc/
├── README.md                 # 本文件
├── invariant_subset.py       # 命令行分析工具
└── webapp/
    ├── start.sh              # 一键启动脚本 (Mac/Linux)
    ├── index.html            # 前端页面
    └── backend/
        ├── app.py            # Flask 后端
        └── requirements.txt  # Python 依赖
```

---

## 📄 License

MIT License

