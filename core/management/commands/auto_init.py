import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from core.models import Department, Project, ScanTask
from core.field_definitions import CHOICES

class Command(BaseCommand):
    help = '自动初始化部门、项目和扫描任务 - 支持增量更新和清理'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='清理数据库中存在但文件系统中不存在的项目',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览模式，不实际执行操作',
        )
        parser.add_argument(
            '--import-reports',
            action='store_true',
            help='初始化完成后自动导入SARIF报告',
        )
        parser.add_argument(
            '--force-import',
            action='store_true',
            help='强制重新导入已存在的报告',
        )

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run', False)
        self.clean_mode = options.get('clean', False)
        self.import_reports = options.get('import_reports', False)
        self.force_import = options.get('force_import', False)
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('=== 预览模式 - 不会实际执行操作 ==='))
        
        self.stdout.write(self.style.SUCCESS('开始自动初始化...'))
        
        # 获取配置的路径
        project_base = settings.REPORT_CONFIG['PROJECT_PATH']
        report_base = settings.REPORT_CONFIG['BASE_PATH']
        
        # 统计信息
        stats = {
            'departments_created': 0,
            'departments_existing': 0,
            'projects_created': 0,
            'projects_existing': 0,
            'projects_cleaned': 0,
            'scan_tasks_created': 0,
            'scan_tasks_existing': 0
        }
        
        # 收集文件系统中的部门和项目
        fs_departments = {}
        if os.path.exists(project_base):
            for dept_name in os.listdir(project_base):
                dept_path = os.path.join(project_base, dept_name)
                if os.path.isdir(dept_path):
                    fs_departments[dept_name] = []
                    for project_name in os.listdir(dept_path):
                        project_path = os.path.join(dept_path, project_name)
                        if os.path.isdir(project_path):
                            fs_departments[dept_name].append({
                                'name': project_name,
                                'path': project_path
                            })
        
        # 处理部门和项目
        for dept_name, projects in fs_departments.items():
            # 创建或获取部门
            if not self.dry_run:
                department, created = Department.objects.get_or_create(
                    name=dept_name,
                    defaults={
                        'description': f'自动发现的部门: {dept_name}',
                        'lead': 'admin'
                    }
                )
            else:
                department = Department.objects.filter(name=dept_name).first()
                created = department is None
            
            if created:
                stats['departments_created'] += 1
                self.stdout.write(f'✓ 创建部门: {dept_name}')
            else:
                stats['departments_existing'] += 1
                self.stdout.write(f'- 部门已存在: {dept_name}')
            
            # 处理部门下的项目
            for project_info in projects:
                project_name = project_info['name']
                project_path = project_info['path']
                
                # 检查项目是否已存在
                if not self.dry_run:
                    existing_project = Project.objects.filter(
                        name=project_name, 
                        department=department
                    ).first()
                else:
                    existing_project = Project.objects.filter(
                        name=project_name, 
                        department__name=dept_name
                    ).first() if not created else None
                
                if existing_project:
                    stats['projects_existing'] += 1
                    self.stdout.write(f'  - 项目已存在: {project_name} (部门: {dept_name})')
                    
                    # 更新项目路径（如果有变化）
                    if not self.dry_run and existing_project.source_path != project_path:
                        existing_project.source_path = project_path
                        existing_project.report_path = os.path.join(report_base, dept_name, project_name)
                        existing_project.save()
                        self.stdout.write(f'    ↻ 更新项目路径: {project_name}')
                    
                    project = existing_project
                else:
                    # 创建新项目
                    if not self.dry_run:
                        project = Project.objects.create(
                            name=project_name,
                            department=department,
                            description=f'自动发现的项目: {project_name}',
                            source_path=project_path,
                            report_path=os.path.join(report_base, dept_name, project_name),
                            code_owner='admin',
                            business_criticality='medium'
                        )
                    
                    stats['projects_created'] += 1
                    self.stdout.write(f'  ✓ 创建项目: {project_name} (部门: {dept_name})')
                    project = None  # 在dry_run模式下
                
                # 创建默认扫描任务（如果项目是新创建的或不存在扫描任务）
                if not self.dry_run and project:
                    scan_task, task_created = ScanTask.objects.get_or_create(
                        project=project,
                        tool_name='codeql',
                        scan_type='SAST',
                        defaults={
                            'status': 'pending'
                        }
                    )
                    
                    if task_created:
                        stats['scan_tasks_created'] += 1
                        self.stdout.write(f'    ✓ 创建扫描任务: CodeQL扫描 (项目: {project_name})')
                    else:
                        stats['scan_tasks_existing'] += 1
                        self.stdout.write(f'    - 扫描任务已存在: CodeQL扫描 (项目: {project_name})')
        
        # 清理模式：删除数据库中存在但文件系统中不存在的项目
        if self.clean_mode:
            self.stdout.write(self.style.WARNING('\n=== 清理模式：检查需要删除的项目 ==='))
            
            all_db_projects = Project.objects.select_related('department').all()
            for db_project in all_db_projects:
                dept_name = db_project.department.name
                project_name = db_project.name
                
                # 检查文件系统中是否存在
                project_exists_in_fs = (
                    dept_name in fs_departments and 
                    any(p['name'] == project_name for p in fs_departments[dept_name])
                )
                
                if not project_exists_in_fs:
                    if not self.dry_run:
                        # 删除相关的扫描任务
                        scan_tasks_count = ScanTask.objects.filter(project=db_project).count()
                        ScanTask.objects.filter(project=db_project).delete()
                        
                        # 删除项目
                        db_project.delete()
                        
                        stats['projects_cleaned'] += 1
                        self.stdout.write(f'  ✗ 删除项目: {project_name} (部门: {dept_name}) - 文件系统中不存在')
                        if scan_tasks_count > 0:
                            self.stdout.write(f'    ↳ 同时删除了 {scan_tasks_count} 个扫描任务')
                    else:
                        stats['projects_cleaned'] += 1
                        self.stdout.write(f'  ✗ [预览] 将删除项目: {project_name} (部门: {dept_name}) - 文件系统中不存在')
            
            # 清理空部门
            empty_departments = Department.objects.filter(project__isnull=True)
            for empty_dept in empty_departments:
                if not self.dry_run:
                    empty_dept.delete()
                    self.stdout.write(f'  ✗ 删除空部门: {empty_dept.name}')
                else:
                    self.stdout.write(f'  ✗ [预览] 将删除空部门: {empty_dept.name}')
        
        # 显示统计信息
        self.stdout.write(self.style.SUCCESS('\n=== 操作统计 ==='))
        self.stdout.write(f'部门: 创建 {stats["departments_created"]}, 已存在 {stats["departments_existing"]}')
        self.stdout.write(f'项目: 创建 {stats["projects_created"]}, 已存在 {stats["projects_existing"]}, 清理 {stats["projects_cleaned"]}')
        self.stdout.write(f'扫描任务: 创建 {stats["scan_tasks_created"]}, 已存在 {stats["scan_tasks_existing"]}')
        
        self.stdout.write(self.style.SUCCESS('\n自动初始化完成！'))
        
        # 自动导入报告（如果启用）
        if self.import_reports and not self.dry_run:
            self.stdout.write(self.style.SUCCESS('\n=== 开始自动导入SARIF报告 ==='))
            try:
                import_args = []
                if self.force_import:
                    import_args.append('--force')
                
                call_command('import_reports', *import_args)
                self.stdout.write(self.style.SUCCESS('✓ SARIF报告导入完成'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ 报告导入失败: {str(e)}'))
        elif self.import_reports and self.dry_run:
            self.stdout.write(self.style.WARNING('\n=== [预览] 将执行SARIF报告导入 ==='))
            try:
                import_args = ['--dry-run']
                if self.force_import:
                    import_args.append('--force')
                
                call_command('import_reports', *import_args)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ 报告导入预览失败: {str(e)}'))
        
        if not self.dry_run:
            self.stdout.write('\n现在你可以：')
            self.stdout.write('1. 访问 http://localhost:7000/admin/ 查看创建的部门和项目')
            if self.import_reports:
                self.stdout.write('2. 查看导入的漏洞发现和分析结果')
                self.stdout.write('3. 使用AI分析功能获取修复建议')
                self.stdout.write('4. 查看中英文对照的漏洞描述')
            else:
                self.stdout.write(f'2. 将SARIF报告放入对应的报告目录 (如: {report_base}/部门名/项目名/)')
                self.stdout.write('3. 运行 python manage.py import_reports 导入报告')
                self.stdout.write('4. 通过API导入报告或使用管理界面上传')
            self.stdout.write('5. 查看 core/field_definitions.py 了解所有可用字段')
            self.stdout.write('')
            self.stdout.write('管理命令：')
            self.stdout.write('  python manage.py auto_init --clean --import-reports     # 清理并导入报告')
            self.stdout.write('  python manage.py auto_init --import-reports --force-import  # 强制重新导入')
            self.stdout.write('  python manage.py auto_init --dry-run --import-reports   # 预览完整流程')
            self.stdout.write('  python manage.py import_reports --dry-run               # 单独预览报告导入')
        else:
            self.stdout.write('这是预览模式，没有实际执行操作。')
            self.stdout.write('移除 --dry-run 参数来执行实际操作。')
