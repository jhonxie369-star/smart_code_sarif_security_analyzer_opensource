import json
import logging
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AIAnalysisCache:
    """AI分析缓存管理 - 继承您的缓存逻辑"""
    
    def __init__(self):
        self.cache_prefix = "ai_analysis"
        self.default_timeout = 86400 * 7  # 7天
    
    def _get_cache_key(self, key: str) -> str:
        """生成缓存键"""
        return f"{self.cache_prefix}:{key}"
    
    def get_analysis(self, key: str) -> Optional[Dict]:
        """获取缓存的分析结果"""
        cache_key = self._get_cache_key(key)
        return cache.get(cache_key)
    
    def save_analysis(self, key: str, analysis: Dict, timeout: Optional[int] = None):
        """保存分析结果到缓存"""
        cache_key = self._get_cache_key(key)
        timeout = timeout or self.default_timeout
        cache.set(cache_key, analysis, timeout=timeout)
    
    def clear_cache(self, pattern: Optional[str] = None):
        """清除缓存"""
        if pattern:
            # 这里可以实现模式匹配清除，简化版本直接清除所有
            cache.clear()
        else:
            cache.clear()


class AIAnalyzer:
    """AI分析器 - 继承您的AI分析逻辑"""
    
    def __init__(self):
        self.config = getattr(settings, 'AI_CONFIG', {})
        self.timeout = self.config.get('TIMEOUT', 90)
        self.cache = AIAnalysisCache()
    
    def analyze_single_issue(self, rule_id: str, issue: Dict) -> Dict:
        """分析单个安全问题 - 继承您的实现"""
        return self._analyze_security_issues(rule_id, [issue], is_single=True)
    
    def analyze_batch_issues(self, rule_id: str, issues: List[Dict]) -> Dict:
        """批量分析安全问题 - 继承您的批量分析逻辑"""
        return self._analyze_security_issues(rule_id, issues, is_single=False)
    
    def _analyze_security_issues(self, rule_id: str, results: List[Dict], is_single: bool = False) -> Dict:
        """使用Amazon Q分析安全问题 - 恢复原来的工作逻辑"""
        try:
            # 构建问题摘要
            issues_summary = []
            max_issues = 1 if is_single else 3
            
            for i, result in enumerate(results[:max_issues]):
                location = result.get('location', {})
                source_context = result.get('source_context', {})
                
                issue_detail = f"""问题{i+1}:
- 文件: {location.get('uri', location.get('file_path', 'unknown'))}
- 行号: {location.get('startLine', location.get('line_number', 'unknown'))}
- 描述: {result.get('translated_message', result.get('message', ''))}
- 严重程度: {result.get('severity', 'unknown')}"""
                
                if source_context and source_context.get('lines'):
                    lines = source_context['lines']
                    issue_detail += "\n- 源码上下文:"
                    
                    has_long_lines = False
                    for line in lines[:10]:  # 最多10行
                        marker = ">>> " if line.get('is_target') else "    "
                        content = line.get('content', '')
                        
                        # 处理超长行（如压缩的JS/CSS）
                        if len(content) > 200:
                            has_long_lines = True
                            if line.get('is_target'):
                                # 目标行：显示前100字符 + 省略号 + 后100字符
                                content = content[:100] + " ... [压缩代码已截断] ... " + content[-100:]
                            else:
                                # 非目标行：只显示前100字符
                                content = content[:100] + " ... [行过长已截断]"
                        
                        issue_detail += f"\n  {marker}{line.get('number', '?'):4d}: {content}"
                    
                    if len(lines) > 10:
                        issue_detail += "\n  ... (更多代码已省略)"
                    
                    # 添加超长行警告
                    if has_long_lines:
                        issue_detail += "\n\n⚠️ 注意：检测到源码包含超长行（可能为压缩代码），AI仅分析截取的关键内容，分析结果可能不够全面。建议查看完整源码进行人工审查。"
                
                issues_summary.append(issue_detail)
            
            # 构建提示词
            if is_single:
                # 检查内容长度，调整分析策略
                content_length = len(issues_summary[0])
                if content_length > 3000:
                    analysis_note = "\n\n[AI分析说明: 由于源代码内容较长，本次分析基于关键代码片段进行]"
                else:
                    analysis_note = ""
                    
                prompt = f"""请分析以下代码安全问题，用中文提供简洁的解决方案。

规则ID: {rule_id}
{issues_summary[0]}{analysis_note}

必须严格按以下格式回答：

## 1. 安全风险分析
[简要说明这个漏洞的安全风险和可能的攻击方式]

## 2. 解决方案
[提供具体的修复代码示例和步骤]

## 3. 预防措施
[说明如何在开发中预防此类问题]

请确保回答简洁明了，重点突出实用性。"""
            else:
                issues_text = "\n\n".join(issues_summary)
                prompt = f"""请分析以下多个代码安全问题，用中文提供统一的解决方案。

规则ID: {rule_id}
问题总数: {len(results)}

{issues_text}

必须严格按以下格式回答：

## 1. 问题汇总分析
[总结这些问题的共同特点和安全风险]

## 2. 统一解决方案
[提供通用的修复方法和代码示例]

## 3. 批量修复建议
[说明如何批量处理这类问题]

## 4. 预防措施
[说明如何在开发中预防此类问题]

请确保回答简洁明了，重点突出批量处理的效率。"""
            
            # 调用Amazon Q进行分析
            analysis_result = self._call_amazon_q(prompt)
            
            return {
                'rule_id': rule_id,
                'analysis_type': 'single' if is_single else 'batch',
                'processed_count': len(results),
                'raw_response': analysis_result,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"AI analysis error for rule {rule_id}: {e}")
            return {
                'rule_id': rule_id,
                'analysis_type': 'single' if is_single else 'batch',
                'processed_count': len(results),
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
    
    def _call_amazon_q(self, prompt: str) -> str:
        """调用Amazon Q进行分析 - 继承您的实现"""
        try:
            # 使用subprocess调用q chat命令
            cmd = ['q', 'chat']
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout
            )
            
            stdout, stderr = process.communicate(input=prompt)
            
            if process.returncode == 0:
                return stdout.strip()
            else:
                raise Exception(f"Amazon Q command failed: {stderr}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("Amazon Q analysis timeout")
        except Exception as e:
            logger.error(f"Amazon Q call error: {e}")
            raise


class AIAnalysisService:
    """AI分析服务 - 主要服务类"""
    
    def __init__(self):
        self.analyzer = AIAnalyzer()
        self.cache = AIAnalysisCache()
        self.cache_enabled = getattr(settings, 'AI_CONFIG', {}).get('CACHE_ENABLED', True)
    
    def analyze_finding(self, finding) -> Dict:
        """分析单个漏洞发现"""
        # 生成缓存键
        cache_key = self._generate_cache_key(finding)
        
        # 检查缓存
        if self.cache_enabled:
            cached_result = self.cache.get_analysis(cache_key)
            if cached_result:
                return {
                    'analysis': cached_result,
                    'cached': True,
                    'timestamp': datetime.now().isoformat()
                }
        
        # 准备分析数据
        issue_data = {
            'message': finding.message,
            'translated_message': finding.translated_message,
            'severity': finding.severity,
            'location': {
                'file_path': finding.file_path,
                'line_number': finding.line_number,
                'uri': finding.file_path
            },
            'source_context': finding.source_context
        }
        
        # 执行AI分析
        try:
            analysis = self.analyzer.analyze_single_issue(
                finding.vuln_id_from_tool or 'unknown',
                issue_data
            )
            
            # 缓存结果
            if self.cache_enabled and analysis.get('success'):
                self.cache.save_analysis(cache_key, analysis)
            
            return {
                'analysis': analysis,
                'cached': False,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed for finding {finding.id}: {e}")
            return {
                'error': str(e),
                'cached': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def batch_analyze_findings(self, findings: List, rule_id: str) -> Dict:
        """批量分析漏洞发现"""
        # 生成批量缓存键
        cache_key = f"batch_{rule_id}_{len(findings)}_{hash(str([f.id for f in findings]))}"
        
        # 检查缓存
        if self.cache_enabled:
            cached_result = self.cache.get_analysis(cache_key)
            if cached_result:
                return {
                    'analysis': cached_result,
                    'cached': True,
                    'processed_count': len(findings)
                }
        
        # 准备批量分析数据
        issues_data = []
        for finding in findings:
            issue_data = {
                'message': finding.message,
                'translated_message': finding.translated_message,
                'severity': finding.severity,
                'location': {
                    'file_path': finding.file_path,
                    'line_number': finding.line_number,
                    'uri': finding.file_path
                },
                'source_context': finding.source_context
            }
            issues_data.append(issue_data)
        
        try:
            analysis = self.analyzer.analyze_batch_issues(rule_id, issues_data)
            
            # 缓存结果
            if self.cache_enabled and analysis.get('success'):
                self.cache.save_analysis(cache_key, analysis)
            
            return {
                'analysis': analysis,
                'cached': False,
                'processed_count': len(findings)
            }
            
        except Exception as e:
            logger.error(f"Batch AI analysis failed for rule {rule_id}: {e}")
            return {
                'error': str(e),
                'cached': False,
                'processed_count': 0
            }
    
    def _generate_cache_key(self, finding) -> str:
        """生成漏洞的缓存键"""
        key_data = f"{finding.vuln_id_from_tool}_{finding.file_path}_{finding.line_number}_{finding.message}"
        return hashlib.md5(key_data.encode()).hexdigest()


# 全局AI分析服务实例
ai_analysis_service = AIAnalysisService()
