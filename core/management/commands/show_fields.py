from django.core.management.base import BaseCommand
from core.field_definitions import (
    DEPARTMENT_FIELDS, PROJECT_FIELDS, SCAN_TASK_FIELDS, 
    FINDING_FIELDS, FINDING_NOTE_FIELDS, STATUS_HISTORY_FIELDS,
    CHOICES, EXTENSION_SUGGESTIONS, USAGE_INSTRUCTIONS
)

class Command(BaseCommand):
    help = '显示所有模型的字段定义'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='指定要查看的模型 (department, project, scan_task, finding, finding_note, status_history)',
        )
        parser.add_argument(
            '--choices',
            action='store_true',
            help='显示所有选择项定义',
        )
        parser.add_argument(
            '--extensions',
            action='store_true',
            help='显示扩展字段建议',
        )
        parser.add_argument(
            '--usage',
            action='store_true',
            help='显示使用说明',
        )

    def handle(self, *args, **options):
        if options['usage']:
            self.stdout.write(self.style.SUCCESS('=== 使用说明 ==='))
            self.stdout.write(USAGE_INSTRUCTIONS)
            return

        if options['choices']:
            self.stdout.write(self.style.SUCCESS('=== 选择项定义 ==='))
            for choice_name, choice_values in CHOICES.items():
                self.stdout.write(f'\n{choice_name}:')
                for value, label in choice_values:
                    self.stdout.write(f'  {value}: {label}')
            return

        if options['extensions']:
            self.stdout.write(self.style.SUCCESS('=== 扩展字段建议 ==='))
            for model_name, suggestions in EXTENSION_SUGGESTIONS.items():
                self.stdout.write(f'\n{model_name}:')
                for suggestion in suggestions:
                    self.stdout.write(f'  - {suggestion}')
            return

        model = options.get('model', '').lower()
        
        if model == 'department':
            self._show_model_fields('Department', DEPARTMENT_FIELDS)
        elif model == 'project':
            self._show_model_fields('Project', PROJECT_FIELDS)
        elif model == 'scan_task':
            self._show_model_fields('ScanTask', SCAN_TASK_FIELDS)
        elif model == 'finding':
            self._show_model_fields('Finding', FINDING_FIELDS)
        elif model == 'finding_note':
            self._show_model_fields('FindingNote', FINDING_NOTE_FIELDS)
        elif model == 'status_history':
            self._show_model_fields('StatusHistory', STATUS_HISTORY_FIELDS)
        else:
            # 显示所有模型的字段
            self.stdout.write(self.style.SUCCESS('=== 所有模型字段定义 ==='))
            self._show_model_fields('Department', DEPARTMENT_FIELDS)
            self._show_model_fields('Project', PROJECT_FIELDS)
            self._show_model_fields('ScanTask', SCAN_TASK_FIELDS)
            self._show_model_fields('Finding', FINDING_FIELDS)
            self._show_model_fields('FindingNote', FINDING_NOTE_FIELDS)
            self._show_model_fields('StatusHistory', STATUS_HISTORY_FIELDS)

    def _show_model_fields(self, model_name, fields):
        self.stdout.write(f'\n=== {model_name} 模型字段 ===')
        for field_name, field_definition in fields.items():
            self.stdout.write(f'{field_name}: {field_definition}')
        self.stdout.write(f'字段总数: {len(fields)}')
