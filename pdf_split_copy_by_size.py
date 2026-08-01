"""
PDF 按大小拆分或复制工具

功能：
1. 递归扫描输入目录中的所有 PDF 文件。
2. 小于等于指定大小的 PDF，直接复制到输出目录。
3. 大于指定大小的 PDF，按页拆分为多个 PDF。
4. 拆分文件命名格式：
   原文件名_part001.pdf
   原文件名_part002.pdf
5. 保留输入目录中的原始子目录结构。
6. 输出目录必须指定，且不能位于输入目录内部。

依赖安装：
    pip install pypdf

使用方法：
    python pdf_split_copy_by_size.py -i <输入目录> -o <输出目录> [选项]

参数说明：
    -i, --input          输入目录，必填
    -o, --output         输出目录，必填
    -m, --max-size-mb    单个输出 PDF 的最大大小，单位 MB，默认 90

运行示例：

    # 使用默认阈值 90MB
    python pdf_split_copy_by_size.py \
      -i "/path/to/source_pdfs" \
      -o "/path/to/output_pdfs"

    # 设置拆分阈值为 80MB
    python pdf_split_copy_by_size.py \
      -i "/path/to/source_pdfs" \
      -o "/path/to/output_pdfs" \
      -m 80

Windows PowerShell 示例：
    python .\pdf_split_copy_by_size.py `
      -i "C:\path\to\source_pdfs" `
      -o "C:\path\to\output_pdfs" `
      -m 80

使用 uv 时：
    uv run python pdf_split_copy_by_size.py \
      -i "/path/to/source_pdfs" \
      -o "/path/to/output_pdfs"

注意：
- macOS、Linux 的多行命令续行符为反斜杠：\
- Windows PowerShell 的多行命令续行符为反引号：`
- Windows CMD 的多行命令续行符为脱字符：^
- 若 PDF 的某个单页本身已经超过阈值，无法继续按页拆小；
  脚本会将该页面单独保存，并在终端输出提示。
- 默认阈值为 90MB。
"""

import argparse
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def unique_path(path: Path) -> Path:
    """若目标文件已存在，则生成不冲突的文件名。"""
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def write_pdf(writer: PdfWriter, output_path: Path) -> int:
    """写入 PDF 并返回文件字节大小。"""
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path.stat().st_size


def split_pdf(pdf_path: Path, output_dir: Path, max_size: int) -> None:
    """按页拆分 PDF，使每个输出文件尽量不超过指定大小。"""
    try:
        reader = PdfReader(str(pdf_path))

        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                print(f"[跳过] PDF 已加密，无法处理: {pdf_path}", flush=True)
                return

        total_pages = len(reader.pages)
        if total_pages == 0:
            print(f"[跳过] 空 PDF: {pdf_path}", flush=True)
            return

        print(f"[拆分] {pdf_path}，共 {total_pages} 页", flush=True)

        part_number = 1
        page_index = 0
        temp_path = output_dir / f".__temp_{pdf_path.stem}.pdf"

        while page_index < total_pages:
            writer = PdfWriter()
            part_start_page = page_index

            while page_index < total_pages:
                writer.add_page(reader.pages[page_index])
                current_size = write_pdf(writer, temp_path)

                if current_size > max_size:
                    # 单页本身已超过限制，只能单独输出
                    if page_index == part_start_page:
                        final_name = f"{pdf_path.stem}_part{part_number:03d}.pdf"
                        final_path = unique_path(output_dir / final_name)
                        temp_path.replace(final_path)

                        print(
                            f"  - 输出: {final_path.name} "
                            f"({final_path.stat().st_size / 1024 / 1024:.2f} MB，"
                            "单页已超过限制)",
                            flush=True,
                        )

                        page_index += 1
                        part_number += 1
                    else:
                        # 当前加入的页导致超限，移除它，输出前面的页
                        writer.remove_page(len(writer.pages) - 1)

                        final_name = f"{pdf_path.stem}_part{part_number:03d}.pdf"
                        final_path = unique_path(output_dir / final_name)

                        write_pdf(writer, final_path)
                        temp_path.unlink(missing_ok=True)

                        print(
                            f"  - 输出: {final_path.name} "
                            f"({final_path.stat().st_size / 1024 / 1024:.2f} MB)",
                            flush=True,
                        )

                        part_number += 1

                    break

                page_index += 1

                # 已处理到最后一页，输出当前部分
                if page_index >= total_pages:
                    final_name = f"{pdf_path.stem}_part{part_number:03d}.pdf"
                    final_path = unique_path(output_dir / final_name)

                    temp_path.replace(final_path)

                    print(
                        f"  - 输出: {final_path.name} "
                        f"({final_path.stat().st_size / 1024 / 1024:.2f} MB)",
                        flush=True,
                    )

                    part_number += 1
                    break

            temp_path.unlink(missing_ok=True)

    except Exception as e:
        print(f"[错误] 处理失败: {pdf_path}\n       原因: {e}", flush=True)


def process_pdfs(input_dir: Path, output_dir: Path, max_size: int) -> None:
    print("正在扫描目录中的 PDF 文件，请稍候...", flush=True)

    pdf_files = list(input_dir.rglob("*.pdf")) + list(input_dir.rglob("*.PDF"))
    pdf_files = list(set(pdf_files))

    if not pdf_files:
        print("未找到 PDF 文件。", flush=True)
        return

    print(f"扫描完成，找到 {len(pdf_files)} 个 PDF 文件。", flush=True)
    print(f"输入目录: {input_dir}", flush=True)
    print(f"输出目录: {output_dir}", flush=True)
    print(f"最大文件大小: {max_size / 1024 / 1024:.2f} MB", flush=True)
    print("-" * 60, flush=True)

    for pdf_path in sorted(pdf_files):
        relative_parent = pdf_path.parent.relative_to(input_dir)
        target_dir = output_dir / relative_parent
        target_dir.mkdir(parents=True, exist_ok=True)

        file_size = pdf_path.stat().st_size

        if file_size <= max_size:
            target_path = unique_path(target_dir / pdf_path.name)
            shutil.copy2(pdf_path, target_path)

            print(
                f"[复制] {pdf_path.name} -> {target_path} "
                f"({file_size / 1024 / 1024:.2f} MB)",
                flush=True,
            )
        else:
            split_pdf(pdf_path, target_dir, max_size)

    print("-" * 60, flush=True)
    print("处理完成。", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="递归处理 PDF：超过指定大小的 PDF 拆分，其余 PDF 复制。"
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="待处理的源目录",
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="输出目录（必须指定）",
    )

    parser.add_argument(
        "-m",
        "--max-size-mb",
        type=float,
        default=90,
        help="单个输出 PDF 的最大大小，单位 MB，默认 90",
    )

    args = parser.parse_args()

    if args.max_size_mb <= 0:
        print("错误：--max-size-mb 必须大于 0。", flush=True)
        sys.exit(1)

    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    max_size_bytes = int(args.max_size_mb * 1024 * 1024)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"错误：输入目录不存在或不是目录：{input_dir}", flush=True)
        sys.exit(1)

    # 禁止将输出目录放在输入目录内部，避免新生成文件再次被扫描
    try:
        output_dir.relative_to(input_dir)
        print("错误：输出目录不能位于输入目录内部。", flush=True)
        sys.exit(1)
    except ValueError:
        pass

    output_dir.mkdir(parents=True, exist_ok=True)

    process_pdfs(input_dir, output_dir, max_size_bytes)


if __name__ == "__main__":
    main()
