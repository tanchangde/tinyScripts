import argparse
import subprocess
import sys
import os
import platform
import glob

# ================= 配置文档 =================
USAGE_EXAMPLES = """
使用示例 (Examples):

  1. 单个文件转换 (默认在同目录下生成同名 PDF):
     python html2pdf.py document.html

  2. 单个文件转换并指定输出文件名:
     python html2pdf.py index.html -o report.pdf

  3. 批量转换目录 (仅当前层级，不包含子目录):
     python html2pdf.py ./docs

  4. 递归转换目录 (包含子目录) 并统一输出到指定文件夹:
     python html2pdf.py ./docs -r -d ./all_pdfs

  5. 强制覆盖已存在的 PDF 文件 (默认会跳过):
     python html2pdf.py ./docs -r -f

  6. 指定使用 Edge 浏览器或手动指定浏览器路径:
     python html2pdf.py input.html --edge
     python html2pdf.py input.html --browser-path "C:/Program Files/Google/Chrome/Application/chrome.exe"
"""
# ===========================================

# ===========================
# 1. 基础设施层
# ===========================

def find_browser_executable(user_path=None, use_edge=False):
    """查找浏览器路径"""
    if user_path and os.path.exists(user_path): return user_path
    system = platform.system()
    paths = []
    
    if system == "Windows":
        if use_edge:
            paths = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
        else:
            paths = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                     r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
    elif system == "Darwin":
        paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    elif system == "Linux":
        paths = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"]

    for p in paths:
        if os.path.exists(p): return p
    print("错误: 未找到浏览器，请使用 --browser-path 指定。")
    sys.exit(1)

def run_conversion(browser, input_file, output_file, force_overwrite=False):
    """执行转换指令，包含存在性检查"""
    abs_input = os.path.abspath(input_file)
    abs_output = os.path.abspath(output_file)
    
    # 存在性检查：如果文件存在且不强制覆盖，则跳过
    if os.path.exists(abs_output) and not force_overwrite:
        print(f"⏭️  [跳过] 文件已存在: {os.path.basename(output_file)}")
        return True

    os.makedirs(os.path.dirname(abs_output), exist_ok=True)
    
    prefix = "file:///" if platform.system() == "Windows" else "file://"
    file_url = prefix + abs_input.replace("\\", "/")

    cmd = [browser, "--headless", "--disable-gpu", f"--print-to-pdf={abs_output}", "--no-pdf-header-footer", file_url]

    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if res.returncode == 0:
            action_text = "覆盖" if os.path.exists(abs_output) and force_overwrite else "生成"
            print(f"✅ [{action_text}] {os.path.basename(input_file)} -> {os.path.basename(output_file)}")
            return True
        else:
            err = res.stderr.decode('utf-8', errors='replace') or res.stderr.decode(errors='replace')
            print(f"❌ [失败] {os.path.basename(input_file)}: {err}")
            return False
    except Exception as e:
        print(f"❌ [异常] {e}")
        return False

# ===========================
# 2. 逻辑层
# ===========================

def collect_files(input_path, recursive=False):
    files = []
    if os.path.isfile(input_path):
        files.append(input_path)
    elif os.path.isdir(input_path):
        if recursive:
            for root, _, filenames in os.walk(input_path):
                for f in filenames:
                    if f.lower().endswith(('.html', '.htm')):
                        files.append(os.path.join(root, f))
        else:
            files.extend(glob.glob(os.path.join(input_path, "*.html")))
            files.extend(glob.glob(os.path.join(input_path, "*.htm")))
    else:
        print(f"错误: 输入路径不存在: {input_path}")
    return files

def calculate_output_path(input_file, specific_output_name, output_dir):
    if output_dir:
        filename = os.path.basename(input_file)
        base, _ = os.path.splitext(filename)
        return os.path.join(output_dir, base + ".pdf")
    if specific_output_name:
        return specific_output_name
    base, _ = os.path.splitext(input_file)
    return base + ".pdf"

# ===========================
# 3. 主流程
# ===========================

def main():
    parser = argparse.ArgumentParser(
        description="HTML 转 PDF 工具 (基于浏览器内核)",
        epilog=USAGE_EXAMPLES, # 绑定使用示例
        formatter_class=argparse.RawDescriptionHelpFormatter # 保持格式
    )
    
    parser.add_argument("input", help="输入路径（文件或目录）")
    parser.add_argument("-o", "--output", help="指定输出文件名 (仅当输入为单文件时有效)")
    parser.add_argument("-d", "--output-dir", help="指定输出目录 (批量处理时推荐)")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归搜索子目录")
    parser.add_argument("-f", "--force", action="store_true", help="强制覆盖已存在的输出文件")
    parser.add_argument("--browser-path", help="手动指定浏览器可执行文件路径")
    parser.add_argument("--edge", action="store_true", help="优先使用 Microsoft Edge")

    args = parser.parse_args()

    browser = find_browser_executable(args.browser_path, args.edge)
    files_to_process = collect_files(args.input, args.recursive)
    
    if not files_to_process:
        print("未找到 HTML 文件。")
        return

    effective_output_name = args.output
    if len(files_to_process) > 1 and args.output:
        print("⚠️  [警告] 检测到多文件输入，已忽略 -o/--output 参数 (请使用 -d 指定输出目录)。")
        effective_output_name = None

    print(f"🚀 开始处理 {len(files_to_process)} 个文件 (覆盖模式: {'开启' if args.force else '关闭'})...")

    count = 0
    skipped = 0
    
    for f in files_to_process:
        target = calculate_output_path(f, effective_output_name, args.output_dir)
        
        abs_target = os.path.abspath(target)
        is_existing = os.path.exists(abs_target)
        
        result = run_conversion(browser, f, target, args.force)
        
        if result:
            if is_existing and not args.force:
                skipped += 1
            else:
                count += 1

    print(f"\n✨ 全部结束: 实际处理 {count} 个, 跳过 {skipped} 个")
    if skipped > 0:
        print("   (提示: 若需重新生成已跳过的文件，请添加 -f 参数)")

if __name__ == "__main__":
    main()