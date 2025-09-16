import logging
from typing import Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TranslationService:
    """翻译服务 - 继承您的argostranslate实现"""
    
    def __init__(self):
        self.available = False
        self.translator = None
        self.config = getattr(settings, 'TRANSLATION_CONFIG', {})
        self.cache_enabled = self.config.get('CACHE_ENABLED', True)
        self.from_lang = self.config.get('FROM_LANG', 'en')
        self.to_lang = self.config.get('TO_LANG', 'zh')
        
        self._init_translator()
    
    def _init_translator(self):
        """初始化翻译器"""
        try:
            import argostranslate.package
            import argostranslate.translate
            
            # 检查是否已安装翻译包
            installed_packages = argostranslate.package.get_installed_packages()
            self.available = any(
                p.from_code == self.from_lang and p.to_code == self.to_lang 
                for p in installed_packages
            )
            
            if self.available:
                self.translator = argostranslate.translate
                logger.info("✓ Translation service initialized successfully")
            else:
                logger.warning("⚠ Translation package not installed. Run install_translation.py first")
                
        except ImportError as e:
            logger.error(f"⚠ Argos Translate not available: {e}")
    
    def translate_text(self, text: str, from_lang: Optional[str] = None, to_lang: Optional[str] = None) -> str:
        """翻译文本 - 继承您的翻译逻辑和修正规则"""
        if not text or not text.strip():
            return text
        
        if not self.available:
            logger.debug("Translation service not available, returning original text")
            return text
        
        from_lang = from_lang or self.from_lang
        to_lang = to_lang or self.to_lang
        
        # 检查缓存
        if self.cache_enabled:
            cache_key = f"translation:{hash(text)}:{from_lang}:{to_lang}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
        
        try:
            translated = self.translator.translate(text, from_lang, to_lang)
            if translated and translated != text:
                # 继承您的修正规则
                translated = self._fix_common_errors(translated)
                
                # 缓存结果
                if self.cache_enabled:
                    cache.set(cache_key, translated, timeout=86400)  # 24小时
                
                return translated
            
            return text
            
        except Exception as e:
            logger.error(f"Translation error for text '{text[:50]}...': {e}")
            return text
    
    def _fix_common_errors(self, text: str) -> str:
        """修正常见翻译错误 - 继承您的修正规则"""
        corrections = {
            '饼干': 'cookie',
            '保守派': 'cookie', 
            '饿干': 'cookie',
            # 可扩展更多修正规则
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # 保持技术术语不变
        tech_terms = ['CSRF', 'HTTP', 'URL', 'API', 'XSS', 'SQL', 'JSON', 'XML', 'HTML', 'CSS', 'JWT']
        for term in tech_terms:
            # 将小写的技术术语恢复为大写
            text = text.replace(term.lower(), term)
            
        return text
    
    def batch_translate(self, texts: list, from_lang: Optional[str] = None, to_lang: Optional[str] = None) -> list:
        """批量翻译"""
        if not self.available:
            return texts
        
        results = []
        for text in texts:
            translated = self.translate_text(text, from_lang, to_lang)
            results.append(translated)
        
        return results
    
    def is_available(self) -> bool:
        """检查翻译服务是否可用"""
        return self.available


# 全局翻译服务实例
translation_service = TranslationService()


def translate_text(text: str, from_lang: str = 'en', to_lang: str = 'zh') -> str:
    """便捷的翻译函数"""
    return translation_service.translate_text(text, from_lang, to_lang)


def batch_translate(texts: list, from_lang: str = 'en', to_lang: str = 'zh') -> list:
    """便捷的批量翻译函数"""
    return translation_service.batch_translate(texts, from_lang, to_lang)
