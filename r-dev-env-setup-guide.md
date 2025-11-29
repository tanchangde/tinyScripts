# R Development Environment Setup Guide

本指南旨在在 WSL2 的 Ubuntu 环境下构建一个现代化、权限分离的 R 开发环境。核心目标是让 R 包安装到用户目录，避免使用 `sudo` 安装包带来的权限混乱。

## 1. 基础环境准备

### 1.1 强制刷新 WSL 配置 (如果 Zsh 没生效)
如果你刚刚切换了 Shell 但没生效，请彻底重启 WSL：
1. 关闭所有 WSL 终端。
2. 在 PowerShell 中运行：
   ```powershell
   wsl --shutdown
   ```
3. 重新打开终端，输入 `echo $SHELL` 确认输出为 `/usr/bin/zsh`。

### 1.2 安装 R (官方源)
Ubuntu 默认源的 R 版本较旧，我们需要添加 CRAN 官方源以获取最新版。

```zsh
# 1. 安装辅助工具
sudo apt update && sudo apt install -y --no-install-recommends software-properties-common dirmngr

# 2. 添加 R 的 GPG 密钥
wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | sudo tee -a /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc

# 3. 添加源 (自动适配 Ubuntu 版本)
sudo add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/"

# 4. 安装 R 基础包
sudo apt update
sudo apt install -y --no-install-recommends r-base
```

---

## 2. 解决 R 包安装权限问题 (核心步骤)

默认情况下，R 会尝试将包安装到系统目录 (`/usr/local/lib/R/site-library`)，导致普通用户安装时报错 `is not writable`。

我们通过在 Shell 层面设置环境变量，强制指定用户级库路径。

### 2.1 创建用户库目录
```zsh
mkdir -p ~/R/library
```

### 2.2 配置环境变量 (修改 .zshrc)
这是最稳健的方法，比修改 `.Rprofile` 更能确保路径优先级。

1. 编辑 Zsh 配置文件：
   ```zsh
   nano ~/.zshrc
   ```
2. 在文件末尾添加以下两行：
   ```zsh
   # 设置 R 的用户库路径 (解决安装包权限问题)
   export R_LIBS_USER="$HOME/R/library"
   
   # 将 Python 用户目录加入 PATH (为 radian 准备)
   export PATH="$HOME/.local/bin:$PATH"
   ```
3. 保存并退出 (`Ctrl+O` -> Enter -> `Ctrl+X`)。
4. 让配置立即生效：
   ```zsh
   source ~/.zshrc
   ```

### 2.3 验证
打开 R 终端，输入以下命令检查。第一行输出必须是你刚才创建的目录：
```R
.libPaths()
# 预期输出: [1] "/home/yourname/R/library" ...
```

---

## 3. 配置增强型终端 (Radian)

R 原生终端体验较差，推荐使用 `radian` (Python 编写的 R 控制台) 获得语法高亮和多行编辑功能。

### 3.1 安装系统依赖 (编译 R 包必备)
为了防止安装 `tidyverse` 等包时编译失败，先安装这组“全家桶”依赖：
```zsh
sudo apt install -y libcurl4-openssl-dev libssl-dev libxml2-dev libfontconfig1-dev libharfbuzz-dev libfribidi-dev libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev python3-pip
```

### 3.2 安装 Radian
```zsh
pip3 install -U radian
```
*如果不生效，请检查步骤 2.2 中的 PATH 是否配置正确。*

---

## 4. 配置 VS Code

确保你已安装 **Remote - WSL** 插件并连接到 Ubuntu。

1. **安装插件：** 搜索并安装 **R** (Yuki Ueda) 和 **R Debugger** 到远程 Ubuntu 主机。
2. **打开设置：** `Ctrl + ,`，选择 **Remote [WSL: Ubuntu]** 标签。
3. **配置路径 (`settings.json`)：**

   你可以直接点击右上角的“打开设置(JSON)”图标，或者搜索以下项进行修改。

   ```json
   {
       // 使用 radian 作为 R 终端 (注意替换为你的真实用户名)
       "r.rterm.linux": "/home/你的用户名/.local/bin/radian",
       
       // 防止终端粘贴代码时格式错乱
       "r.bracketedPaste": true,
       
       // 启用绘图窗口和变量查看器
       "r.session.watcher": true,
       
       // (可选) 移除 radian 不需要的一些启动参数
       "r.rterm.option": [
           "--no-save",
           "--no-restore"
       ]
   }
   ```

---

## 5. 安装常用 R 包

现在环境已经配置好，可以直接安装包，无需 `sudo`，也不会再有权限询问。

在 VS Code 终端或 radian 中运行：

```R
# 安装语言服务器 (VS Code 智能提示必须)
install.packages("languageserver")

# 安装数据科学核心包 (编译时间较长，请耐心等待)
install.packages("tidyverse")
install.packages("devtools")
```

---

## 6. 最佳实践总结

*   **日常安装：** 直接使用 `install.packages("包名")`，包会自动进入 `~/R/library`，重装系统只需备份此文件夹。
*   **正式项目：** 推荐在项目文件夹中使用 `renv::init()`，建立项目隔离的包环境，避免版本冲突。
*   **路径查找：** 如果 VS Code 找不到 `radian`，在终端输入 `which radian` 获取完整路径。
