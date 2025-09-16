import os
from datetime import datetime
from .base import BaseScanEngine

class CodeQLEngine(BaseScanEngine):
    """CodeQL扫描引擎"""
    
    def __init__(self, language, project=None):
        super().__init__()
        self.language = language
        self.project = project
        self.codeql_bin = self.config['TOOLS']['CODEQL_BIN']
        self.codeql_rules = self.config['TOOLS']['CODEQL_RULES']
        
    def get_language(self):
        return self.language
        
    def scan(self, source_path, output_path, log_callback=None):
        """执行CodeQL扫描"""
        project_name = os.path.basename(source_path)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        sarif_file = os.path.join(output_path, f'{project_name}_codeql_{self.language}_{timestamp}.sarif')
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        db_path = os.path.join(self.config['WORK_DIR'], f'codeql-db-{unique_id}')
        
        if log_callback:
            from django.conf import settings
            relative_path = os.path.relpath(source_path, settings.BASE_DIR)
            log_callback(f"[INFO] 开始{self.language}扫描: {relative_path}")
        
        if self.language == 'java':
            self._scan_java(source_path, db_path, sarif_file, log_callback)
        elif self.language == 'javascript':
            self._scan_javascript(source_path, db_path, sarif_file, log_callback)
            
        if log_callback:
            from django.conf import settings
            relative_sarif = os.path.relpath(sarif_file, settings.BASE_DIR)
            log_callback(f"[INFO] 扫描完成: {relative_sarif}")
            
        return sarif_file
        
    def _get_build_command(self, source_path, language):
        """获取编译命令"""
        # 如果项目设置了自定义编译命令，优先使用
        if self.project and self.project.build_command and self.project.build_command.strip():
            return self.project.build_command.strip()
        
        # 默认命令
        jdk_home = self.config['TOOLS']['JDK_HOME']
        if language == 'java':
            return f"env JAVA_HOME={jdk_home} PATH={jdk_home}/bin:$PATH mvn clean compile -DskipTests"
        elif language == 'javascript':
            return "npm install --ignore-scripts --no-audit --no-fund --legacy-peer-deps"
        
        return ""
    
    def _scan_java(self, source_path, db_path, sarif_file, log_callback=None):
        """Java项目扫描"""
        build_command = self._get_build_command(source_path, 'java')
        
        compile_cmd = f"cd {source_path} && {build_command}"
        self.run_command(compile_cmd, log_callback=log_callback)
        
        create_cmd = f"{self.codeql_bin} database create {db_path} --language=java --source-root={source_path} --overwrite --command='{build_command}'"
        self.run_command(create_cmd, log_callback=log_callback)
        
        analyze_cmd = f"{self.codeql_bin} database analyze {db_path} --format=sarifv2.1.0 --output={sarif_file} --threads=8 --ram=7000 --search-path={self.codeql_rules} {self.codeql_rules}/java/ql/src/codeql-suites/java-security-extended.qls"
        self.run_command(analyze_cmd, log_callback=log_callback)
        
    def _scan_javascript(self, source_path, db_path, sarif_file, log_callback=None):
        """JavaScript项目扫描"""
        build_command = self._get_build_command(source_path, 'javascript')
        
        if build_command and build_command.strip():
            compile_cmd = f"cd {source_path} && {build_command}"
            self.run_command(compile_cmd, log_callback=log_callback, timeout=900)
        elif os.path.exists(os.path.join(source_path, 'package.json')):
            import subprocess
            cleanup_cmd = f"cd {source_path} && rm -f package-lock.json"
            subprocess.run(cleanup_cmd, shell=True)
            
            install_cmd = f"cd {source_path} && npm install --ignore-scripts --no-audit --no-fund --legacy-peer-deps"
            self.run_command(install_cmd, log_callback=log_callback, timeout=900)
        
        create_cmd = f"{self.codeql_bin} database create {db_path} --language=javascript --source-root={source_path} --overwrite"
        self.run_command(create_cmd, log_callback=log_callback, timeout=900)
        
        analyze_cmd = f"{self.codeql_bin} database analyze {db_path} --format=sarifv2.1.0 --output={sarif_file} --threads=8 --ram=7000 --search-path={self.codeql_rules} {self.codeql_rules}/javascript/ql/src/codeql-suites/javascript-security-extended.qls"
        self.run_command(analyze_cmd, log_callback=log_callback)