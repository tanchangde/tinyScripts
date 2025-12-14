# 通用终端代理设置指引 (Windows Git Bash / macOS)

> 由 Gemini 3 Pro 辅助生成并人工部分测试通过

### 脚本说明

**1. 脚本功能**

本脚本主要用于在终端环境中快速开启或关闭网络代理。启用后，终端内的网络请求命令（如 `curl`, `wget`, `git clone`, `brew`, `npm` 等）将通过您本地的代理软件转发，从而加速资源下载或访问特定网络。

**2. 为什么需要此脚本？**

*   **默认行为限制**：大多数终端命令（CLI 工具）默认不会读取系统层面的代理设置（即您在系统“设置”中配置的代理通常对终端无效）。
*   **手动配置繁琐**：手动输入 `export http_proxy=...` 既麻烦又容易出错，且关闭时需要逐个 unset 变量。
*   **便捷性**：此脚本提供了类似开关的命令（`proxy` / `unproxy`），一键即可切换网络环境，并自动验证连通性。

**3. 使用前置条件**

*   您需要在本机运行代理软件（如 Clash, v2rayN, Clash Verge, Surge 等）。
*   您需要知道代理软件提供的 **HTTP 代理端口**（通常为 7890, 7897 或 10809，具体请查看软件主界面）。

---

### 脚本代码

请复制以下完整代码块。建议仔细阅读顶部的冲突解决指引和变量设置部分。

```bash
# =============================================================================
#   [Terminal Proxy Tool] 通用终端代理设置脚本
#   适用于: macOS (zsh/bash), Linux, Windows (Git Bash)
# =============================================================================

# --- [0. 冲突解决指引] ---
# 如果您的系统中已经安装了名为 'proxy' 与 'unproxy' 的工具，或者调用命令后异常：
# 请手动将下方函数名修改为独特的名称
# -------------------------

# --- [1. 代理参数配置] ---
# 重要：请务必修改 PROXY_PORT 为您代理软件实际显示的 HTTP 端口
# Clash/ClashX 常见: 7890
# Clash Verge 常见: 7897
# v2rayN 常见: 10809
PROXY_HOST="127.0.0.1"
PROXY_PORT="7890"        # <--- 请根据实际情况修改此端口数字
PROXY_URL="http://${PROXY_HOST}:${PROXY_PORT}"

# --- [2. 开启代理函数] ---
function proxy() {
    # 设置标准环境变量
    export http_proxy="${PROXY_URL}"
    export https_proxy="${PROXY_URL}"
    export all_proxy="${PROXY_URL}"
    # 设置不走代理的地址 (本地回环及局域网)
    export no_proxy="localhost,127.0.0.1,localaddress,.localdomain.com,::1"

    echo -e "\033[36m[Proxy Setup]\033[0m 正在开启终端代理..."
    echo -e "Target Address: \033[4m${PROXY_URL}\033[0m"

    # 连接测试 (使用 curl)
    # 逻辑：尝试连接 Google，超时时间设为 3 秒
    # 如果用户未安装 curl，可能会报错，但环境变量依然生效
    if command -v curl &> /dev/null; then
        if curl -I -s --connect-timeout 3 https://www.google.com > /dev/null; then
            echo -e "\033[32m[Success]\033[0m 代理已生效，Google 连接成功！"
        else
            echo -e "\033[31m[Error]\033[0m 无法连接 Google。"
            echo -e "  -> 请检查: 1.代理软件是否开启 2.脚本中端口号(${PROXY_PORT})是否正确"
        fi
    else
        echo -e "\033[33m[Notice]\033[0m 未检测到 curl，跳过连通性测试 (环境变量已设置)。"
    fi
}

# 自动执行一次，避免每次开启终端都需手动输入 proxy
proxy 

# --- [3. 关闭代理函数] ---
# 使用方法: 在终端直接输入 unproxy
function unproxy() {
    unset http_proxy
    unset https_proxy
    unset all_proxy
    unset no_proxy
    echo -e "\033[33m[Proxy Reset]\033[0m 代理已关闭 (恢复直连模式)"
}
```

---

### 安装步骤

根据您的操作系统，将上述代码写入对应的 Shell 配置文件中。

#### 场景 A：Windows (Git Bash)

Windows Git Bash 默认不会自动加载 `~/.bashrc`，但你可以直接将脚本放到 `~/.bash_profile` 中（推荐简化方法），因为 Git Bash 启动时会自动加载 `~/.bash_profile`。

**步骤 1：配置 `.bash_profile`**

在终端执行以下命令创建或编辑引导文件：
```bash
notepad ~/.bash_profile
```
在打开的记事本中，直接粘贴**脚本代码**部分的所有内容（注意修改 `PROXY_PORT` 端口号）。
保存并关闭文件。

**步骤 2：生效与验证**
关闭所有 Git Bash 窗口并重新打开（或者执行 `source ~/.bash_profile`）。

*   输入 `proxy` -> 开启代理并测试。
*   输入 `unproxy` -> 关闭代理。

**可选兼容方法**：如果需要与 macOS/Linux 保持一致，可以先将脚本放到 `~/.bashrc`，然后在 `~/.bash_profile` 中添加 `if [ -f ~/.bashrc ]; then source ~/.bashrc; fi` 来加载。

#### 场景 B：macOS (默认终端 / iTerm2)

1.  **确认 Shell 类型**：
    输入 `echo $SHELL`。
    *   若是 `/bin/zsh` (macOS 默认)，请编辑 `~/.zshrc`。
    *   若是 `/bin/bash`，请编辑 `~/.bash_profile`。
2.  **编辑文件**：
    运行 `nano ~/.zshrc` (或对应文件)。
3.  **粘贴代码**：
    粘贴脚本并修改端口号。按 `Ctrl+O` 保存，`Ctrl+X` 退出。
4.  **生效配置**：
    运行：`source ~/.zshrc`

---

### 常见问题 (FAQ)

**Q1: 开启 proxy 后，为什么 ping google.com 还是不通？**
> **A:** `ping` 命令工作在 ICMP 协议层，而此脚本设置的是 `http_proxy`（应用层代理）。终端代理通常**不会**让 ping 命令走代理。请使用 `curl -I google.com` 来验证代理是否生效。

**Q2: 依然连接失败 (Error 提示)？**
> **A:** 90% 的原因是端口写错了。不同的代理软件端口不同（例如 Clash Verge 可能是 7897，而旧版 Clash 是 7890）。请务必在脚本的 `PROXY_PORT` 处填入正确的 HTTP 端口。

**Q3: Git 报错 "OpenSSL SSL_read: Connection was reset"？**
> **A:** 这通常是网络不稳定。开启本脚本的 `proxy` 后再试一次。如果依然报错，且你以前设置过 git 的全局代理，请运行 `git config --global --unset http.proxy` 来清除旧配置，让 git 使用本脚本设置的环境变量。
