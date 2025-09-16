import json
import os
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.utils import timezone

from core.models import Finding, SeverityManager, Project, ScanTask
from translation.services import translation_service
from core.git_utils import get_line_author, get_file_author

logger = logging.getLogger(__name__)

CWE_REGEX = r"cwe-(\d+)"

# 集成简化通用评分算法
try:
    from .vulnerability_scoring import calculate_universal_vulnerability_score
except ImportError:
    # 如果导入失败，使用默认评分
    def calculate_universal_vulnerability_score(cwe_input, cvss_score=None, owasp_category=None):
        return 5.0, "中危", {'method': 'fallback'}


class EnhancedSARIFParser:
    """增强的SARIF解析器 - 集成DefectDojo逻辑和您的功能"""
    
    def __init__(self):
        self.translation_service = translation_service
        self.severity_manager = SeverityManager()
    
    def parse_file(self, file_path: str, project: Project, scan_task: ScanTask) -> List[Finding]:
        """解析SARIF文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sarif_data = json.load(f)
            
            findings = []
            
            for run in sarif_data.get('runs', []):
                # 获取规则信息
                rules = self._extract_rules(run)
                
                # 处理结果
                for result in run.get('results', []):
                    finding = self._process_result(result, rules, project, scan_task)
                    if finding:
                        findings.append(finding)
            
            logger.info(f"Successfully parsed {len(findings)} findings from {file_path}")
            return findings
            
        except Exception as e:
            logger.error(f"Error parsing SARIF file {file_path}: {e}")
            raise
    
    def _extract_rules(self, run: Dict) -> Dict:
        """提取规则信息"""
        rules = {}
        
        # 从driver中提取规则
        if 'tool' in run and 'driver' in run['tool']:
            driver = run['tool']['driver']
            if 'rules' in driver:
                for rule in driver['rules']:
                    rule_id = rule.get('id', '')
                    if rule_id:
                        rules[rule_id] = rule
        
        return rules
    
    def _process_result(self, result: Dict, rules: Dict, project: Project, scan_task: ScanTask) -> Optional[Finding]:
        """处理单个结果 - 借鉴DefectDojo逻辑"""
        try:
            rule_id = result.get('ruleId', '')
            rule = rules.get(rule_id, {})
            
            # 获取位置信息
            locations = self._extract_locations(result)
            if not locations:
                logger.warning(f"No valid location found for result with rule {rule_id}")
                return None
            
            # 使用第一个位置
            location = locations[0]
            
            # 获取严重程度 - 使用简化通用评分算法
            severity_result = self._get_severity(result, rule)
            if isinstance(severity_result, tuple):
                severity, vulnerability_score, scoring_details = severity_result
            else:
                severity = severity_result
                vulnerability_score = None
                scoring_details = {}
            
            # 获取消息
            message = self._get_message(result, rule)
            
            # 翻译消息 - 继承您的翻译功能
            translated_message = self._translate_message(message)
            
            # 获取源码上下文 - 继承您的源码展示功能
            source_context = self._get_source_context(
                project, location['file_path'], location['line_number']
            )
            
            # 获取git作者信息 - 确保自动扫描也能获取代码负责人
            git_author = self._get_git_author(project, location['file_path'], location['line_number'])
            logger.debug(f"Git author for {location['file_path']}:{location['line_number']}: {git_author}")
            
            # 创建Finding对象
            finding = Finding(
                title=self._get_title(result, rule),
                severity=severity,
                numerical_severity=SeverityManager.get_numerical_severity(severity),
                description=self._get_description(result, rule, location),
                message=message,
                translated_message=translated_message,
                file_path=location['file_path'],
                line_number=location['line_number'],
                column_number=location.get('column_number'),
                source_context=source_context,
                cwe=self._extract_cwe(result, rule),
                project=project,
                scan_task=scan_task,
                code_owner=git_author or project.code_owner or '',
                tags=self._extract_tags(result, rule),
                vuln_id_from_tool=rule_id,
                unique_id_from_tool=self._get_unique_id(result),
                reporter='system',
                date=timezone.now().date()
            )
            
            # 设置评分信息
            if vulnerability_score:
                finding.cvssv3_score = vulnerability_score
            
            # 保存评分详情到metadata
            if scoring_details:
                finding.metadata = {
                    'scoring_details': scoring_details,
                    'scoring_method': 'universal_cwe_scoring'
                }
            
            # 处理CVSS信息 - 借鉴DefectDojo
            self._process_cvss(finding, rule)
            
            return finding
            
        except Exception as e:
            logger.error(f"Error processing result: {e}")
            return None
    
    def _extract_locations(self, result: Dict) -> List[Dict]:
        """提取位置信息"""
        locations = []
        
        for location_data in result.get('locations', []):
            physical_location = location_data.get('physicalLocation', {})
            artifact_location = physical_location.get('artifactLocation', {})
            region = physical_location.get('region', {})
            
            file_path = artifact_location.get('uri', '')
            if not file_path:
                continue
            
            # 清理文件路径
            file_path = file_path.lstrip('/')
            
            location = {
                'file_path': file_path,
                'line_number': region.get('startLine', 1),
                'column_number': region.get('startColumn'),
                'end_line': region.get('endLine'),
                'end_column': region.get('endColumn')
            }
            
            locations.append(location)
        
        return locations
    
    def _get_severity(self, result: Dict, rule: Dict) -> tuple:
        """获取严重程度 - 使用简化通用评分算法"""
        # 1. 提取CWE编号
        cwe_num = self._extract_cwe(result, rule)
        cwe_input = f"CWE-{cwe_num}" if cwe_num else None
        
        # 2. 提取CVSS分数
        cvss_score = None
        if rule and "properties" in rule and "security-severity" in rule["properties"]:
            try:
                cvss_score = float(rule["properties"]["security-severity"])
            except ValueError:
                pass
        
        # 3. 使用简化通用评分算法
        if cwe_input:
            final_score, severity, details = calculate_universal_vulnerability_score(
                cwe_input=cwe_input,
                cvss_score=cvss_score
            )
            return severity, final_score, details
        
        # 4. 回退到原有逻辑
        severity = result.get("level")
        if severity is None and rule:
            if "defaultConfiguration" in rule:
                severity = rule["defaultConfiguration"].get("level")
        
        if severity:
            mapped_severity = SeverityManager.sarif_level_to_severity(severity)
            return mapped_severity, 5.0, {}
        
        if cvss_score:
            mapped_severity = SeverityManager.cvss_to_severity(cvss_score)
            return mapped_severity, cvss_score, {}
        
        return "中危", 5.0, {}  # 默认值
    
    def _get_message(self, result: Dict, rule: Dict) -> str:
        """获取消息"""
        # 优先从result获取消息
        message = result.get('message', {})
        if isinstance(message, dict):
            text = message.get('text', '')
            if text:
                return text
        elif isinstance(message, str):
            return message
        
        # 从rule获取消息
        if rule:
            short_desc = rule.get('shortDescription', {})
            if isinstance(short_desc, dict):
                text = short_desc.get('text', '')
                if text:
                    return text
        
        return "No description available"
    
    def _get_title(self, result: Dict, rule: Dict) -> str:
        """获取标题"""
        # 从rule获取名称
        if rule:
            name = rule.get('name', '')
            if name:
                return name
        
        # 使用rule ID
        rule_id = result.get('ruleId', '')
        if rule_id:
            return rule_id
        
        return "Unknown Issue"
    
    def _get_description(self, result: Dict, rule: Dict, location: Dict) -> str:
        """获取描述"""
        description_parts = []
        
        # 添加消息
        message = self._get_message(result, rule)
        description_parts.append(f"问题描述: {message}")
        
        # 添加位置信息
        description_parts.append(f"文件位置: {location['file_path']}:{location['line_number']}")
        
        # 添加规则信息
        if rule:
            full_desc = rule.get('fullDescription', {})
            if isinstance(full_desc, dict):
                text = full_desc.get('text', '')
                if text:
                    description_parts.append(f"详细说明: {text}")
        
        return "\n\n".join(description_parts)
    
    def _translate_message(self, message: str) -> str:
        """翻译消息 - 继承您的翻译功能"""
        if self.translation_service and self.translation_service.is_available():
            return self.translation_service.translate_text(message)
        return message
    
    def _get_source_context(self, project: Project, file_path: str, line_number: int) -> Dict:
        """获取源码上下文 - 继承您的源码展示功能"""
        try:
            # 构建完整的源码文件路径
            full_path = None
            
            # 情况1: 如果file_path已经是绝对路径
            if file_path.startswith('/'):
                full_path = file_path
            # 情况2: 如果file_path看起来像是从根目录开始但缺少/
            elif file_path.startswith('home/') or file_path.startswith('opt/') or file_path.startswith('usr/'):
                full_path = '/' + file_path
            # 情况3: 使用项目的source_path
            elif project.source_path:
                full_path = os.path.join(project.source_path, file_path.lstrip('/'))
            # 情况4: 尝试从项目路径构建
            else:
                full_path = os.path.join(
                    settings.REPORT_CONFIG['PROJECT_PATH'],
                    project.department.name,
                    project.name,
                    file_path.lstrip('/')
                )
            
            if not full_path or not os.path.exists(full_path):
                logger.debug(f"Source file not found: {full_path}")
                return {}
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            context_lines = 5
            start_line = max(1, line_number - context_lines)
            end_line = min(len(lines), line_number + context_lines)
            
            context = {
                'lines': [],
                'start_line': start_line,
                'end_line': end_line,
                'target_line': line_number
            }
            
            for i in range(start_line - 1, end_line):
                context['lines'].append({
                    'number': i + 1,
                    'content': lines[i].rstrip(),
                    'is_target': i + 1 == line_number
                })
            
            logger.debug(f"Successfully loaded source context from {full_path}")
            return context
            
        except Exception as e:
            logger.error(f"Error reading source file {full_path}: {e}")
            return {}
    
    def _extract_cwe(self, result: Dict, rule: Dict) -> Optional[int]:
        """提取CWE编号"""
        # 从rule的properties中查找
        if rule and "properties" in rule:
            properties = rule["properties"]
            
            # 检查tags
            if "tags" in properties:
                tags = properties["tags"]
                if isinstance(tags, list):
                    for tag in tags:
                        if isinstance(tag, str):
                            match = re.search(CWE_REGEX, tag.lower())
                            if match:
                                return int(match.group(1))
            
            # 检查cwe字段
            if "cwe" in properties:
                cwe_value = properties["cwe"]
                if isinstance(cwe_value, str):
                    match = re.search(r'\d+', cwe_value)
                    if match:
                        return int(match.group())
                elif isinstance(cwe_value, int):
                    return cwe_value
        
        # 从result的properties中查找
        if "properties" in result:
            properties = result["properties"]
            if "cwe" in properties:
                cwe_value = properties["cwe"]
                if isinstance(cwe_value, str):
                    match = re.search(r'\d+', cwe_value)
                    if match:
                        return int(match.group())
                elif isinstance(cwe_value, int):
                    return cwe_value
        
        return None
    
    def _extract_tags(self, result: Dict, rule: Dict) -> List[str]:
        """提取标签"""
        tags = []
        
        # 从rule中提取标签
        if rule and "properties" in rule and "tags" in rule["properties"]:
            rule_tags = rule["properties"]["tags"]
            if isinstance(rule_tags, list):
                tags.extend([str(tag) for tag in rule_tags])
        
        # 添加严重程度标签
        severity_result = self._get_severity(result, rule)
        if isinstance(severity_result, tuple):
            severity = severity_result[0]
        else:
            severity = severity_result
        tags.append(f"severity:{severity.lower()}")
        
        # 添加工具标签
        tags.append("tool:sarif")
        
        return list(set(tags))  # 去重
    
    def _get_git_author(self, project: Project, file_path: str, line_number: int) -> str:
        """从 git 获取代码作者 - 增强错误处理"""
        if not project.source_path:
            logger.debug(f"No source_path for project {project.name}")
            return None
            
        try:
            # 先尝试获取特定行的作者
            author = get_line_author(project.source_path, file_path, line_number)
            if author:
                logger.debug(f"Found line author: {author}")
                return author
                
            # 如果失败，获取文件的最后修改者
            file_author = get_file_author(project.source_path, file_path)
            if file_author:
                logger.debug(f"Found file author: {file_author}")
                return file_author
                
            logger.debug(f"No git author found for {file_path}")
            return None
            
        except Exception as e:
            logger.warning(f"Error getting git author for {file_path}: {e}")
            return None
    
    def _get_code_owner(self, project: Project, file_path: str) -> str:
        """获取代码负责人"""
        # 简单实现，返回项目的代码负责人
        # 后续可以扩展为基于文件路径的更精细控制
        return project.code_owner
    
    def _get_unique_id(self, result: Dict) -> str:
        """获取唯一ID"""
        # 尝试从fingerprints获取
        fingerprints = result.get('fingerprints', {})
        if fingerprints:
            # 返回第一个fingerprint值
            return list(fingerprints.values())[0]
        
        # 生成基于内容的唯一ID
        rule_id = result.get('ruleId', '')
        message = self._get_message(result, {})
        locations = self._extract_locations(result)
        
        if locations:
            location = locations[0]
            unique_content = f"{rule_id}_{location['file_path']}_{location['line_number']}_{message}"
            return str(hash(unique_content))
        
        return str(hash(f"{rule_id}_{message}"))
    
    def _process_cvss(self, finding: Finding, rule: Dict):
        """处理CVSS信息 - 已在_get_severity中处理"""
        # CVSS处理已移至_get_severity方法中的通用评分算法
        pass


def parse_sarif_file(file_path: str, project: Project, scan_task: ScanTask) -> List[Finding]:
    """便捷的SARIF解析函数"""
    parser = EnhancedSARIFParser()
    return parser.parse_file(file_path, project, scan_task)
