# 完整的漏洞评分计算方法

## 🎯 系统概述

这是一个**通用CWE评分系统**，能够为CodeQL扫描到的**所有CWE类型**计算准确的风险评分。

### 核心特性
- ✅ **全覆盖**: 支持CodeQL能扫到的所有CWE和漏洞类型
- ✅ **权威基础**: 基于CWE Top 25 2024 + OWASP Top 10 2025
- ✅ **分级赋分**: Top 25精确评分，其他CWE按威胁类型分级
- ✅ **智能映射**: 自动识别规则ID并映射到对应CWE
- ✅ **可扩展**: 新CWE自动归类，无需手动维护

## 📊 评分算法架构

```
最终评分 = CWE基础分 + OWASP权重 + CVSS校准
```

### 1. CWE基础分计算

#### A. CWE Top 25 2024 精确评分
```python
# Top 25使用精确排名评分
if rank <= 5:      # 极高风险 (9.0-10.0)
    score = 9.0 + (6 - rank) * 0.2
elif rank <= 10:   # 高风险 (8.0-9.0)  
    score = 8.0 + (11 - rank) * 0.2
elif rank <= 15:   # 中高风险 (7.0-8.0)
    score = 7.0 + (16 - rank) * 0.2
elif rank <= 20:   # 中等风险 (6.0-7.0)
    score = 6.0 + (21 - rank) * 0.2
else:              # 中低风险 (5.0-6.0)
    score = 5.0 + (26 - rank) * 0.2
```

**CWE Top 25 2024 关键排名:**
| CWE | 排名 | 基础分 | 威胁类型 |
|-----|------|--------|----------|
| CWE-79 | 1 | 10.0 | XSS |
| CWE-787 | 2 | 9.8 | 缓冲区溢出 |
| CWE-89 | 3 | 9.6 | SQL注入 |
| CWE-352 | 4 | **6.8** | CSRF (特殊处理) |
| CWE-22 | 5 | 9.2 | 路径遍历 |
| CWE-78 | 7 | 8.8 | 命令注入 |
| CWE-94 | 11 | 8.2 | 代码注入 |
| CWE-918 | 19 | 6.4 | SSRF |

#### B. 非Top 25 CWE分级评分
```python
# 威胁级别分级
CRITICAL (9.0-10.0):  代码执行、系统控制
HIGH (7.5-8.9):       数据泄露、权限提升、XSS
MEDIUM_HIGH (6.0-7.4): 信息泄露、SSRF、拒绝服务
MEDIUM (4.5-5.9):     配置问题、弱加密
LOW (2.0-4.4):        信息收集、轻微问题
```

**威胁分级示例:**
- **CRITICAL**: CWE-120(缓冲区溢出), CWE-415(双重释放), CWE-502(反序列化)
- **HIGH**: CWE-269(权限管理), CWE-287(认证失败), CWE-327(弱加密)
- **MEDIUM_HIGH**: CWE-200(信息泄露), CWE-400(资源消耗), CWE-601(重定向)
- **MEDIUM**: CWE-117(日志注入), CWE-319(明文传输), CWE-730(正则DoS)
- **LOW**: CWE-459(资源泄露), CWE-754(错误处理)

### 2. OWASP Top 10 2025 权重

```python
OWASP_WEIGHTS = {
    # A03:2025 – Injection (高权重 +1.2)
    'CWE-79': 1.2,   # XSS
    'CWE-89': 1.2,   # SQL注入
    'CWE-78': 1.2,   # 命令注入
    'CWE-94': 1.2,   # 代码注入
    
    # A01:2025 – Broken Access Control (+1.0)
    'CWE-22': 1.0,   # 路径遍历
    'CWE-862': 1.0,  # 缺失授权
    'CWE-352': 0.3,  # CSRF (降权)
    
    # A10:2025 – SSRF (+0.8)
    'CWE-918': 0.8,  # SSRF
    
    # 其他权重较低 (+0.2-0.6)
    'CWE-200': 0.4,  # 信息泄露
    'CWE-327': 0.6,  # 弱加密
}
```

### 3. 特殊处理规则

```python
# CSRF特殊处理 - 配置级威胁
'CWE-352': {
    'base_score': 6.8,  # 强制基础分
    'reason': '配置级威胁，非代码执行类风险'
}
```

## 🔧 规则ID到CWE映射

### 支持的扫描工具规则

#### CodeQL Java (50+ 规则)
```python
'java/sql-injection': 'CWE-89',
'java/path-injection': 'CWE-22', 
'java/xss': 'CWE-79',
'java/csrf-unprotected-request-type': 'CWE-352',
'java/ssrf': 'CWE-918',
'java/code-injection': 'CWE-94',
'java/log-injection': 'CWE-117',
# ... 更多规则
```

#### CodeQL JavaScript (30+ 规则)
```python
'js/xss': 'CWE-79',
'js/code-injection': 'CWE-94',
'js/prototype-pollution-utility': 'CWE-78',
'js/client-side-unvalidated-url-redirection': 'CWE-79',
# ... 更多规则
```

#### Semgrep PHP (20+ 规则)
```python
'php.lang.security.injection.tainted-sql-string': 'CWE-89',
'php.lang.security.injection.echoed-request': 'CWE-79',
'php.lang.security.injection.tainted-filename': 'CWE-918',
# ... 更多规则
```

### 智能CWE提取算法

1. **直接CWE格式**: `CWE-79`, `cwe-89`, `CWE_352`
2. **精确规则映射**: 99个预定义规则映射
3. **模糊匹配**: 部分规则名匹配
4. **关键词启发式**: 基于漏洞类型关键词
5. **默认处理**: 未识别规则使用5.0默认分

## 📈 实际计算示例

### 示例1: XSS漏洞 (js/xss)
```
规则ID: js/xss
↓ 映射
CWE-79 (XSS)
↓ 计算
基础分: 10.0 (Top 25 #1)
OWASP权重: +1.2 (A03注入攻击)
最终评分: 10.0 + 1.2 = 11.2 → 10.0 (上限)
严重程度: 高危
```

### 示例2: CSRF漏洞 (java/csrf-unprotected-request-type)
```
规则ID: java/csrf-unprotected-request-type
↓ 映射  
CWE-352 (CSRF)
↓ 计算
特殊处理: 6.8 (配置级威胁)
OWASP权重: +0.3 (降权处理)
最终评分: 6.8 + 0.3 = 7.1
严重程度: 中危
```

### 示例3: 未知规则 (custom-security-check)
```
规则ID: custom-security-check
↓ 映射
无法识别CWE
↓ 计算
默认评分: 5.0
严重程度: 中危
```

### 示例4: 直接CWE (CWE-117)
```
规则ID: CWE-117
↓ 映射
CWE-117 (日志注入)
↓ 计算
威胁分级: MEDIUM (4.5-5.9)
基础分: 5.2
OWASP权重: +0.2
最终评分: 5.2 + 0.2 = 5.4
严重程度: 低危
```

## 🛠️ 使用方法

### Python API调用

```python
from rule_to_cwe_mapping import score_vulnerability_from_rule

# 单个漏洞评分
score, severity, details = score_vulnerability_from_rule(
    rule_id='java/sql-injection',
    cvss_score=8.5,
    language='Java',
    tool='CodeQL'
)

print(f"评分: {score:.1f}")
print(f"严重程度: {severity}")
print(f"CWE: {details['cwe_id']}")
print(f"评分依据: {details['base_reason']}")
```

### 批量处理

```python
from rule_to_cwe_mapping import batch_score_vulnerabilities

vulnerabilities = [
    {'rule_id': 'java/sql-injection', 'cvss_score': 8.5},
    {'rule_id': 'js/xss', 'language': 'JavaScript'},
    {'rule_id': 'CWE-352', 'cvss_score': 7.2},
]

results = batch_score_vulnerabilities(vulnerabilities)

for result in results:
    print(f"{result['rule_id']}: {result['final_score']:.1f} ({result['final_severity']})")
```

## 📊 系统覆盖率

- **总规则数**: 99个预定义规则
- **CWE覆盖数**: 38个不同CWE类型  
- **支持工具**: CodeQL (Java/JavaScript), Semgrep (PHP)
- **威胁分级**: 5个级别，覆盖所有CWE类型
- **自动扩展**: 新CWE自动归类到对应威胁级别

## 🎯 严重程度划分

| 评分范围 | 严重程度 | 修复时间 | 典型CWE |
|----------|----------|----------|---------|
| ≥8.0 | **高危** | 7天内 | CWE-79, CWE-89, CWE-22, CWE-78, CWE-94 |
| 5.5-7.9 | **中危** | 30天内 | CWE-352, CWE-918, CWE-200, CWE-327 |
| <5.5 | **低危** | 90天内 | CWE-117, CWE-532, CWE-459 |

## 🔍 2024年主要变化

### CWE排名变化影响
- **CWE-22** (路径遍历): 排名上升 → 评分提高到9.2
- **CWE-918** (SSRF): 排名大幅下降 → 评分降到6.4  
- **CWE-352** (CSRF): 保持特殊处理 → 评分维持6.8
- **CWE-79** (XSS): 排名第1 → 评分最高10.0

### 评分分布优化
- **高危漏洞**: 更精准识别真正的高风险威胁
- **中危漏洞**: 合理分级，避免过度评估
- **低危漏洞**: 包含轻微问题，但仍需关注

## 💡 最佳实践

1. **优先修复高危漏洞** (≥8.0分)
2. **关注数量多的中危漏洞**
3. **定期更新评分体系** (跟随CWE年度更新)
4. **结合实际环境** (考虑网络架构和防护)
5. **持续监控** (关注新攻击技术)

## 🔗 技术实现

- **核心算法**: `universal_cwe_scoring.py`
- **规则映射**: `rule_to_cwe_mapping.py`  
- **威胁分级**: 基于MITRE CWE分类
- **权威数据**: CWE Top 25 2024 + OWASP Top 10 2025

---

**这个评分系统确保了CodeQL能扫到的所有CWE都能得到合理的风险评分，无论是Top 25中的热门威胁，还是长尾的特殊CWE类型。**
