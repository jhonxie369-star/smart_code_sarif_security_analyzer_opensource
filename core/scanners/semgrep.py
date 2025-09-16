import os
from datetime import datetime
from .base import BaseScanEngine

class SemgrepEngine(BaseScanEngine):
    """Semgrep扫描引擎"""
    
    def __init__(self, project=None):
        super().__init__()
        self.project = project
    
    def get_language(self):
        return 'php'
    
    def _get_build_command(self, source_path):
        """获取PHP编译命令"""
        # 如果项目设置了自定义编译命令，优先使用
        if self.project and self.project.build_command and self.project.build_command.strip():
            return self.project.build_command.strip()
        
        # PHP默认编译命令
        if os.path.exists(os.path.join(source_path, 'composer.json')):
            return "composer install --no-dev --optimize-autoloader"
        
        return ""
        
    def scan(self, source_path, output_path, log_callback=None):
        """执行Semgrep扫描"""
        project_name = os.path.basename(source_path)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        sarif_file = os.path.join(output_path, f'{project_name}_semgrep_{timestamp}.sarif')
        
        if log_callback:
            from django.conf import settings
            relative_path = os.path.relpath(source_path, settings.BASE_DIR)
            log_callback(f"[INFO] 开始PHP扫描: {relative_path}")
        
        # 执行PHP编译命令（如果有）
        build_command = self._get_build_command(source_path)
        if build_command:
            if log_callback:
                log_callback(f"[INFO] 执行PHP编译: {build_command}")
            compile_cmd = f"cd {source_path} && {build_command}"
            self.run_command(compile_cmd, log_callback=log_callback, timeout=600)
        
        semgrep_bin = self.config['TOOLS']['SEMGREP_BIN']
        cmd = f"{semgrep_bin} --config=p/php --sarif --output={sarif_file} {source_path}"
        
        self.run_command(cmd, log_callback=log_callback)
        
        if log_callback:
            from django.conf import settings
            relative_sarif = os.path.relpath(sarif_file, settings.BASE_DIR)
            log_callback(f"[INFO] 扫描完成: {relative_sarif}")
            
        return sarif_file