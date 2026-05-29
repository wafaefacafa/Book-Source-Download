import json
import os
import hashlib
import time

class IndexManager:
    """
    全量书源高速索引 (High-Speed Index Manager)
    针对数千个 Legado 书源进行元数据提取与本地缓存分析，加速过滤与检索。
    """
    def __init__(self, source_path, cache_dir=".cache"):
        self.source_path = source_path
        self.cache_dir = cache_dir
        self.index_file = os.path.join(cache_dir, "sources_index.json")
        self.metadata_file = os.path.join(cache_dir, "index_metadata.json")
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        self.index_data = []
        self._ensure_index()

    def _get_file_hash(self):
        """计算源文件哈希，用于检测变化"""
        hasher = hashlib.md5()
        with open(self.source_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def _ensure_index(self):
        """确保索引存在且为最新"""
        current_hash = self._get_file_hash()
        
        # 检查元数据判断是否需要重建
        need_rebuild = True
        if os.path.exists(self.metadata_file) and os.path.exists(self.index_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                if meta.get('source_hash') == current_hash:
                    need_rebuild = False
        
        if need_rebuild:
            self.rebuild_index(current_hash)
        else:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index_data = json.load(f)

    def rebuild_index(self, source_hash):
        """重建索引：提取核心字段，减少内存占用"""
        print(f"🔍 正在为全量书源建立高速索引... (Hash: {source_hash[:8]})")
        start_time = time.time()
        
        with open(self.source_path, 'r', encoding='utf-8') as f:
            raw_sources = json.load(f)
            
        indexed = []
        for i, s in enumerate(raw_sources):
            # 仅提取核心过滤字段
            name = s.get('bookSourceName', '')
            group = s.get('bookSourceGroup', '')
            url = s.get('bookSourceUrl', '')
            
            # 预判质量等级 (常见标识：优, 稳, 荐)
            rank_score = 0
            if '优' in name: rank_score += 10
            if '稳' in name: rank_score += 5
            if '荐' in name: rank_score += 5
            if '失效' in name or '无法' in name: rank_score -= 50
            
            indexed.append({
                'id': i,
                'name': name,
                'group': group,
                'url': url,
                'rank_score': rank_score,
                # 存储原始对象的精简引用（如果需要完整解析，再回原文件查或存部分核心）
                'has_search': bool(s.get('searchUrl')),
                'raw_index': i # 记录在原始 JSON 中的位置
            })
            
        # 存储索引
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(indexed, f, ensure_ascii=False)
            
        # 存储元数据
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source_hash': source_hash,
                'count': len(indexed),
                'timestamp': time.time()
            }, f)
            
        self.index_data = indexed
        print(f"✅ 索引重建完成！共处理 {len(indexed)} 个源，耗时 {time.time()-start_time:.2f}s")

    def get_sources(self, group_name="小说", min_rank_score=0):
        """根据索引快速获取匹配的源 ID 列表"""
        matched_indices = []
        for s in self.index_data:
            if group_name in s['group'] and s['rank_score'] >= min_rank_score and s['has_search']:
                matched_indices.append(s['raw_index'])
        return matched_indices

if __name__ == "__main__":
    # 测试
    source = r"c:\Users\www20\Downloads\墨辰整理书源大全7.0（禁止倒卖）【完整】.json"
    manager = IndexManager(source)
    results = manager.get_sources("小说", 10)
    print(f"匹配到高质量源: {len(results)} 个")
