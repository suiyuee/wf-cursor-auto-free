import os
import sys
import platform
import subprocess
import time
import psutil
from logger import logging
from language import get_translation

class CursorStarter:
    """
    启动 Cursor 应用程序的类
    """
    def __init__(self):
        self.system = platform.system()
        self.cursor_paths = self._get_cursor_paths()
        
    def _get_cursor_paths(self):
        """获取不同操作系统下的 Cursor 可执行文件路径"""
        paths = {}
        
        if self.system == "Windows":
            localappdata = os.getenv("LOCALAPPDATA", "")
            paths["executable"] = os.path.join(localappdata, "Programs", "Cursor", "Cursor.exe")
            
        elif self.system == "Darwin":  # macOS
            paths["executable"] = "/Applications/Cursor.app/Contents/MacOS/Cursor"
            
        elif self.system == "Linux":
            # 尝试几个常见的 Linux 安装位置
            possible_paths = [
                "/usr/bin/cursor",
                "/usr/local/bin/cursor",
                "/opt/cursor/cursor",
                os.path.expanduser("~/.local/bin/cursor")
            ]
            
            # 寻找存在的路径
            for path in possible_paths:
                if os.path.exists(path):
                    paths["executable"] = path
                    break
            
            # 如果没有找到，使用常见路径
            if "executable" not in paths:
                paths["executable"] = "/usr/bin/cursor"
        
        return paths
    
    def _is_cursor_running(self):
        """检查 Cursor 进程是否已经在运行"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() in ['cursor.exe', 'cursor']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def start_cursor(self, wait_time=5):
        """
        启动 Cursor 应用程序
        
        Args:
            wait_time (int): 等待 Cursor 启动的最大时间（秒）
            
        Returns:
            bool: 是否成功启动
        """
        try:
            # 检查是否已经运行
            if self._is_cursor_running():
                logging.info("Cursor 已经在运行中")
                return True
            
            # 获取可执行文件路径
            executable = self.cursor_paths.get("executable", "")
            
            if not executable or not os.path.exists(executable):
                logging.error(f"找不到 Cursor 可执行文件: {executable}")
                return False
            
            logging.info(f"正在启动 Cursor: {executable}")
            
            # 使用适当的方法启动 Cursor，确保作为独立进程运行
            if self.system == "Windows":
                # 使用 startupinfo 隐藏命令行窗口，启动独立进程
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                
                # 不使用 shell=True，并分离进程
                subprocess.Popen(
                    executable, 
                    startupinfo=startupinfo,
                    shell=False,  # 不使用 shell
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # 分离进程
                )
            elif self.system == "Darwin":
                # 在 macOS 上，使用 open 命令启动应用
                subprocess.Popen(["open", "-a", "Cursor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:  # Linux
                # 在 Linux 上启动分离的进程
                subprocess.Popen(
                    [executable], 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True  # 创建新会话，分离进程
                )
            
            # 等待进程启动
            start_time = time.time()
            while time.time() - start_time < wait_time:
                if self._is_cursor_running():
                    logging.info("Cursor 已成功启动")
                    return True
                time.sleep(0.5)
            
            logging.warning(f"启动超时，但进程可能仍在初始化中")
            return False
            
        except Exception as e:
            logging.error(f"启动 Cursor 时发生错误: {str(e)}")
            return False

def StartCursor(wait_time=5):
    """
    启动 Cursor 的便捷函数
    
    Args:
        wait_time (int): 等待 Cursor 启动的最大时间（秒）
        
    Returns:
        bool: 是否成功启动
    """
    starter = CursorStarter()
    return starter.start_cursor(wait_time)

if __name__ == "__main__":
    # 直接运行此脚本时执行
    logging.info("正在启动 Cursor...")
    success = StartCursor()
    
    if success:
        print("Cursor 已成功启动")
    else:
        print("启动 Cursor 失败，请检查应用程序是否正确安装")
    
    input("按 Enter 键继续...") 