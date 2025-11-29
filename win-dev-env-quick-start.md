# Windows 现代开发环境基础配置指南

本指南专注于构建 Windows 下的 Linux 内核底座，旨在解决两个核心痛点：**网络连通性**（通过镜像网络）和**软件下载速度**（通过阿里云镜像）。

---

## 第一层：Windows 侧的系统底座与网络架构

### 1. 系统版本硬性检查

要启用最新的“镜像网络”模式，Windows 组件版本必须达标。

1.  **检查 WSL 版本**：
    打开 PowerShell，运行：
    ```powershell
    wsl --version
    ```
    *   要求：**WSL 版本 >= 2.0.0**
    *   *如果版本过低*：运行 `wsl --update` 进行升级。
    *   *如果未安装*：运行 `wsl --install`。

2.  **检查 Windows 版本**：
    *   要求：Windows 11 **22H2** 或更高版本。

### 2. 启用镜像网络模式 (核心配置)

通过全局配置文件，强制 WSL2 共享 Windows 的网络接口。这意味着 WSL 可以直接继承 Windows 的 VPN/代理状态，无需在 Linux 内部配置任何代理脚本。

1.  在 Windows 资源管理器地址栏输入 `%UserProfile%` 并回车（通常进入 `C:\Users\你的用户名`）。
2.  新建文件名为 `.wslconfig` 的文本文件（注意前面有点）。
3.  用记事本打开，写入以下配置：

```ini
[wsl2]
# [核心] 启用镜像网络模式
# 效果：WSL IP 与 Windows 一致，VPN 开启即对 WSL 生效
networkingMode=mirrored

# [推荐] 允许 WSL 绑定 Windows 的 localhost
# 效果：在 WSL 启动 web 服务 (localhost:3000)，Windows 浏览器可直接访问
localhostForwarding=true

# [性能] 限制最大内存占用
# 建议设置为物理内存的 50%，防止 WSL 吃光系统资源
memory=8GB
swap=2GB
```

4.  **重启 WSL 使配置生效**：
    在 PowerShell 中运行：
    ```powershell
    wsl --shutdown
    ```

---

## 第二层：WSL 侧的基础环境标准化

进入 Ubuntu 终端，执行以下步骤，将环境从“原生状态”改造为“国内开发可用状态”。

### 1. 替换阿里云 APT 源 (解决系统更新慢)

我们将 Ubuntu 官方源替换为阿里云镜像站，显著提升 `apt install` 的速度。

*   **操作步骤**：

```bash
# 1. 备份原始源文件
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak

# 2. 替换为阿里源 (适用于 Ubuntu 20.04 / 22.04)
# 使用 sed 命令批量替换域名
sudo sed -i "s@http://.*archive.ubuntu.com@https://mirrors.aliyun.com@g" /etc/apt/sources.list
sudo sed -i "s@http://.*security.ubuntu.com@https://mirrors.aliyun.com@g" /etc/apt/sources.list

# 注意：Ubuntu 24.04 (Noble) 用户请直接编辑 /etc/apt/sources.list.d/ubuntu.sources 文件

# 3. 更新软件索引并升级系统
sudo apt update && sudo apt upgrade -y
```

### 2. 安装编译前置“全家桶” (必做)

这是最关键的一步。几乎所有现代编程语言（Python, R, Node.js, Rust 等）的某些包在安装时都需要现场编译 C/C++ 代码。如果现在不装好这些库，未来你会遇到各种莫名其妙的 `gcc failed` 或 `header not found` 错误。

**直接复制运行以下命令：**

```bash
# 1. 基础构建工具 (编译器、调试器)
sudo apt install -y build-essential

# 2. 基础下载与版本控制工具
sudo apt install -y curl wget git unzip

# 3. 核心开发依赖库 (SSL 加密, 压缩算法, 文本解析)
# 这一步能预防 90% 的“缺少头文件”报错
sudo apt install -y libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev
```

### 3. 验证环境

完成以上步骤后，请进行以下验证确保底座稳固：

1.  **验证网络 (镜像模式)**：
    *   确保 Windows 上开启了 VPN/代理。
    *   在 WSL 终端运行：`curl -I https://www.google.com`
    *   *预期结果*：应迅速返回 `HTTP/2 200` 状态码，无需在 WSL 里设代理。

2.  **验证下载 (阿里源)**：
    *   运行：`sudo apt install neofetch`
    *   *预期结果*：下载速度应非常快（MB/s 级别），且无连接超时错误。
