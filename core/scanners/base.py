import os
import subprocess
from abc import ABC, abstractmethod
from django.conf import settings

class BaseScanEngine(ABC):
    """扫描引擎基类"""
    
    def __init__(self):
        self.config = settings.AUTO_SCAN_CONFIG
        
    @abstractmethod
    def scan(self, source_path, output_path):
        """执行扫描"""
        pass
        
    @abstractmethod
    def get_language(self):
        """获取支持的语言"""
        pass
        
    def run_command(self, cmd, cwd=None, timeout=None, log_callback=None):
        """执行命令"""
        timeout = timeout or self.config['TIMEOUT']
        
        if log_callback:
            # 将命令中的绝对路径转为相对路径显示
            display_cmd = self._format_cmd_for_display(cmd)
            log_callback(f"[CMD] {display_cmd}")
        
        # 使用Popen实现实时输出
        import subprocess
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=cwd, text=True, bufsize=1, universal_newlines=True
        )
        
        stdout_lines = []
        stderr_lines = []
        
        # 实时读取输出
        import select
        import time
        start_time = time.time()
        
        while True:
            if timeout and time.time() - start_time > timeout:
                process.kill()
                raise Exception(f"命令执行超时: {timeout}秒")
                
            # 检查进程是否结束
            if process.poll() is not None:
                break
                
            # 读取可用的输出
            ready, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
            
            for stream in ready:
                line = stream.readline()
                if line:
                    line = line.rstrip()
                    if stream == process.stdout:
                        stdout_lines.append(line)
                        if log_callback:
                            log_callback(f"[OUT] {line}")
                    else:
                        stderr_lines.append(line)
                        if log_callback:
                            # npm WARN 显示为警告而不是错误
                            if 'npm WARN' in line:
                                log_callback(f"[WARN] {line}")
                            # Semgrep 正常输出信息
                            elif any(keyword in line for keyword in ['Scan Status', 'Scan Summary', 'Scanning', 'findings', 'Rules run', 'Targets scanned', 'Parsed lines', 'Scan skipped', 'Files larger than', 'Files matching', 'Scan was limited', 'detailed list', 'Ran', 'rules on', 'files:', 'Too many findings']):
                                formatted_line = self._format_log_for_display(line)
                                log_callback(f"[INFO] {formatted_line}")
                            else:
                                formatted_line = self._format_log_for_display(line)
                                log_callback(f"[ERR] {formatted_line}")
        
        # 读取剩余输出
        remaining_stdout, remaining_stderr = process.communicate()
        if remaining_stdout:
            for line in remaining_stdout.strip().split('\n'):
                if line:
                    stdout_lines.append(line)
                    if log_callback:
                        log_callback(f"[OUT] {line}")
        if remaining_stderr:
            for line in remaining_stderr.strip().split('\n'):
                if line:
                    stderr_lines.append(line)
                    if log_callback:
                        # 过滤CodeQL编译查询计划的正常信息
                        if 'Compiling query plan for' in line:
                            log_callback(f"[INFO] {line.replace('[ERR]', '').strip()}")
                        # npm WARN 显示为警告而不是错误
                        elif 'npm WARN' in line:
                            log_callback(f"[WARN] {line}")
                        # Semgrep 正常输出信息
                        elif any(keyword in line for keyword in ['Scan Status', 'Scan Summary', 'Scanning', 'findings', 'Rules run', 'Targets scanned', 'Parsed lines', 'Scan skipped', 'Files larger than', 'Files matching', 'Scan was limited', 'detailed list', 'Ran', 'rules on', 'files:', 'Too many findings', '✅', '◦', '•', '📢']):
                            formatted_line = self._format_log_for_display(line)
                            log_callback(f"[INFO] {formatted_line}")
                        else:
                            formatted_line = self._format_log_for_display(line)
                            log_callback(f"[ERR] {formatted_line}")
        
        if process.returncode != 0:
            raise Exception(f"命令执行失败: {''.join(stderr_lines)}")
            
        # 返回类似subprocess.run的结果
        class Result:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
                
        return Result(process.returncode, '\n'.join(stdout_lines), '\n'.join(stderr_lines))
    
    def _format_cmd_for_display(self, cmd):
        """格式化命令显示，将绝对路径转为相对路径"""
        from django.conf import settings
        base_dir = str(settings.BASE_DIR)
        
        # 替换命令中的绝对路径
        display_cmd = cmd.replace(base_dir, '.')
        
        return display_cmd
    
    def _format_log_for_display(self, log_line):
        """格式化日志显示，将绝对路径转为相对路径"""
        from django.conf import settings
        base_dir = str(settings.BASE_DIR)
        
        # 替换日志中的绝对路径
        formatted_line = log_line.replace(base_dir, '.')
        
        return formatted_line