import os
import glob
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Project, ScanTask, Finding
from parsers.sarif_parser import EnhancedSARIFParser

class Command(BaseCommand):
    help = '扫描并导入SARIF报告文件'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            type=str,
            help='指定项目名称，只导入该项目的报告',
        )
        parser.add_argument(
            '--department',
            type=str,
            help='指定部门名称，只导入该部门的报告',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新导入，覆盖已存在的漏洞',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览模式，不实际导入',
        )

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run', False)
        self.force = options.get('force', False)
        project_filter = options.get('project')
        department_filter = options.get('department')
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('=== 预览模式 - 不会实际导入报告 ==='))
        
        self.stdout.write(self.style.SUCCESS('开始扫描SARIF报告文件...'))
        
        # 获取配置的报告路径
        report_base = settings.REPORT_CONFIG['BASE_PATH']
        
        if not os.path.exists(report_base):
            self.stdout.write(self.style.ERROR(f'报告目录不存在: {report_base}'))
            return
        
        # 统计信息
        stats = {
            'files_found': 0,
            'files_processed': 0,
            'findings_imported': 0,
            'findings_skipped': 0,
            'errors': 0
        }
        
        # 创建SARIF解析器
        parser = EnhancedSARIFParser()
        
        # 扫描报告文件 - 支持两种目录结构
        for dept_name in os.listdir(report_base):
            dept_path = os.path.join(report_base, dept_name)
            if not os.path.isdir(dept_path):
                continue
                
            # 部门过滤
            if department_filter and dept_name != department_filter:
                continue

            self.stdout.write(f'\n=== 扫描部门: {dept_name} ===')

            # 方法1: 扫描部门目录下的直接SARIF文件
            dept_sarif_files = []
            for ext in ['*.sarif', '*.json']:
                dept_sarif_files.extend(glob.glob(os.path.join(dept_path, ext)))

            for sarif_file in dept_sarif_files:
                stats['files_found'] += 1

                # 从文件名推断项目名
                filename = os.path.basename(sarif_file)
                project_name = self._extract_project_name(filename)

                if not project_name:
                    self.stdout.write(f'⚠ 无法从文件名推断项目: {filename}')
                    continue

                # 项目过滤
                if project_filter and project_name != project_filter:
                    continue

                # 处理报告文件
                self._process_report_file(sarif_file, dept_name, project_name, parser, stats)

            # 方法2: 扫描部门下的项目子目录
            for item in os.listdir(dept_path):
                item_path = os.path.join(dept_path, item)
                if not os.path.isdir(item_path):
                    continue

                project_name = item

                # 项目过滤
                if project_filter and project_name != project_filter:
                    continue

                # 扫描项目目录下的SARIF文件
                project_sarif_files = []
                for ext in ['*.sarif', '*.json']:
                    project_sarif_files.extend(glob.glob(os.path.join(item_path, '**', ext), recursive=True))

                for sarif_file in project_sarif_files:
                    stats['files_found'] += 1
                    self._process_report_file(sarif_file, dept_name, project_name, parser, stats)
        
        # 显示统计信息
        self.stdout.write(self.style.SUCCESS('\n=== 导入统计 ==='))
        self.stdout.write(f'发现文件: {stats["files_found"]}')
        self.stdout.write(f'处理文件: {stats["files_processed"]}')
        self.stdout.write(f'导入漏洞: {stats["findings_imported"]}')
        self.stdout.write(f'跳过漏洞: {stats["findings_skipped"]}')
        self.stdout.write(f'处理错误: {stats["errors"]}')
        
        if not self.dry_run:
            self.stdout.write(self.style.SUCCESS('\nSARIF报告导入完成！'))
            self.stdout.write('现在可以在管理界面查看导入的漏洞发现。')
        else:
            self.stdout.write('这是预览模式，没有实际导入报告。')
            self.stdout.write('移除 --dry-run 参数来执行实际导入。')

    def _extract_project_name(self, filename):
        """从文件名中提取项目名"""
        # 支持格式: project_tool_report_timestamp.sarif
        # 例如: balance-server_codeql_report_20250708-025734.sarif
        parts = filename.split('_')
        if len(parts) >= 2:
            return parts[0]

        # 如果无法解析，返回去掉扩展名的文件名
        return os.path.splitext(filename)[0]

    def _process_report_file(self, sarif_file, dept_name, project_name, parser, stats):
        """处理单个报告文件"""
        # 检查文件是否为SARIF格式
        if not self._is_sarif_file(sarif_file):
            return

        self.stdout.write(f'处理文件: {os.path.relpath(sarif_file, settings.REPORT_CONFIG["BASE_PATH"])}')
        self.stdout.write(f'  项目: {dept_name}/{project_name}')

        try:
            # 查找项目
            try:
                project = Project.objects.get(name=project_name, department__name=dept_name)
            except Project.DoesNotExist:
                self.stdout.write(f'  ⚠ 项目不存在: {dept_name}/{project_name}')
                return

            # 获取或创建扫描任务
            scan_task, created = ScanTask.objects.get_or_create(
                project=project,
                tool_name='codeql',
                scan_type='SAST',
                defaults={'status': 'completed'}
            )

            if created:
                self.stdout.write(f'  ✓ 创建扫描任务: {scan_task.id}')

            # 检查是否已经导入过
            existing_findings = Finding.objects.filter(scan_task=scan_task).count()
            if existing_findings > 0 and not self.force:
                self.stdout.write(f'  - 跳过已导入的文件 (已有 {existing_findings} 个漏洞)')
                stats['findings_skipped'] += existing_findings
                return

            if self.force and existing_findings > 0:
                if not self.dry_run:
                    Finding.objects.filter(scan_task=scan_task).delete()
                self.stdout.write(f'  ↻ 强制重新导入，删除已有 {existing_findings} 个漏洞')

            # 解析SARIF文件
            if not self.dry_run:
                findings = parser.parse_file(sarif_file, project, scan_task)
                
                # 批量保存Finding对象到数据库
                saved_findings = []
                for finding in findings:
                    try:
                        finding.save()
                        saved_findings.append(finding)
                    except Exception as e:
                        self.stdout.write(f'    ⚠ 保存漏洞失败: {str(e)}')
                
                # 更新扫描任务状态
                scan_task.status = 'completed'
                scan_task.save()
                
                stats['findings_imported'] += len(saved_findings)
                self.stdout.write(f'  ✓ 导入 {len(saved_findings)} 个漏洞')
                if len(saved_findings) != len(findings):
                    self.stdout.write(f'    ⚠ {len(findings) - len(saved_findings)} 个漏洞保存失败')
            else:
                # 预览模式，只计算数量
                findings_count = self._count_sarif_findings(sarif_file)
                stats['findings_imported'] += findings_count
                self.stdout.write(f'  ✓ [预览] 将导入 {findings_count} 个漏洞')

            stats['files_processed'] += 1

        except Exception as e:
            stats['errors'] += 1
            self.stdout.write(f'  ✗ 处理失败: {str(e)}')

    def _is_sarif_file(self, file_path):
        """检查文件是否为SARIF格式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return '$schema' in data and 'sarif' in data.get('$schema', '').lower()
        except:
            return False

    def _count_sarif_findings(self, file_path):
        """计算SARIF文件中的漏洞数量（预览模式用）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            for run in data.get('runs', []):
                for result in run.get('results', []):
                    count += 1
            return count
        except:
            return 0
