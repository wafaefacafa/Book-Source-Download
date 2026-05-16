import json
import requests
from bs4 import BeautifulSoup
import re

class LegadoDownloader:
    def __init__(self, source_path):
        self.sources = self._load_sources(source_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        })

    def _load_sources(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def filter_sources(self, group_name="小说", min_rank="优"):
        """过滤特定分类和等级的源"""
        filtered = []
        for s in self.sources:
            group = s.get('bookSourceGroup', '')
            name = s.get('bookSourceName', '')
            if group_name in group and min_rank in name:
                filtered.append(s)
        return filtered

    def search_book(self, source, keyword):
        """解析书源规则并执行搜索"""
        search_rule = source.get('ruleSearch', {})
        search_url_template = source.get('bookSourceUrl', '') + source.get('ruleSearch', {}).get('checkKeyWord', '')
        
        # 很多 Legado 书源使用 {{key}} 作为关键词占位符
        if '{{key}}' in search_url_template:
            search_url = search_url_template.replace('{{key}}', keyword)
        else:
            # 备选方案：尝试从 sourceUrl 拼接
            search_url = source.get('bookSourceUrl', '') + f"/search?key={keyword}"

        print(f"正在尝试从 [{source['bookSourceName']}] 获取数据: {search_url}")
        
        try:
            # 特殊处理笔下文学的 POST 搜索
            if "17bxwx.com" in source.get('bookSourceUrl', ''):
                search_url = source.get('bookSourceUrl', '').rstrip('/') + "/search.html"
                data = {"searchkey": keyword}
                response = self.session.post(search_url, data=data, timeout=10, verify=False)
            else:
                # 增加 verify=False 忽略 SSL 证书错误，增加更真实的 Headers
                response = self.session.get(search_url, timeout=10, verify=False)
            
            if response.status_code == 200:
                # 针对不同编码进行处理
                response.encoding = response.apparent_encoding
                soup = BeautifulSoup(response.text, 'lxml')
                results = []
                
                # 增强搜索逻辑：不仅找 a 标签文本，还搜索包含关键字的容器
                # 寻找所有包含关键字的 a 链接
                for link in soup.find_all('a'):
                    text = link.get_text().strip()
                    href = link.get('href')
                    if keyword in text and href:
                        results.append({
                            'title': text,
                            'url': href,
                            'source': source['bookSourceName']
                        })
                
                # 如果没找到，尝试在整个页面寻找带关键字的标题
                if not results:
                    for tag in soup.find_all(['h1', 'h2', 'h3', 'span']):
                        if keyword in tag.get_text():
                            parent_a = tag.find_parent('a')
                            if parent_a and parent_a.get('href'):
                                results.append({
                                    'title': tag.get_text().strip(),
                                    'url': parent_a.get('href'),
                                    'source': source['bookSourceName']
                                })
                return results
        except Exception as e:
            print(f"源 [{source['bookSourceName']}] 请求失败: {e}")
        return []

    def get_content(self, source, book_url):
        """抓取书籍详情页或第一章内容作为预览"""
        try:
            # 补齐完整 URL
            if book_url.startswith('/'):
                from urllib.parse import urljoin
                base_url = source.get('bookSourceUrl', '')
                book_url = urljoin(base_url, book_url)

            response = self.session.get(book_url, timeout=10, verify=False)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')

            # 改进的提取逻辑：
            # 1. 寻找常见的正文 ID 或 Class
            content_selectors = [
                 '#content', '.content', '#booktxt', '.read-content', '#chaptercontent', '#txt', '.post_content'
            ]
            for sel in content_selectors:
                element = soup.select_one(sel)
                if element:
                    text = element.get_text(separator="\n", strip=True)
                    if len(text) > 50:
                        return {"type": "novel", "data": text[:300] + "..."}

            # 2. 如果是漫画 (寻找 img)
            imgs = soup.find_all('img')
            img_links = []
            for img in imgs:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                # 过滤一些明显的图标或广告
                if src and any(ext in src.lower() for ext in ['.jpg', '.png', '.webp', '.jpeg']):
                    if len(src) < 10: continue 
                    if not src.startswith('http'):
                        from urllib.parse import urljoin
                        src = urljoin(book_url, src)
                    img_links.append(src)
                if len(img_links) >= 5:
                    break
            
            if img_links:
                return {"type": "manga", "data": img_links}

            # 3. 兜底搜索所有 p 标签
            paragraphs = soup.find_all('p')
            text = "\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
            if text:
                return {"type": "novel", "data": text[:300] + "..."}

            return {"type": "novel", "data": "未能提取到具体内容，可能需要进入目录页或详情页进一步解析。"}
        except Exception as e:
            return {"type": "error", "data": f"内容获取失败: {str(e)}"}

if __name__ == "__main__":
    # 示例用法
    path = r"c:\Users\www20\Downloads\墨辰整理书源大全7.0（禁止倒卖）【完整】.json"
    downloader = LegadoDownloader(path)
    novel_sources = downloader.filter_sources("小说", "优+++")
    print(f"找到 {len(novel_sources)} 个优+++小说源")
    for s in novel_sources:
        print(f"- {s['bookSourceName']}")
