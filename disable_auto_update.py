import os
import sys
import platform
import shutil
from colorama import Fore, Style, init
import subprocess
from utils import get_linux_cursor_path, get_default_driver_path, get_default_browser_path
import re
import tempfile
from language import get_translation

# Initialize colorama
init()

# Define emoji constants
EMOJI = {
    "PROCESS": "🔄",
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "FOLDER": "📁",
    "FILE": "📄",
    "STOP": "🛑",
    "CHECK": "✔️"
}

class AutoUpdateDisabler:
    def __init__(self, translator=None):
        self.translator = translator
        self.system = platform.system()
        
        # Get path from configuration file
        config = self._get_config()
        if config:
            if self.system == "Windows":
                self.updater_path = self._get_config_item(config, 'WindowsPaths', 'updater_path', os.path.join(os.getenv("LOCALAPPDATA", ""), "cursor-updater"))
                self.update_yml_path = self._get_config_item(config, 'WindowsPaths', 'update_yml_path', os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app", "update.yml"))
                self.product_json_path = self._get_config_item(config, 'WindowsPaths', 'product_json_path', os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app", "product.json"))
            elif self.system == "Darwin":
                self.updater_path = self._get_config_item(config, 'MacPaths', 'updater_path', os.path.expanduser("~/Library/Application Support/cursor-updater"))
                self.update_yml_path = self._get_config_item(config, 'MacPaths', 'update_yml_path', "/Applications/Cursor.app/Contents/Resources/app-update.yml")
                self.product_json_path = self._get_config_item(config, 'MacPaths', 'product_json_path', "/Applications/Cursor.app/Contents/Resources/app/product.json")
            elif self.system == "Linux":
                self.updater_path = self._get_config_item(config, 'LinuxPaths', 'updater_path', os.path.expanduser("~/.config/cursor-updater"))
                self.update_yml_path = self._get_config_item(config, 'LinuxPaths', 'update_yml_path', os.path.expanduser("~/.config/cursor/resources/app-update.yml"))
                self.product_json_path = self._get_config_item(config, 'LinuxPaths', 'product_json_path', os.path.expanduser("~/.config/cursor/resources/app/product.json"))
        else:
            # If configuration loading fails, use default paths
            self.updater_paths = {
                "Windows": os.path.join(os.getenv("LOCALAPPDATA", ""), "cursor-updater"),
                "Darwin": os.path.expanduser("~/Library/Application Support/cursor-updater"),
                "Linux": os.path.expanduser("~/.config/cursor-updater")
            }
            self.updater_path = self.updater_paths.get(self.system)
            
            self.update_yml_paths = {
                "Windows": os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app", "update.yml"),
                "Darwin": "/Applications/Cursor.app/Contents/Resources/app-update.yml",
                "Linux": os.path.expanduser("~/.config/cursor/resources/app-update.yml")
            }
            self.update_yml_path = self.update_yml_paths.get(self.system)

            self.product_json_paths = {
                "Windows": os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Cursor", "resources", "app", "product.json"),
                "Darwin": "/Applications/Cursor.app/Contents/Resources/app/product.json",
                "Linux": os.path.expanduser("~/.config/cursor/resources/app/product.json")
            }
            self.product_json_path = self.product_json_paths.get(self.system)

    def _get_config_item(self,config, key1, key2, default):
        if not config[key1]:
            return default
        if not config[key1][key2]:
            return default
        return config[key1][key2]
    
    def _get_config(self):
        # Default configuration
        default_config = {
            'Browser': {
                'default_browser': 'chrome',
                'chrome_path': get_default_browser_path('chrome'),
                'chrome_driver_path': get_default_driver_path('chrome'),
                'edge_path': get_default_browser_path('edge'),
                'edge_driver_path': get_default_driver_path('edge'),
                'firefox_path': get_default_browser_path('firefox'),
                'firefox_driver_path': get_default_driver_path('firefox'),
                'brave_path': get_default_browser_path('brave'),
                'brave_driver_path': get_default_driver_path('brave'),
                'opera_path': get_default_browser_path('opera'),
                'opera_driver_path': get_default_driver_path('opera'),
                'operagx_path': get_default_browser_path('operagx'),
                'operagx_driver_path': get_default_driver_path('chrome')  # Opera GX 使用 Chrome 驱动
            },
            'Turnstile': {
                'handle_turnstile_time': '2',
                'handle_turnstile_random_time': '1-3'
            },
            'Timing': {
                'min_random_time': '0.1',
                'max_random_time': '0.8',
                'page_load_wait': '0.1-0.8',
                'input_wait': '0.3-0.8',
                'submit_wait': '0.5-1.5',
                'verification_code_input': '0.1-0.3',
                'verification_success_wait': '2-3',
                'verification_retry_wait': '2-3',
                'email_check_initial_wait': '4-6',
                'email_refresh_wait': '2-4',
                'settings_page_load_wait': '1-2',
                'failed_retry_time': '0.5-1',
                'retry_interval': '8-12',
                'max_timeout': '160'
            },
            'Utils': {
                'enabled_update_check': 'True',
                'enabled_force_update': 'False',
                'enabled_account_info': 'True'
            },
            'OAuth': {
                'show_selection_alert': False,  # 默认不显示选择提示弹窗
                'timeout': 120,
                'max_attempts': 3
            },
            'Token': {
                'refresh_server': 'https://token.cursorpro.com.cn',
                'enable_refresh': True
            }
        }

        # Add system-specific path configuration
        if sys.platform == "win32":
            appdata = os.getenv("APPDATA")
            localappdata = os.getenv("LOCALAPPDATA", "")
            default_config['WindowsPaths'] = {
                'storage_path': os.path.join(appdata, "Cursor", "User", "globalStorage", "storage.json"),
                'sqlite_path': os.path.join(appdata, "Cursor", "User", "globalStorage", "state.vscdb"),
                'machine_id_path': os.path.join(appdata, "Cursor", "machineId"),
                'cursor_path': os.path.join(localappdata, "Programs", "Cursor", "resources", "app"),
                'updater_path': os.path.join(localappdata, "cursor-updater"),
                'update_yml_path': os.path.join(localappdata, "Programs", "Cursor", "resources", "app-update.yml"),
                'product_json_path': os.path.join(localappdata, "Programs", "Cursor", "resources", "app", "product.json")
            }
            # Create storage directory
            os.makedirs(os.path.dirname(default_config['WindowsPaths']['storage_path']), exist_ok=True)
            
        elif sys.platform == "darwin":
            default_config['MacPaths'] = {
                'storage_path': os.path.abspath(os.path.expanduser("~/Library/Application Support/Cursor/User/globalStorage/storage.json")),
                'sqlite_path': os.path.abspath(os.path.expanduser("~/Library/Application Support/Cursor/User/globalStorage/state.vscdb")),
                'machine_id_path': os.path.expanduser("~/Library/Application Support/Cursor/machineId"),
                'cursor_path': "/Applications/Cursor.app/Contents/Resources/app",
                'updater_path': os.path.expanduser("~/Library/Application Support/cursor-updater"),
                'update_yml_path': "/Applications/Cursor.app/Contents/Resources/app-update.yml",
                'product_json_path': "/Applications/Cursor.app/Contents/Resources/app/product.json"
            }
            # Create storage directory
            os.makedirs(os.path.dirname(default_config['MacPaths']['storage_path']), exist_ok=True)
            
        elif sys.platform == "linux":
            # Get the actual user's home directory, handling both sudo and normal cases
            sudo_user = os.environ.get('SUDO_USER')
            current_user = sudo_user if sudo_user else (os.getenv('USER') or os.getenv('USERNAME'))
            
            if not current_user:
                current_user = os.path.expanduser('~').split('/')[-1]
            
            # Handle sudo case
            if sudo_user:
                actual_home = f"/home/{sudo_user}"
                root_home = "/root"
            else:
                actual_home = f"/home/{current_user}"
                root_home = None
            
            if not os.path.exists(actual_home):
                actual_home = os.path.expanduser("~")
            
            # Define base config directory
            config_base = os.path.join(actual_home, ".config")
            
            # Try both "Cursor" and "cursor" directory names in both user and root locations
            cursor_dir = None
            possible_paths = [
                os.path.join(config_base, "Cursor"),
                os.path.join(config_base, "cursor"),
                os.path.join(root_home, ".config", "Cursor") if root_home else None,
                os.path.join(root_home, ".config", "cursor") if root_home else None
            ]
            
            for path in possible_paths:
                if path and os.path.exists(path):
                    cursor_dir = path
                    break
            
            if not cursor_dir:
                print(f"{Fore.YELLOW}{EMOJI['WARNING']} {get_translation('cursor_dir_not_found', dir=config_base)}{Style.RESET_ALL}")
                if root_home:
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('also_checked_dir', dir=f'{root_home}/.config')}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('cursor_install_reminder')}{Style.RESET_ALL}")
            
            # Define Linux paths using the found cursor directory
            storage_path = os.path.abspath(os.path.join(cursor_dir, "User/globalStorage/storage.json")) if cursor_dir else ""
            storage_dir = os.path.dirname(storage_path) if storage_path else ""
            
            # Verify paths and permissions
            try:
                # Check storage directory
                if storage_dir and not os.path.exists(storage_dir):
                    print(f"{Fore.YELLOW}{EMOJI['WARNING']} {get_translation('storage_dir_not_found', dir=storage_dir)}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('cursor_install_reminder')}{Style.RESET_ALL}")
                
                # Check storage.json with more detailed verification
                if storage_path and os.path.exists(storage_path):
                    # Get file stats
                    try:
                        stat = os.stat(storage_path)
                        print(f"{Fore.GREEN}{EMOJI['INFO']} {get_translation('storage_file_found', path=storage_path)}{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}{EMOJI['INFO']} {get_translation('file_size', size=stat.st_size)}{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}{EMOJI['INFO']} {get_translation('file_permissions', permissions=oct(stat.st_mode & 0o777))}{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}{EMOJI['INFO']} {get_translation('file_owner', owner=stat.st_uid)}{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}{EMOJI['INFO']} {get_translation('file_group', group=stat.st_gid)}{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('file_stats_error', error=str(e))}{Style.RESET_ALL}")
                    
                    # Check if file is readable and writable
                    if not os.access(storage_path, os.R_OK | os.W_OK):
                        print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('permission_denied', path=storage_path)}{Style.RESET_ALL}")
                        if sudo_user:
                            print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('try_chown', user=sudo_user, path=storage_path)}{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('try_chmod', path=storage_path)}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('try_chown', user=current_user, path=storage_path)}{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('try_chmod', path=storage_path)}{Style.RESET_ALL}")
                    
                    # Try to read the file to verify it's not corrupted
                    try:
                        with open(storage_path, 'r') as f:
                            content = f.read()
                            if not content.strip():
                                print(f"{Fore.YELLOW}{EMOJI['WARNING']} {get_translation('storage_file_empty', path=storage_path)}{Style.RESET_ALL}")
                                print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('file_corrupted')}{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {get_translation('storage_file_valid')}{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('storage_file_read_error', error=str(e))}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('file_corrupted_reinstall')}{Style.RESET_ALL}")
                elif storage_path:
                    print(f"{Fore.YELLOW}{EMOJI['WARNING']} {get_translation('storage_file_not_found', path=storage_path)}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('cursor_install_reminder')}{Style.RESET_ALL}")
                
            except (OSError, IOError) as e:
                print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('linux_paths_error', error=str(e))}{Style.RESET_ALL}")
            
            # Define all paths using the found cursor directory
            default_config['LinuxPaths'] = {
                'storage_path': storage_path,
                'sqlite_path': os.path.abspath(os.path.join(cursor_dir, "User/globalStorage/state.vscdb")) if cursor_dir else "",
                'machine_id_path': os.path.join(cursor_dir, "machineid") if cursor_dir else "",
                'cursor_path': get_linux_cursor_path(),
                'updater_path': os.path.join(config_base, "cursor-updater"),
                'update_yml_path': os.path.join(cursor_dir, "resources/app-update.yml") if cursor_dir else "",
                'product_json_path': os.path.join(cursor_dir, "resources/app/product.json") if cursor_dir else ""
            }

        return default_config

    def _remove_update_url(self):
        """删除更新URL"""
        try:
            original_stat = os.stat(self.product_json_path)
            original_mode = original_stat.st_mode
            original_uid = original_stat.st_uid
            original_gid = original_stat.st_gid

            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
                with open(self.product_json_path, "r", encoding="utf-8") as product_json_file:
                    content = product_json_file.read()
                
                patterns = {
                    r"https://api2.cursor.sh/aiserver.v1.AuthService/DownloadUpdate": r"",
                    r"https://api2.cursor.sh/updates": r"",
                    r"http://cursorapi.com/updates": r"",
                }
                
                for pattern, replacement in patterns.items():
                    content = re.sub(pattern, replacement, content)

                tmp_file.write(content)
                tmp_path = tmp_file.name

            shutil.copy2(self.product_json_path, self.product_json_path + ".old")
            shutil.move(tmp_path, self.product_json_path)

            os.chmod(self.product_json_path, original_mode)
            if os.name != "nt":
                os.chown(self.product_json_path, original_uid, original_gid)

            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {get_translation('file_modified')}{Style.RESET_ALL}")
            return True

        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('file_modify_failed', error=str(e))}{Style.RESET_ALL}")
            if "tmp_path" in locals():
                os.unlink(tmp_path)
            return False

    def _kill_cursor_processes(self):
        """终止所有 Cursor 进程"""
        try:
            print(f"{Fore.CYAN}{EMOJI['PROCESS']} {get_translation('terminating_cursor_processes')}{Style.RESET_ALL}")
            
            if self.system == "Windows":
                subprocess.run(['taskkill', '/F', '/IM', 'Cursor.exe', '/T'], capture_output=True)
            else:
                subprocess.run(['pkill', '-f', 'Cursor'], capture_output=True)
                
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {get_translation('cursor_processes_terminated')}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('process_termination_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def _remove_updater_directory(self):
        """删除更新程序目录"""
        try:
            updater_path = self.updater_path
            if not updater_path:
                raise OSError(get_translation('unsupported_os'))

            print(f"{Fore.CYAN}{EMOJI['FOLDER']} {get_translation('removing_updater_directory')}{Style.RESET_ALL}")
            
            if os.path.exists(updater_path):
                try:
                    if os.path.isdir(updater_path):
                        shutil.rmtree(updater_path)
                    else:
                        os.remove(updater_path)
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {get_translation('updater_directory_removed')}{Style.RESET_ALL}")
                except PermissionError:
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('updater_directory_locked', path=updater_path)}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('directory_removal_failed', error=str(e))}{Style.RESET_ALL}")
            return True
    
    def _clear_update_yml_file(self):
        """清空更新配置文件"""
        try:
            update_yml_path = self.update_yml_path
            if not update_yml_path:
                raise OSError(get_translation('unsupported_os'))
            
            print(f"{Fore.CYAN}{EMOJI['FILE']} {get_translation('clearing_update_config')}{Style.RESET_ALL}")
            
            if os.path.exists(update_yml_path):
                try:
                    with open(update_yml_path, 'w') as f:
                        f.write('')
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {get_translation('update_config_cleared')}{Style.RESET_ALL}")
                except PermissionError:
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('update_config_locked')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('update_config_not_exist')}{Style.RESET_ALL}")
            return True
                
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('clear_config_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def _create_blocking_file(self):
        """创建阻止文件"""
        try:
            # 检查 updater_path
            updater_path = self.updater_path
            if not updater_path:
                raise OSError(get_translation('unsupported_os_with_name', system=self.system))

            print(f"{Fore.CYAN}{EMOJI['FILE']} {get_translation('creating_blocking_files')}{Style.RESET_ALL}")
            
            # 创建 updater_path 阻止文件
            try:
                os.makedirs(os.path.dirname(updater_path), exist_ok=True)
                open(updater_path, 'w').close()
                
                # 设置 updater_path 为只读
                if self.system == "Windows":
                    os.system(f'attrib +r "{updater_path}"')
                else:
                    os.chmod(updater_path, 0o444)  # 设置为只读
                
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {get_translation('blocking_file_created', path=updater_path)}{Style.RESET_ALL}")
            except PermissionError:
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('blocking_file_locked')}{Style.RESET_ALL}")
            
            # 检查 update_yml_path
            update_yml_path = self.update_yml_path
            if update_yml_path and os.path.exists(os.path.dirname(update_yml_path)):
                try:
                    # 创建 update_yml_path 阻止文件
                    with open(update_yml_path, 'w') as f:
                        f.write(get_translation('update_config_content'))
                    
                    # 设置 update_yml_path 为只读
                    if self.system == "Windows":
                        os.system(f'attrib +r "{update_yml_path}"')
                    else:
                        os.chmod(update_yml_path, 0o444)  # 设置为只读
                    
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {get_translation('update_config_locked_success', path=update_yml_path)}{Style.RESET_ALL}")
                except PermissionError:
                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {get_translation('update_config_already_locked')}{Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('create_blocking_file_failed', error=str(e))}{Style.RESET_ALL}")
            return True  # 返回 True 以继续执行后续步骤

    def disable_auto_update(self):
        """禁用自动更新"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {get_translation('starting_disable_update')}{Style.RESET_ALL}")
            
            # 1. 终止进程
            if not self._kill_cursor_processes():
                return False
                
            # 2. 删除目录 - 即使失败也继续执行
            self._remove_updater_directory()
                
            # 3. 清空更新配置文件
            if not self._clear_update_yml_file():
                return False
                
            # 4. 创建阻止文件
            if not self._create_blocking_file():
                return False
                
            # 5. 从 product.json 移除更新 URL
            if not self._remove_update_url():
                return False
                
            print(f"{Fore.GREEN}{EMOJI['CHECK']} {get_translation('auto_update_disabled')}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {get_translation('disable_update_failed', error=str(e))}{Style.RESET_ALL}")
            return False

def run(translator=None):
    """方便直接调用禁用功能的函数"""
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['STOP']} {get_translation('disable_cursor_auto_update_title')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    disabler = AutoUpdateDisabler(translator)
    disabler.disable_auto_update()

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {get_translation('press_enter_continue')}")

if __name__ == "__main__":
    run(None) 