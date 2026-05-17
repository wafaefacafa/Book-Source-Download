import json
import requests
import re
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import urljoin, quote

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        """通用搜索逻辑，适配多种搜索规则"""
        base_url = source.get('bookSourceUrl', '').split('#')[0].rstrip('/')
        search_path = str(source.get('searchUrl', ''))
        rule_search = source.get('ruleSearch', {})
        
        # 针对手动添加的简单规则
        param_name = rule_search.get('checkKeyWord') if isinstance(rule_search, dict) else None

        method = 'GET'
        full_search_url = base_url
        post_data = {}
        encoding = 'utf-8'

        # 启发式选择编码 (中文书籍网站多用 GBK 或 UTF-8)
        if any(x in base_url for x in ['69shuba', 'xbiquge', 'biquge', '17bxwx']):
            encoding = 'gbk'

        # 1. 处理 Legado 的 {{key}} 模板
        if '{{key}}' in search_path:
            try:
                k_encoded = quote(keyword.encode(encoding))
            except:
                k_encoded = quote(keyword)
            
            if '@js' in search_path:
                # 尝试提取末尾的 URL 字符串
                url_match = re.search(r'["\'](http.*?)["\']', search_path)
                if url_match:
                    full_search_url = url_match.group(1).replace('{{key}}', k_encoded)
                else:
                    # 尝试清理非 JS 部分
                    clean_path = search_path.split('}}')[-1].strip().strip('"\';')
                    if clean_path.startswith('http'):
                        full_search_url = clean_path.replace('{{key}}', k_encoded)
                    elif clean_path.startswith('/'):
                        full_search_url = base_url + clean_path.replace('{{key}}', k_encoded)
            else:
                full_search_url = base_url + search_path.replace('{{key}}', k_encoded)
        
        # 2. 处理带有 checkKeyWord 的规则 (main.py 手动定义的源)
        elif param_name:
            if search_path.startswith('/'):
                full_search_url = base_url + search_path
            else:
                full_search_url = base_url + '/' + search_path
            
            if '?' in full_search_url or param_name in ['q', 'key', 'searchkey', 'keyword']:
                method = 'GET'
                # 检查是否已经有问号
                sep = '&' if '?' in full_search_url else '?'
                # 对于 main.py 中的 69shuba.pro 等，强制使用 GBK
                k_encoded = quote(keyword, encoding=encoding)
                full_search_url += f"{sep}{param_name}={k_encoded}"
            else:
                method = 'POST'
                try:
                    # POST 数据也需要对应编码
                    post_data = {param_name: keyword.encode(encoding)}
                except:
                    post_data = {param_name: keyword}
        
        # 3. 兜底搜索 (根据常见规律)
        else:
            full_search_url = base_url + f"/search.php?keyword={quote(keyword, encoding=encoding)}"

        # 笔趣阁专用 API 逻辑 (针对 bqg78.com / bqg474.cc 的 SPA 版本)
        if 'bqg78.com' in base_url or 'bqg474.cc' in base_url or 'bqg' in base_url:
            print(f"正在尝试从 [{source['bookSourceName']}] 获取数据: 正在使用笔趣阁全局 API 探测...")
            try:
                # 优先尝试通用的 bqg474 API (目前最稳定)
                api_host = "https://www.bqg474.cc"
                search_api = f"{api_host}/api/search?q={quote(keyword)}"
                res = self.session.get(search_api, timeout=10, verify=False)
                if res.status_code == 200:
                    data = res.json()
                    book_list = data.get('data', []) if isinstance(data, dict) else []
                    results = []
                    for item in book_list:
                        results.append({
                            'title': item.get('title'),
                            # 存储为详情页接口 URL
                            'url': f"{api_host}/api/book?id={item.get('id')}", 
                            'author': item.get('author'),
                            'source': source['bookSourceName']
                        })
                    if results:
                        print(f"✅ [笔趣阁API] 成功通过全局网关获取 {len(results)} 条数据")
                        return results[:10]
            except:
                pass

        # 针对 69shuba.pro 这种特殊的跳转，添加 Referer 和更多 Headers
        self.session.headers.update({
            'Referer': base_url + '/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': 'allow_all=true; visited=true' # 尝试绕过一些简单的 JS 验证
        })
        
        # 强制其他普通笔趣阁（如果有）使用旧逻辑
        if 'bqg' in base_url and 'bqg78' not in base_url and 'bqg474' not in base_url:
            print(f"正在尝试从 [{source['bookSourceName']}] 获取数据: 尝试执行备选搜索...")
            try:
                # 1. 激活搜索 (HM 接口)
                hm_url = f"{base_url}/user/hm.html?q={quote(keyword)}"
                self.session.get(hm_url, timeout=5, verify=False)
                # 2. 获取 JSON 结果
                search_api = f"{base_url}/user/search.html?q={quote(keyword)}"
                res = self.session.get(search_api, timeout=10, verify=False)
                if res.status_code == 200:
                    data = []
                    try: data = res.json()
                    except: pass
                    
                    if isinstance(data, list) and len(data) > 0:
                        results = []
                        for item in data:
                            results.append({
                                'title': item.get('articlename'),
                                'url': urljoin(base_url, item.get('url_list')),
                                'author': item.get('author'),
                                'source': source['bookSourceName']
                            })
                        if results: return results[:5]
            except Exception:
                pass

        # 针对 69shuba.pro 的搜索路径修复：它是 /search.htm 而不是 /modules/article/search.php
        if '69shuba.pro' in base_url:
            full_search_url = base_url + f"/search.htm?searchkey={quote(keyword, encoding='gbk')}"
            method = 'GET'

        print(f"正在尝试从 [{source['bookSourceName']}] 获取数据: {full_search_url} ({method})")
        
        try:
            # 增加通用的浏览器 Headers 以减少 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Referer': base_url
            }

            if method == 'POST':
                response = self.session.post(full_search_url, data=post_data, headers=headers, timeout=10, verify=False, allow_redirects=True)
            else:
                response = self.session.get(full_search_url, headers=headers, timeout=10, verify=False, allow_redirects=True)
            
            # 如果依然失败且是 69shuba，尝试另一种 URL 格式
            if response.status_code != 200 and '69shuba' in base_url:
                 # 69shuba 有时使用 modules/... 路径，有时直接在根目录
                 alt_url = base_url + f"/modules/article/search.php?searchkey={quote(keyword, encoding='gbk')}"
                 response = self.session.get(alt_url, headers=headers, timeout=10, verify=False)

            if response.status_code == 200:
                # 针对 GBK 页面手动修复
                if 'charset=gbk' in response.text.lower() or 'charset=gb2312' in response.text.lower():
                    response.encoding = 'gbk'
                else:
                    response.encoding = response.apparent_encoding
                
                soup = BeautifulSoup(response.text, 'lxml')
                results = []
                
                # 方案 A: 根据 ruleSearch.bookList 尝试解析 (如果存在)
                book_list_rule = rule_search.get('bookList') if isinstance(rule_search, dict) else None
                if book_list_rule and not book_list_rule.startswith('@js'):
                    selector = book_list_rule.split('@')[0]
                    books = soup.select(selector)
                    for b in books:
                        a_tag = b.select_one('a')
                        if a_tag:
                            results.append({
                                'title': a_tag.get_text().strip(),
                                'url': urljoin(base_url + '/', a_tag.get('href')),
                                'source': source['bookSourceName']
                            })

                # 方案 B: 模糊查找 (适用于大多数情况)
                if not results:
                    for link in soup.find_all('a'):
                        text = link.get_text().strip()
                        href = link.get('href')
                        if keyword in text and href and len(text) < 50:
                            if any(x in href.lower() for x in ['search', 'javascript', 'register', 'login']):
                                continue
                            full_url = urljoin(base_url + '/', href)
                            results.append({
                                'title': text,
                                'url': full_url,
                                'source': source['bookSourceName']
                            })
                
                return results[:5] # 只保留前5个结果
        except Exception as e:
            pass
        return []

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
                    full_text = []
                    # 批量获取所有章节 (API 比较快，可以全量下载)
                    print(f"正在全量下载 {len(chapters)} 个章节...")
                    for i in range(1, len(chapters) + 1):
                        try:
                            c_url = f"{api_host}/api/chapter?id={dir_id}&chapterid={i}"
                            c_res = self.session.get(c_url, timeout=10, verify=False)
                            c_data = c_res.json()
                            raw_txt = c_data.get('txt', '')
                            # 简单的格式化
                            formatted = raw_txt.replace('\n', '\n\n')
                            full_text.append(f"【{c_data.get('chaptername')}】\n\n{formatted}")
                            if i % 50 == 0:
                                print(f"已下载 {i}/{len(chapters)} 章节...")
                        except:
                            print(f"警告: 章节 {i} 下载失败，跳过")
                    
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
                        return {"type": "novel", "data": text}

            return {"type": "error", "data": "未能自动提取有效内容。"}
        except Exception as e:
            return {"type": "error", "data": f"提取失败: {e}"}
