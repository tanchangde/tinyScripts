import unittest
import os
import sys
import shutil
import tempfile
import platform
from unittest.mock import patch, MagicMock

# 假设你的脚本名为 html2pdf.py
import html2pdf

class TestBrowserPath(unittest.TestCase):
    """测试 find_browser_executable 函数"""

    @patch('os.path.exists')
    @patch('platform.system')
    def test_find_browser_windows_chrome(self, mock_system, mock_exists):
        """测试 Windows 平台自动查找 Chrome"""
        mock_system.return_value = "Windows"
        # 模拟第一个路径(Chrome)存在
        mock_exists.side_effect = lambda p: "Chrome" in p 
        
        path = html2pdf.find_browser_executable()
        self.assertIn("chrome.exe", path)

    @patch('os.path.exists')
    @patch('platform.system')
    def test_find_browser_linux(self, mock_system, mock_exists):
        """测试 Linux 平台自动查找"""
        mock_system.return_value = "Linux"
        mock_exists.side_effect = lambda p: "/usr/bin/google-chrome" in p
        
        path = html2pdf.find_browser_executable()
        self.assertEqual(path, "/usr/bin/google-chrome")

    def test_user_specified_path(self):
        """测试用户指定路径"""
        # 创建一个假的临时可执行文件
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            pass
        try:
            path = html2pdf.find_browser_executable(user_path=tf.name)
            self.assertEqual(path, tf.name)
        finally:
            os.remove(tf.name)

    @patch('sys.exit')
    @patch('os.path.exists')
    @patch('builtins.print')  # <--- 新增：拦截 print
    def test_browser_not_found(self, mock_print, mock_exists, mock_exit): # <--- 新增参数
        """测试找不到浏览器时退出"""
        mock_exists.return_value = False 
        
        html2pdf.find_browser_executable()
        
        # 我们可以顺便验证一下是不是真的打印了错误信息
        mock_print.assert_called_with("错误: 未找到浏览器，请使用 --browser-path 指定。")
        mock_exit.assert_called_with(1)

class TestFileOperations(unittest.TestCase):
    """测试 collect_files 和 calculate_output_path"""

    def setUp(self):
        # 创建临时目录结构用于测试 collect_files
        self.test_dir = tempfile.mkdtemp()
        self.sub_dir = os.path.join(self.test_dir, "subdir")
        os.mkdir(self.sub_dir)
        
        # 创建文件: root/a.html, root/b.txt, root/subdir/c.htm
        with open(os.path.join(self.test_dir, "a.html"), 'w') as f: f.write("content")
        with open(os.path.join(self.test_dir, "b.txt"), 'w') as f: f.write("content")
        with open(os.path.join(self.sub_dir, "c.htm"), 'w') as f: f.write("content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_collect_files_single_file(self):
        """测试指定单文件"""
        input_file = os.path.join(self.test_dir, "a.html")
        files = html2pdf.collect_files(input_file)
        self.assertEqual(files, [input_file])

    def test_collect_files_directory_flat(self):
        """测试目录（非递归）"""
        files = html2pdf.collect_files(self.test_dir, recursive=False)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith("a.html"))

    def test_collect_files_directory_recursive(self):
        """测试目录（递归）"""
        files = html2pdf.collect_files(self.test_dir, recursive=True)
        self.assertEqual(len(files), 2)
        filenames = [os.path.basename(f) for f in files]
        self.assertIn("a.html", filenames)
        self.assertIn("c.htm", filenames)

    def test_calculate_output_path(self):
        """测试输出路径计算逻辑"""
        input_f = "test.html"
        
        # 1. 默认情况
        res = html2pdf.calculate_output_path(input_f, None, None)
        self.assertEqual(res, "test.pdf")
        
        # 2. 指定输出文件名
        res = html2pdf.calculate_output_path(input_f, "custom.pdf", None)
        self.assertEqual(res, "custom.pdf")
        
        # 3. 指定输出目录
        res = html2pdf.calculate_output_path(input_f, None, "out_dir")
        # 注意：这里我们不管 path separator 是 / 还是 \
        self.assertTrue(res.endswith(os.path.join("out_dir", "test.pdf")))

class TestConversionLogic(unittest.TestCase):
    """测试 run_conversion 函数"""

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_conversion_success(self, mock_makedirs, mock_exists, mock_run):
        """测试正常转换流程"""
        # 模拟输出文件不存在 (需要生成)
        mock_exists.return_value = False 
        
        # 模拟 subprocess 返回成功
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_run.return_value = mock_res

        result = html2pdf.run_conversion("chrome", "in.html", "out.pdf")
        
        self.assertTrue(result)
        # 验证是否构建了正确的命令
        args, _ = mock_run.call_args
        cmd_list = args[0]
        self.assertIn("--headless", cmd_list)
        self.assertIn("file:///", cmd_list[-1] if platform.system() == "Windows" else cmd_list[-1])

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_skip_existing(self, mock_exists, mock_run):
        """测试跳过已存在文件"""
        # 模拟输出文件已存在
        mock_exists.return_value = True 
        
        result = html2pdf.run_conversion("chrome", "in.html", "out.pdf", force_overwrite=False)
        
        self.assertTrue(result) # 函数返回 True 表示处理（或跳过）成功
        mock_run.assert_not_called() # 关键：不应调用浏览器

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_force_overwrite(self, mock_makedirs, mock_exists, mock_run):
        """测试强制覆盖"""
        mock_exists.return_value = True # 文件已存在
        
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_run.return_value = mock_res
        
        result = html2pdf.run_conversion("chrome", "in.html", "out.pdf", force_overwrite=True)
        
        self.assertTrue(result)
        mock_run.assert_called() # 即使文件存在，也应调用浏览器

class TestMainFlow(unittest.TestCase):
    """测试 main 函数的主流程"""

    @patch('html2pdf.run_conversion')
    @patch('html2pdf.collect_files')
    @patch('html2pdf.find_browser_executable')
    def test_main_single_file(self, mock_find, mock_collect, mock_run):
        """测试单文件处理流程"""
        mock_find.return_value = "dummy_browser"
        mock_collect.return_value = ["test.html"]
        mock_run.return_value = True
        
        test_args = ['html2pdf.py', 'test.html']
        with patch.object(sys, 'argv', test_args):
            html2pdf.main()
            
        # 验证是否对该文件调用了转换
        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        self.assertEqual(args[1], "test.html") # input
        self.assertEqual(args[2], "test.pdf")  # default output

    @patch('html2pdf.run_conversion')
    @patch('html2pdf.collect_files')
    @patch('html2pdf.find_browser_executable')
    def test_main_multiple_files_with_o_warning(self, mock_find, mock_collect, mock_run):
        """测试多文件输入时使用 -o 参数的警告逻辑"""
        mock_find.return_value = "dummy_browser"
        # 模拟收集到了2个文件
        mock_collect.return_value = ["a.html", "b.html"]
        mock_run.return_value = True
        
        # 用户指定了 -o single.pdf，但这在多文件时是不合法的
        test_args = ['html2pdf.py', '.', '-o', 'single.pdf']
        
        with patch.object(sys, 'argv', test_args):
            # 捕获 stdout 看看有没有打印警告
            from io import StringIO
            captured_output = StringIO()
            sys.stdout = captured_output
            
            html2pdf.main()
            
            sys.stdout = sys.__stdout__ # 恢复 stdout
            output = captured_output.getvalue()
            
            # --- 修改点：匹配新的警告文案 ---
            # 现在的文案是 "已忽略 -o/--output 参数"
            self.assertIn("已忽略 -o/--output 参数", output)
            # ---------------------------
            
        # 验证 run_conversion 被调用了两次
        self.assertEqual(mock_run.call_count, 2)
        
        # 验证输出路径没有使用 'single.pdf'，而是使用了默认的 .pdf
        # 检查第一次调用
        args1 = mock_run.call_args_list[0][0] 
        self.assertNotEqual(args1[2], "single.pdf")
        self.assertTrue(args1[2].endswith(".pdf"))

    @patch('html2pdf.run_conversion')
    @patch('html2pdf.collect_files')
    @patch('html2pdf.find_browser_executable')
    def test_main_output_dir(self, mock_find, mock_collect, mock_run):
        """测试指定输出目录"""
        mock_find.return_value = "dummy_browser"
        mock_collect.return_value = ["test.html"]
        mock_run.return_value = True
        
        test_args = ['html2pdf.py', 'test.html', '-d', 'pdfs']
        with patch.object(sys, 'argv', test_args):
            html2pdf.main()
            
        args = mock_run.call_args[0]
        # 验证输出路径包含 output_dir
        self.assertTrue("pdfs" in args[2])

if __name__ == '__main__':
    unittest.main()