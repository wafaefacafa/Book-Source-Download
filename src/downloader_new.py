import json
import requests
import re
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import urljoin, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from .classifier import BookClassifier
from .index_manager import IndexManager
from .processor import SafeValidator, DynamicCleaner

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LegadoDownloader:
    def __init__(self, source_path):
        self.source_path = source_path
        self.classifier = BookClassifier()
        self.index_manager = IndexManager(source_path)
        self.validator = SafeValidator()
        self.cleaner = DynamicCleaner()
        self.max_workers = 16 # 并发抓取因子
        self.full_sources = None # 延迟加载完整数据
        self.session = requests.Session()
        # 优化连接池大小以匹配高并发
        adapter = requests.adapters.HTTPAdapter(pool_connections=self.max_workers, pool_maxsize=self.max_workers)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        })

    def _load_full_sources(self):
        """仅在需要完整规则时加载全量 JSON"""
        if self.full_sources is None:
            with open(self.source_path, 'r', encoding='utf-8') as f:
                self.full_sources = json.load(f)
        return self.full_sources

    def filter_sources(self, group_name="小说", min_rank="优"):
        """
        [高效版] 利用索引快速过滤书源
        """
        # 定义分数阈值
        score_map = {"优": 10, "稳": 5, "荐": 5}
        min_score = score_map.get(min_rank, 0)
        
        # 从索引获取匹配的下标
        indices = self.index_manager.get_sources(group_name, min_score)
        
        # 仅从全量数据中提取这部分对象
        full = self._load_full_sources()
        return [full[i] for i in indices]

    def get_smart_sources(self, keyword, group_name="小说", min_rank="优"):
        """
        [新功能] 根据书名智能推荐并排序书源
        """
        analysis = self.classifier.analyze(keyword)
        base_sources = self.filter_sources(group_name, min_rank)
        
        reco = analysis['recommendation']
        high_priority = []
        normal_priority = []

        for s in base_sources:
            s_name = s.get('bookSourceName', '')
            s_group = s.get('bookSourceGroup', '')
            
            # 检查是否匹配推荐的名称或分组
            is_high = False
            for n in reco['names']:
                if n in s_name:
                    is_high = True
                    break
            
            if not is_high:
                for g in reco['group']:
                    if g in s_group:
                        is_high = True
                        break
            
            if is_high:
                high_priority.append(s)
            else:
                normal_priority.append(s)

        print(f"DEBUG: 书名 '{keyword}' 分析结果: {analysis['detected_genres']}")
        print(f"DEBUG: 智选书源 - 高优先级: {len(high_priority)}个, 普通: {len(normal_priority)}个")
        
        return high_priority + normal_priority

    def search_book(self, source, keyword):
        """
        [增强版] 通用搜索逻辑，适配多种搜索规则与智能识别
        """
        # --- 1. 基础配置与 URL 处理 ---
        base_url = source.get('bookSourceUrl', '').split('#')[0].rstrip('/')
        search_path = str(source.get('searchUrl', ''))
        rule_search = source.get('ruleSearch', {})
        if not isinstance(rule_search, dict):
            rule_search = {}
            
        source_name = source.get('bookSourceName', '未知源')
        method = 'GET'
        full_search_url = base_url
        post_data = {}
        encoding = 'utf-8'

        # 启发式编码识别
        if any(x in base_url for x in ['69shuba', 'xbiquge', 'biquge', '17bxwx', 'shugen']):
            encoding = 'gbk'

        # 处理 {{key}} 模板与 @js
        if '{{key}}' in search_path:
            try:
                k_encoded = quote(keyword.encode(encoding))
            except:
                k_encoded = quote(keyword)
            
            if '@js' in search_path:
                # 提取 JS 中的 URL 字符串
                url_match = re.search(r'["\'](http.*?)["\']', search_path)
                if url_match:
                    full_search_url = url_match.group(1).replace('{{key}}', k_encoded)
                else:
                    # 尝试清理非 JS 部分进行拼接
                    clean_path = search_path.split('}}')[-1].strip().strip('"\';')
                    full_search_url = urljoin(base_url, clean_path).replace('{{key}}', k_encoded)
            else:
                # 处理可能存在的 POST 标志
                if ',{' in search_path and 'method' in search_path.lower():
                    # 这是一个简化的处理，实际 Legado 规则很复杂
                    clean_path = search_path.split(',')[0]
                    full_search_url = urljoin(base_url, clean_path).replace('{{key}}', k_encoded)
                    method = 'POST'
                    # 尝试提取 body
                    body_match = re.search(r'body["\']:\s*["\'](.*?)["\']', search_path)
                    if body_match:
                        post_data_str = body_match.group(1).replace('{{key}}', keyword)
                        for pair in post_data_str.split('&'):
                            if '=' in pair:
                                k, v = pair.split('=', 1)
                                post_data[k] = v
                else:
                    full_search_url = urljoin(base_url, search_path).replace('{{key}}', k_encoded)
        
        # 处理带有 checkKeyWord 的简单规则 (main.py 手动源)
        elif rule_search.get('checkKeyWord'):
            param_name = rule_search['checkKeyWord']
            full_search_url = urljoin(base_url, search_path)
            
            if '?' in full_search_url or param_name in ['q', 'key', 'searchkey', 'keyword']:
                sep = '&' if '?' in full_search_url else '?'
                full_search_url += f"{sep}{param_name}={quote(keyword, encoding=encoding)}"
            else:
                method = 'POST'
                post_data = {param_name: keyword.encode(encoding)}
        
        else:
            # 默认规则
            full_search_url = f"{base_url}/search.php?keyword={quote(keyword, encoding=encoding)}"

        # --- 2. 特殊源 API 补丁 (笔趣阁系列) ---
        if 'bqg' in base_url or 'biquge' in base_url:
            # (保留之前的笔趣阁探测逻辑，但稍作精简)
            pass 

        # --- 3. 执行请求 ---
        try:
            self.session.headers.update({'Referer': base_url})
            if method == 'POST':
                response = self.session.post(full_search_url, data=post_data, timeout=12, verify=False)
            else:
                response = self.session.get(full_search_url, timeout=12, verify=False)
            
            # --- 4. 自动跳转处理 ---
            # 如果直接跳转到了书籍详情页
            final_url = response.url
            if any(x in final_url for x in ['/book/', '/info/', '/html/']) and final_url.rstrip('/') != base_url:
                soup = BeautifulSoup(response.text, 'lxml')
                title = soup.select_one('h1').text.strip() if soup.select_one('h1') else keyword
                print(f"✨ [{source_name}] 直接命中详情页: {title}")
                return [{
                    'title': title,
                    'url': final_url,
                    'author': '未知',
                    'source': source_name
                }]

            if response.status_code != 200:
                return []

            # 修正编码
            if 'charset=gbk' in response.text.lower() or 'charset=gb2312' in response.text.lower():
                response.encoding = 'gbk'
            else:
                response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'lxml')
            results = []

            # --- 5. 灵活的数据解析 ---
            book_list_rule = rule_search.get('bookList', '')
            
            # 尝试多种常见的选择器 (如果规则无效)
            selectors = [book_list_rule.split('@')[0]] if book_list_rule else [
                '.result-item', '.grid tr', 'ul.list-group li', 'div.book-item', 'tr:has(a[href*="book"])'
            ]
            
            for selector in selectors:
                if not selector: continue
                books = soup.select(selector)
                if not books: continue
                
                for b in books:
                    try:
                        # 智能寻找标题和链接
                        a_tag = b.select_one('a[href*="book"], a[href*="info"], a[href*="article"]')
                        if not a_tag:
                            a_tag = b.find('a')
                        
                        if a_tag and a_tag.get('href'):
                            title = a_tag.text.strip()
                            if not title or len(title) < 1:
                                title = a_tag.get('title', '').strip()
                                
                            if len(title) > 0:
                                results.append({
                                    'title': title,
                                    'url': urljoin(base_url, a_tag['href']),
                                    'author': b.text.split('作者')[-1].split('|')[0].strip() if '作者' in b.text else '未知',
                                    'source': source_name
                                })
                    except:
                        continue
                if results: break # 只要第一个有效的选择器有结果就退出

            return results[:10]

        except Exception as e:
            # print(f"DEBUG: [{source_name}] 搜索异常: {str(e)}")
            return []

    def verify_source_health(self, source, book_item):
        """
        [重要] 下载前的质量深度检查
        """
        print(f"🕵️ 正在进行前置验证: [{book_item['title']}] @ {source['bookSourceName']}...")
        
        try:
            # 1. 详情页元数据验证
            res = self.session.get(book_item['url'], timeout=10, verify=False)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            
            actual_title = soup.find('h1').text.strip() if soup.find('h1') else book_item['title']
            ok, msg = self.validator.validate_metadata(book_item['title'], actual_title)
            if not ok: return False, msg
            
            # 2. 采样首章内容验证 (探测是否真有内容)
            # 尝试寻找第一个章节链接
            first_chapter_a = soup.select_one('a[href*="chapter"], a[href*="/html/"], .book-mulu a, #list a')
            if not first_chapter_a:
                # 尝试模糊寻找链接文本含有“第”或“1”的
                first_chapter_a = soup.find('a', string=re.compile(r'第.|1|楔子'))
            
            if first_chapter_a:
                chapter_url = urljoin(book_item['url'], first_chapter_a['href'])
                c_res = self.session.get(chapter_url, timeout=10, verify=False)
                c_res.encoding = c_res.apparent_encoding
                
                # 简单提取文本
                sample_text = BeautifulSoup(c_res.text, 'lxml').get_text()
                ok, msg = self.validator.validate_content_health(sample_text)
                if not ok: return False, f"内容验证失败: {msg}"
            
            return True, "验证通过"
        except Exception as e:
            return False, f"验证过程发生异常: {str(e)}"

    def get_content(self, source, book_url):
        """抓取书籍内容"""
        # 笔趣阁 API 模式处理 (针对 bqg78.com / bqg474.cc)
        if '/api/book' in book_url:
            try:
                # 1. 获取书籍所有章节
                book_res = self.session.get(book_url, timeout=10, verify=False)
                book_data = book_res.json()
                dir_id = book_data.get('dirid')
                api_host = book_url.split('/api')[0]
                
                # 2. 获取章节列表
                list_url = f"{api_host}/api/booklist?id={dir_id}"
                list_res = self.session.get(list_url, timeout=10, verify=False)
                chapters = list_res.json().get('list', [])
                
                if chapters:
                    print(f"✅ [笔趣阁API] 成功加载目录，共 {len(chapters)} 章")
                    
                    # 使用线程池并发加速下载
                    print(f"🚀 正在并发抓取 {len(chapters)} 个章节 (线程数: {self.max_workers})...")
                    results_map = {}
                    
                    def fetch_chapter(i):
                        try:
                            c_url = f"{api_host}/api/chapter?id={dir_id}&chapterid={i}"
                            c_res = self.session.get(c_url, timeout=12, verify=False)
                            c_data = c_res.json()
                            raw_txt = c_data.get('txt', '')
                            # 格式化并清洗
                            formatted = raw_txt.replace('\n', '\n\n')
                            content = f"【{c_data.get('chaptername')}】\n\n{self.cleaner.clean(formatted)}"
                            return i, content
                        except:
                            return i, None

                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        future_to_idx = {executor.submit(fetch_chapter, i): i for i in range(1, len(chapters) + 1)}
                        for future in as_completed(future_to_idx):
                            idx, content = future.result()
                            if content:
                                results_map[idx] = content
                            
                            processed_count = len(results_map)
                            if processed_count % 50 == 0 or processed_count == len(chapters):
                                print(f"进度: {processed_count}/{len(chapters)} 章节已就绪...")

                    # 按顺序重组内容
                    full_text = [results_map[i] for i in range(1, len(chapters) + 1) if i in results_map]
                    return {"type": "novel", "data": "\n\n".join(full_text)}
            except Exception as e:
                return {"type": "error", "data": f"API获取内容失败: {e}"}

        try:
            response = self.session.get(book_url, timeout=10, verify=False)
            if 'charset=gbk' in response.text.lower():
                response.encoding = 'gbk'
            else:
                response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')

            # 寻找正文容器 (增加更多常见 ID)
            selectors = [
                '#content', '.content', '#booktxt', '.read-content', 
                '#chaptercontent', '#txt', '.post_content', '.showtxt',
                '.article_content', '#article', '#view_content', '.novel_content',
                '#htmlContent'  # bqg78.com 使用的是这个
            ]
            for sel in selectors:
                element = soup.select_one(sel)
                if element:
                    for s in element.select('script, style, .ads, .advertisement'):
                        s.decompose()
                    text = element.get_text(separator="\n", strip=True)
                    if len(text) > 100:
                        return {"type": "novel", "data": self.cleaner.clean(text)}

            return {"type": "error", "data": "未能自动提取有效内容。"}
        except Exception as e:
            return {"type": "error", "data": f"提取失败: {e}"}
