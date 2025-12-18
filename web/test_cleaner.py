import unittest
import os
import sys
import shutil
import tempfile
from unittest.mock import patch
from bs4 import BeautifulSoup

# 导入我们要测试的模块
import cleaner

class TestHTMLCleaner(unittest.TestCase):

    def setUp(self):
        """每个测试运行前执行：创建临时目录和测试文件"""
        self.test_dir = tempfile.mkdtemp()
        
        # 1. 创建一个标准的 UTF-8 HTML 文件 (包含目标 ID)
        self.html_utf8 = os.path.join(self.test_dir, "test_utf8.html")
        with open(self.html_utf8, 'w', encoding='utf-8') as f:
            f.write("""
            <html>
                <body>
                    <div id="remove-me">I should be gone</div>
                    <div class="keep-me">I should stay</div>
                </body>
            </html>
            """)

        # 2. 创建一个 GBK 编码的 HTML 文件 (包含目标 Class)
        self.html_gbk = os.path.join(self.test_dir, "test_gbk.html")
        with open(self.html_gbk, 'w', encoding='gbk') as f:
            f.write("""
            <html>
                <body>
                    <div class="ad-banner">广告内容(GBK)</div>
                    <p>正文内容</p>
                </body>
            </html>
            """)

        # 3. 创建一个不包含目标的 HTML 文件
        self.html_clean = os.path.join(self.test_dir, "clean.html")
        with open(self.html_clean, 'w', encoding='utf-8') as f:
            f.write("<html><body><p>No targets here</p></body></html>")

    def tearDown(self):
        """每个测试运行后执行：清理临时目录"""
        shutil.rmtree(self.test_dir)

    def test_remove_by_id_inplace(self):
        """测试 1: 使用 ID 选择器，覆盖原文件"""
        target_selector = "#remove-me"
        
        # 模拟命令行参数: cleaner.py -i [dir] -s "#remove-me"
        test_args = ['cleaner.py', '-i', self.test_dir, '-s', target_selector]
        
        with patch.object(sys, 'argv', test_args):
            cleaner.main()

        # 验证文件内容
        with open(self.html_utf8, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        self.assertIsNone(soup.find(id="remove-me"), "ID 为 remove-me 的元素应该被删除")
        self.assertIsNotNone(soup.find(class_="keep-me"), "其他元素应该保留")

    def test_remove_by_class_save_new(self):
        """测试 2: 使用 Class 选择器，另存为新文件 (支持 GBK)"""
        target_selector = ".ad-banner"
        output_dir = os.path.join(self.test_dir, "output")
        
        # 模拟命令行参数: cleaner.py -i [dir] -o [out_dir] -s ".ad-banner"
        test_args = ['cleaner.py', '-i', self.test_dir, '-o', output_dir, '-s', target_selector]
        
        with patch.object(sys, 'argv', test_args):
            cleaner.main()

        # 验证输出目录是否存在
        self.assertTrue(os.path.exists(output_dir))
        
        # 验证新文件是否存在
        new_file_path = os.path.join(output_dir, "test_gbk.html")
        self.assertTrue(os.path.exists(new_file_path))

        # 验证内容 (读取时用 GBK)
        with open(new_file_path, 'r', encoding='gbk') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        self.assertFalse(soup.select(".ad-banner"), "Class 为 ad-banner 的元素应该被删除")
        self.assertTrue(soup.find("p"), "正文内容应该保留")

    def test_no_match_skip(self):
        """测试 3: 没有匹配元素时，不应该修改文件"""
        target_selector = ".non-existent-class"
        
        # 获取修改前的时间戳
        original_mtime = os.path.getmtime(self.html_utf8)
        
        test_args = ['cleaner.py', '-i', self.test_dir, '-s', target_selector]
        
        with patch.object(sys, 'argv', test_args):
            cleaner.main()
            
        # 验证文件修改时间是否未变 (或者内容未变)
        # 注意：某些极快的文件系统操作可能导致 mtime 没变，这里主要看逻辑，
        # 更严谨的是检查内容。
        with open(self.html_utf8, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('id="remove-me"', content, "未匹配时不应删除任何内容")

    def test_input_dir_not_exist(self):
        """测试 4: 输入目录不存在的情况"""
        fake_dir = os.path.join(self.test_dir, "does_not_exist")
        test_args = ['cleaner.py', '-i', fake_dir, '-s', 'div']
        
        # 我们捕获 stdout 来检查是否打印了错误信息，或者确保程序没有崩溃
        with patch.object(sys, 'argv', test_args):
            try:
                cleaner.main()
            except Exception as e:
                self.fail(f"程序在输入目录不存在时崩溃了: {e}")

    def test_complex_selector(self):
        """测试 5: 复杂 CSS 选择器 (如 div > p)"""
        # 创建一个复杂的 HTML
        complex_html = os.path.join(self.test_dir, "complex.html")
        with open(complex_html, 'w', encoding='utf-8') as f:
            f.write("""
            <div class="wrapper">
                <p>Delete me</p>
            </div>
            <p>Keep me</p>
            """)
            
        test_args = ['cleaner.py', '-i', self.test_dir, '-s', 'div.wrapper > p', '-p', 'complex.html']
        
        with patch.object(sys, 'argv', test_args):
            cleaner.main()
            
        with open(complex_html, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        # 检查 div 里的 p 是否没了，但 div 还在
        self.assertTrue(soup.find(class_="wrapper"))
        self.assertEqual(len(soup.select("div.wrapper > p")), 0)
        # 检查外面的 p 还在
        self.assertIsNotNone(soup.find(string="Keep me"))

if __name__ == '__main__':
    unittest.main()