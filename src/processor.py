import hashlib
import re
from difflib import SequenceMatcher

class SafeValidator:
    """
    三重前置验证体系 (Pre-Download Validation)
    确保下载的内容是真实、完整且符合预期的。
    """
    def __init__(self):
        self.fake_markers = ["请稍后", "正在重定向", "访问受限", "滑动验证", "503 Service", "机器人验证"]
        
    def validate_metadata(self, expected_title, actual_title, actual_author=None):
        """校验书名一致性"""
        score = SequenceMatcher(None, expected_title, actual_title).ratio()
        if score < 0.5:
            return False, f"标题不匹配 (相似度: {score:.2f}, 预期: {expected_title}, 实际: {actual_title})"
        return True, "元数据验证通过"

    def validate_content_health(self, content):
        """校验内容健康度（是否包含正文特征）"""
        if not content or len(content) < 200:
            return False, "内容过短，疑似无效页面"
        
        # 统计正文特征
        period_count = content.count('。') + content.count('！') + content.count('？')
        if period_count < 5:
            return False, f"文本熵过低（标点密度不足），疑似广告或乱码"

        if any(marker in content for marker in self.fake_markers):
            return False, "检测到反爬/重定向标记"
            
        return True, "内容负载验证通过"

class DynamicCleaner:
    """
    章节指纹去重 V2 (Chapter Fingerprint Deduplication)
    流式特征提取，自动拦截重复行和系统广告。
    """
    def __init__(self):
        self.seen_fingerprints = set()
        # 预置一些绝对垃圾行模式
        self.global_blocked_patterns = [
            r"https?://[\w\./]+", # URL
            r"www\.\w+\.(com|net|cn|org)", # 域名
            r".*最新章节.*",
            r".*手机用户.*",
            r".*点击下载.*",
            r".*本站域名.*",
            r"\(第\d+/\d+页\)", # 分页符
            r".*加入书架.*"
        ]

    def clean(self, raw_text, skip_dedup=False):
        """
        净化章节内容
        :param skip_dedup: 是否跳过重复行检测（如果不希望误伤某些重复对话）
        """
        if not raw_text:
            return ""

        lines = raw_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            # 1. 模式拦截 (Regex)
            is_blocked = False
            for pattern in self.global_blocked_patterns:
                if re.match(pattern, trimmed):
                    is_blocked = True
                    break
            if is_blocked: continue

            # 2. 指纹去重 (MD5 Fingerprint)
            # 缩减指纹只保留文字核心，忽略标点
            core_content = re.sub(r'[^\u4e00-\u9fa5\w]', '', trimmed)
            if not core_content: continue
            
            fingerprint = hashlib.md5(core_content.encode('utf-8')).hexdigest()

            if not skip_dedup:
                # 只有长度超过一定阈值的行才参与去重，防止误伤短对话
                if len(trimmed) > 12:
                    if fingerprint in self.seen_fingerprints:
                        continue
                    self.seen_fingerprints.add(fingerprint)
            
            cleaned_lines.append(trimmed)

        return "\n\n".join(cleaned_lines)

    def reset_history(self):
        """重置已见指纹（用于处理不同书籍）"""
        self.seen_fingerprints.clear()
