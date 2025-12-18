import os
import argparse
import glob
from bs4 import BeautifulSoup

# ================= 文档配置 =================
# 将文档赋值给变量，确保一定能被 argparse 读取到
USAGE_EXAMPLES = """
使用示例 (Examples):

  1. 基础用法：删除 ID 为 'js_row_immersive_stream_wrap' 的元素（覆盖原文件）
     python cleaner.py -s "#js_row_immersive_stream_wrap"

  2. 另存文件：删除类名为 'ad-banner' 的 div，保存到新目录
     python cleaner.py -i ./input -o ./output -s "div.ad-banner"

  3. 指定文件类型：删除所有 .htm 文件中的 '.trash' 类
     python cleaner.py -s ".trash" -p "*.htm"

  4. 复杂选择器：删除 '.content' 类下的所有 script 标签
     python cleaner.py -s ".content script"
"""
# ===========================================

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        # description 显示在帮助的最顶部
        description="HTML 批量元素清理工具 (基于 CSS 选择器)",
        
        # epilog 显示在帮助的最底部 (参数列表之后)
        epilog=USAGE_EXAMPLES,
        
        # 这个 formatter 很关键，它能保留 USAGE_EXAMPLES 里的换行和缩进
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # --- 参数定义 ---
    parser.add_argument(
        '-s', '--selector', 
        type=str, 
        required=True, 
        help='要移除元素的 CSS 选择器 (必填，如: "#id", ".class")'
    )

    parser.add_argument(
        '-p', '--pattern', 
        type=str, 
        default='*.html', 
        help='文件匹配模式 (默认: *.html)'
    )
    
    parser.add_argument(
        '-i', '--input', 
        type=str, 
        default='.', 
        help='输入文件夹路径 (默认: 当前文件夹)'
    )
    
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        default=None, 
        help='输出文件夹路径 (默认: 不指定则覆盖原文件)'
    )
    
    return parser.parse_args()

def process_file(file_path, output_dir, selector):
    # ... (处理逻辑与之前相同，无需变动) ...
    # 1. 读取文件
    content = None
    encoding_used = 'utf-8'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            encoding_used = 'gbk'
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
        except Exception as e:
            print(f"[读取失败] {os.path.basename(file_path)}: {e}")
            return

    # 2. 解析与处理
    soup = BeautifulSoup(content, 'html.parser')
    target_elements = soup.select(selector)

    if target_elements:
        count = len(target_elements)
        for el in target_elements:
            el.decompose()
            
        # 3. 确定保存路径
        if output_dir:
            file_name = os.path.basename(file_path)
            save_path = os.path.join(output_dir, file_name)
            action_type = "另存"
        else:
            save_path = file_path
            action_type = "覆盖"

        # 4. 写入文件
        try:
            with open(save_path, 'w', encoding=encoding_used) as f:
                f.write(str(soup))
            print(f"[已{action_type}] 移除 {count} 处 -> {os.path.basename(save_path)}")
        except Exception as e:
            print(f"[写入失败] {save_path}: {e}")
    else:
        print(f"[跳过] 未匹配到选择器: {os.path.basename(file_path)}")

def main():
    args = parse_args()
    
    input_dir = args.input
    output_dir = args.output
    selector = args.selector
    pattern = args.pattern

    # 检查输入目录
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在 -> {input_dir}")
        return

    # 创建输出目录
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as e:
            print(f"错误: 无法创建输出目录 -> {e}")
            return

    # 查找文件
    search_path = os.path.join(input_dir, pattern)
    files = glob.glob(search_path)
    
    if not files:
        print(f"在 '{input_dir}' 中未找到匹配 '{pattern}' 的文件。")
        return

    print(f"--- 开始处理 ---")
    print(f"目标选择器: {selector}")
    print(f"找到文件: {len(files)} 个")
    print("-" * 30)

    for file_path in files:
        process_file(file_path, output_dir, selector)
        
    print("-" * 30)
    print("处理完成。")

if __name__ == "__main__":
    main()