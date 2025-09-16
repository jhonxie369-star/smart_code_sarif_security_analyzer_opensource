import os
import subprocess
import logging
from datetime import datetime
from django.conf import settings
from .models import Project, ScanTask
from parsers.sarif_parser import parse_sarif_file
from .scanners.codeql import CodeQLEngine
from .scanners.semgrep import SemgrepEngine

logger = logging.getLogger(__name__)

class AutoScanner:
    """自动扫描器 - 支持Git克隆和自动扫描"""
    
    def __init__(self, project):
        self.project = project
        self.config = settings.AUTO_SCAN_CONFIG
        self.work_dir = os.path.join(self.config['WORK_DIR'], f'scan_{project.id}')
        
        if not self.config['ENABLED']:
            raise Exception("自动扫描功能未启用")
        
    def clone_repository(self, git_url, branch='main'):
        """克隆Git仓库"""
        try:
            os.makedirs(self.work_dir, exist_ok=True)
            
            # 目标目录
            dept_name = self.project.department.name
            project_name = self.project.name
            target_dir = os.path.join(self.config['PROJECT_DIR'], dept_name, project_name)
            
            # 如果目录已存在，检查是否为Git仓库
            if os.path.exists(target_dir):
                # 检查是否为Git仓库
                git_check = subprocess.run(f"cd {target_dir} && git status", shell=True, capture_output=True)
                if git_check.returncode == 0:
                    # 是Git仓库，执行pull
                    cmd = f"cd {target_dir} && git pull origin {branch}"
                else:
                    # 不是Git仓库，删除目录重新克隆
                    subprocess.run(f"rm -rf {target_dir}", shell=True)
                    os.makedirs(os.path.dirname(target_dir), exist_ok=True)
                    cmd = f"git clone -b {branch} {git_url} {target_dir}"
            else:
                os.makedirs(os.path.dirname(target_dir), exist_ok=True)
                cmd = f"git clone -b {branch} {git_url} {target_dir}"
                
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Git操作失败: {result.stderr}")
                
            return target_dir
        except Exception as e:
            logger.error(f"Git操作失败: {e}")
            raise
            
    def check_git_updates(self, git_url, branch='main'):
        """检查Git更新"""
        dept_name = self.project.department.name
        project_name = self.project.name
        target_dir = os.path.join(self.config['PROJECT_DIR'], dept_name, project_name)
        
        if not os.path.exists(target_dir):
            return True  # 需要克隆
            
        try:
            # 获取本地和远程提交
            cmd = f"cd {target_dir} && git fetch origin {branch} && git rev-parse HEAD && git rev-parse origin/{branch}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return True  # 错误时重新克隆
                
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                local_commit = lines[0]
                remote_commit = lines[1]
                return local_commit != remote_commit
                
            return True
        except Exception:
            return True
            
    def detect_language(self, source_path):
        """检测项目语言"""
        if os.path.exists(os.path.join(source_path, 'pom.xml')):
            return 'java'
        elif os.path.exists(os.path.join(source_path, 'package.json')):
            return 'javascript'
        elif any(f.endswith('.php') for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))):
            return 'php'
        return None
        
    def get_scanner_engine(self, language):
        """获取扫描引擎"""
        engines = {
            'java': CodeQLEngine('java', self.project),
            'javascript': CodeQLEngine('javascript', self.project),
            'php': SemgrepEngine(self.project)
        }
        
        engine = engines.get(language)
        if not engine:
            raise Exception(f"不支持的语言: {language}")
        return engine
        
    def run_scan(self, source_path, language, scan_task=None):
        """执行扫描"""
        logs = []
        
        def log_callback(message):
            log_line = f"{datetime.now().strftime('%H:%M:%S')} {message}"
            logs.append(log_line)
            if scan_task:
                scan_task.scan_log = '\n'.join(logs)
                scan_task.save(update_fields=['scan_log'])
        
        # 按部门/项目结构组织报告输出目录
        dept_name = self.project.department.name
        project_name = self.project.name
        
        # 检查是否已有部门目录，如果有就直接使用
        reports_base = self.config['OUTPUT_DIR']
        existing_dept_dirs = [d for d in os.listdir(reports_base) 
                             if os.path.isdir(os.path.join(reports_base, d)) and project_name in os.listdir(os.path.join(reports_base, d))]
        
        if existing_dept_dirs:
            dept_name = existing_dept_dirs[0]  # 使用已存在的部门目录名
            
        output_dir = os.path.join(self.config['OUTPUT_DIR'], dept_name, project_name)
        os.makedirs(output_dir, exist_ok=True)
        
        engine = self.get_scanner_engine(language)
        return engine.scan(source_path, output_dir, log_callback)
        
    def execute_scan(self, git_url, branch='main', scan_task=None, language=None):
        # 保存git_url供后续使用
        self.git_url = git_url
        """执行扫描逻辑（使用已存在的任务）"""
        try:
            # 1. 更新任务状态
            if scan_task:
                scan_task.status = 'running'
                scan_task.save()
            else:
                # 如果没有传入任务，创建一个
                scan_task = ScanTask.objects.create(
                    project=self.project,
                    tool_name='auto',
                    scan_type='full',
                    status='running'
                )
            
            # 2. 克隆/更新代码
            logger.info(f"开始克隆/更新仓库: {git_url}")
            source_path = self.clone_repository(git_url, branch)
            
            # 3. 检测语言
            if language:
                # 使用用户指定的语言
                detected_language = language
                logger.info(f"使用指定语言: {language}")
            else:
                # 自动检测语言
                detected_language = self.detect_language(source_path)
                if not detected_language:
                    raise Exception("无法检测项目语言类型")
                logger.info(f"检测到项目语言: {detected_language}")
                
            scan_task.tool_name = f"codeql-{detected_language}" if detected_language != 'php' else 'semgrep'
            scan_task.save()
            
            # 4. 执行扫描
            logger.info(f"开始扫描项目: {source_path}")
            sarif_file = self.run_scan(source_path, detected_language, scan_task)
            
            # 5. 解析报告
            logger.info(f"解析扫描报告: {sarif_file}")
            from core.models import Finding
            findings = parse_sarif_file(sarif_file, self.project, scan_task)
            Finding.objects.bulk_create(findings)
            
            # 6. 更新任务状态
            scan_task.status = 'completed'
            scan_task.report_file = sarif_file
            scan_task.total_findings = len(findings)
            scan_task.save()
            
            # 7. 清理临时文件
            subprocess.run(f"rm -rf {self.work_dir}", shell=True)
            subprocess.run(f"rm -rf {os.path.join(self.config['WORK_DIR'], 'codeql-db-*')}", shell=True)
            
            # 8. 更新项目信息
            self.project.source_path = source_path
            
            # 获取Git项目所属人信息（个人）
            try:
                # 从 Git 配置获取项目所属人（当前用户配置）
                owner_cmd = f"cd {source_path} && git config --get user.name && git config --get user.email"
                result = subprocess.run(owner_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        name = lines[0].strip()
                        email = lines[1].strip()
                        if name and email:
                            self.project.code_owner = f"{name} <{email}>"
                
            except Exception as e:
                logger.warning(f"获取Git项目所属人失败: {e}")
            
            self.project.save()
            
            return {
                'success': True,
                'scan_task_id': scan_task.id,
                'findings_count': len(findings),
                'report_file': sarif_file
            }
            
        except Exception as e:
            logger.error(f"自动扫描失败: {e}")
            if scan_task:
                scan_task.status = 'failed'
                scan_task.error_message = str(e)
                scan_task.save()
            
            # 清理临时文件
            subprocess.run(f"rm -rf {self.work_dir}", shell=True)
            subprocess.run(f"rm -rf {os.path.join(self.config['WORK_DIR'], 'codeql-db-*')}", shell=True)
            
            return {
                'success': False,
                'error': str(e),
                'scan_task_id': scan_task.id if scan_task else None
            }
    
    def auto_scan(self, git_url, branch='main'):
        """完整的自动扫描流程（兼容旧接口）"""
        return self.execute_scan(git_url, branch)