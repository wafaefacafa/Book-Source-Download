import json
import requests
import re
import os
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import urljoin, quote
from concurrent.futures import ThreadPoolExecutor, as_completed

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LegadoMangaDownloader:
    def __init__(self, source_path=None):
        self.max_workers = 16
        self.session = requests.Session()
        # 优化漫画连接池，因为图片请求非常频繁
        adapter = requests.adapters.HTTPAdapter(pool_connections=self.max_workers, pool_maxsize=self.max_workers)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        })
        # 预设一个包子漫画源，因为它的 API 比较特殊
        self.baozimh_source = {
            "bookSourceName": "包子漫画",
            "bookSourceUrl": "https://manhuafree.com",
            "searchUrl": "/s/{{key}}",
            "ruleSearch": {
                "bookList": ".grid-cols-3 .pb-2",
                "name": "h3",
                "bookUrl": "a"
            }
        }

    def fix_encoding(self, text):
        """修复 requests 抓取结果中的中文乱码"""
        try:
            return text.encode('latin1').decode('utf-8')
        except:
            return text

    def search_manga(self, keyword):
        """搜索漫画"""
        url = f"https://manhuafree.com/s/{quote(keyword)}"
        print(f"正在搜索: {url} ...")
        r = self.session.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        books = soup.select('.grid-cols-3 .pb-2')
        
        results = []
        for b in books:
            title = self.fix_encoding(b.select_one('h3').get_text().strip())
            href = b.select_one('a')['href']
            results.append({
                "title": title,
                "url": urljoin("https://manhuafree.com", href),
                "source": "包子漫画"
            })
        return results

    def get_toc(self, comic_url):
        """获取目录"""
        r = self.session.get(comic_url, timeout=10)
        # 调试输出
        # print(f"详情页内容长度: {len(r.text)}")
        mid_match = re.search(r'data-mid="(\d+)"', r.text)
        if not mid_match:
            print("未在页面中找到 data-mid")
            return None, []
        
        mid = mid_match.group(1)
        print(f"找到 mid: {mid}")
        toc_api = f"https://api-get-v2.mgsearcher.com/api/manga/get?mid={mid}&mode=all"
        r_toc = self.session.get(toc_api, headers={'Referer': 'https://manhuafree.com'}, timeout=10)
        data = r_toc.json()
        
        chapters = []
        # 注意: 这里的结构是 data['data']['chapters'] 而不是 ['data']['info']['chapters']
        raw_chapters = data.get('data', {}).get('chapters', [])
        if not raw_chapters:
            # 兼容另一种可能的结构
            raw_chapters = data.get('data', {}).get('info', {}).get('chapters', [])

        for c in raw_chapters:
            title = c.get('attributes', {}).get('title')
            cid = c.get('id')
            if title and cid:
                chapters.append({
                    "title": title,
                    "id": cid
                })
        return mid, chapters

    def download_chapter(self, mid, chapter, save_dir, index=None):
        """下载单个章节的所有图片，增加重试机制和更完善的状态检查"""
        chapter_title = chapter['title']
        chapter_id = chapter['id']
        
        # 创建章节目录，加上序号排序
        prefix = f"{index:04d}_" if index is not None else ""
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', chapter_title)
        chapter_dir_name = f"{prefix}{safe_title}"
        chapter_path = os.path.join(save_dir, chapter_dir_name)
        
        content_api = f"https://api-get-v2.mgsearcher.com/api/chapter/getinfo?m={mid}&c={chapter_id}"
        
        # 尝试获取章节图片列表（增加重试）
        images = []
        for retry in range(3):
            try:
                r = self.session.get(content_api, headers={'Referer': 'https://manhuafree.com'}, timeout=20)
                data = r.json()
                images = data.get('data', {}).get('info', {}).get('images', {}).get('images', [])
                if images:
                    break
            except Exception as e:
                if retry == 2:
                    print(f"❌ 获取章节 [{chapter_title}] 列表失败: {e}")
                    return False
                print(f"⚠️ 获取章节列表失败，正在进行第 {retry+1} 次重试...")

        # 检查是否已经下载完成
        if os.path.exists(chapter_path):
            existing_files = [f for f in os.listdir(chapter_path) if f.endswith('.webp')]
            if len(existing_files) >= len(images) and len(images) > 0:
                print(f"⏩ 章节 [{chapter_title}] 已存在且完整，跳过")
                return True
            else:
                print(f"补全章节 [{chapter_title}]: 当前 {len(existing_files)}/{len(images)}")
            
        os.makedirs(chapter_path, exist_ok=True)
            
        print(f"正在下载章节 [{chapter_title}] ({len(images)} 张图片)...")
        
        def download_img(idx, img):
            img_url = f"https://f40-1-4.g-mh.online{img['url']}"
            img_name = f"{idx+1:03d}.webp"
            file_path = os.path.join(chapter_path, img_name)
            
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return True
            
            for img_retry in range(3):
                try:
                    img_data = self.session.get(img_url, headers={'Referer': 'https://manhuafree.com'}, timeout=30).content
                    with open(file_path, 'wb') as f:
                        f.write(img_data)
                    return True
                except:
                    pass
            return False

        # 使用线程池并发抓取图片
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_img = {executor.submit(download_img, idx, img): idx for idx, img in enumerate(images)}
            success_count = 0
            for future in as_completed(future_to_img):
                if future.result():
                    success_count += 1

        if success_count >= len(images):
            print(f"✅ 章节 [{chapter_title}] 下载完成")
            return True
        else:
            print(f"⚠️ 章节 [{chapter_title}] 未完全下载 ({success_count}/{len(images)})")
            return False

def main():
    downloader = LegadoMangaDownloader()
    keyword = "斗罗大陆3龙王传说"
    
    print(f"=== 漫画下载测试 (基于包子漫画) ===")
    results = downloader.search_manga(keyword)
    
    if not results:
        print("未找到漫画")
        return
        
    print("\n搜索结果:")
    for idx, r in enumerate(results[:10]):
        print(f"[{idx}] {r['title']}")
        
    choice = input("\n请选择下载序号 (默认 0): ") or "0"
    selected = results[int(choice)]
    
    mid, chapters = downloader.get_toc(selected['url'])
    if not mid or not chapters:
        print("获取目录失败")
        return
        
    print(f"\n成功获取目录，共 {len(chapters)} 章。")
    
    # 创建书名目录
    base_save_dir = os.path.join("D:\\book\\manga", re.sub(r'[\\/:*?"<>|]', '_', selected['title']))
    if not os.path.exists(base_save_dir):
        os.makedirs(base_save_dir)
        
    # 开始正式全本下载
    print(f"\n开始下载全本内容，共 {len(chapters)} 章 (并发模式)...")
    
    # 使用线程池并发下载章节
    max_workers = 5  # 建议不要设置太高，防止被封 IP
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chapter = {
            executor.submit(downloader.download_chapter, mid, c, base_save_dir, index=idx): c 
            for idx, c in enumerate(chapters)
        }
        
        for future in as_completed(future_to_chapter):
            chapter = future_to_chapter[future]
            try:
                future.result()
            except Exception as exc:
                print(f"❌ 章节 [{chapter['title']}] 产生未处理异常: {exc}")
        
    print(f"\n下载完成！所有文件已保存至: {base_save_dir}")

if __name__ == "__main__":
    main()
