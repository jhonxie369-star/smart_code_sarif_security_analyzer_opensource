from django.core.management.base import BaseCommand
from core.models import BuildConfig

class Command(BaseCommand):
    help = '初始化默认编译配置'

    def handle(self, *args, **options):
        configs = [
            {
                'name': 'Maven标准配置',
                'language': 'java',
                'project_type': 'maven',
                'build_command': 'env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH mvn clean compile -DskipTests',
                'description': 'Maven项目的标准编译配置',
                'is_default': True,
            },
            {
                'name': 'Gradle标准配置',
                'language': 'java',
                'project_type': 'gradle',
                'build_command': 'env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH ./gradlew build -x test',
                'description': 'Gradle项目的标准编译配置',
                'is_default': False,
            },
            {
                'name': 'NPM标准配置',
                'language': 'javascript',
                'project_type': 'npm',
                'build_command': 'npm install --ignore-scripts --no-audit --no-fund --legacy-peer-deps',
                'description': 'NPM项目的标准安装配置',
                'is_default': True,
            },
            {
                'name': 'Yarn配置',
                'language': 'javascript',
                'project_type': 'yarn',
                'build_command': 'yarn install --ignore-scripts --ignore-engines',
                'description': 'Yarn项目的安装配置',
                'is_default': False,
            },
        ]

        for config_data in configs:
            config, created = BuildConfig.objects.get_or_create(
                name=config_data['name'],
                defaults=config_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'创建编译配置: {config.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'编译配置已存在: {config.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('编译配置初始化完成')
        )