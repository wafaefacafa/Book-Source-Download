import requests
import os
import json
from bs4 import BeautifulSoup

def test_manga_search():
    keyword = "斗罗大陆3龙王传说"
    # 包子漫画
    url = f"https://manhuafree.com/s/{keyword}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print(f"正在搜索漫画: {keyword} ...")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 根据书源规则: .grid-cols-3@.pb-2
        books = soup.select('.grid-cols-3 .pb-2')
        print(f"找到 {len(books)} 个结果")
        
        results = []
        for b in books:
            title = b.select_one('h3').get_text().strip()
            href = b.select_one('a')['href']
            # 包子漫画的 href 可能是相对路径 /comic/duoluodalu3longwangchuanshuo
            full_url = "https://manhuafree.com" + href if href.startswith('/') else href
            print(f"- {title}: {full_url}")
            results.append({"title": title, "url": full_url})
            
        return results
    except Exception as e:
        print(f"搜索出错: {e}")
        return []

def test_get_toc(comic_url):
    print(f"\n正在获取目录: {comic_url} ...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://manhuafree.com'
    }
    try:
        r = requests.get(comic_url, headers=headers, timeout=10)
        # 书源脚本中从 HTML 提取 mid: var mid=src.match(/data\-mid\=\"(\d+)\"/)[1];
        import re
        mid_match = re.search(r'data-mid="(\d+)"', r.text)
        if not mid_match:
            print("未找到 mid")
            return
        mid = mid_match.group(1)
        print(f"找到漫画 ID (mid): {mid}")
        
        # 目录 API: https://api-get-v2.mgsearcher.com/api/manga/get?mid=${mid}&mode=all
        toc_api = f"https://api-get-v2.mgsearcher.com/api/manga/get?mid={mid}&mode=all"
        print(f"正在调用目录 API: {toc_api}")
        
        r_toc = requests.get(toc_api, headers=headers, timeout=10)
        data = r_toc.json()
        
        chapters = data.get('data', {}).get('info', {}).get('chapters', [])
        print(f"总计 {len(chapters)} 章节")
        
        for c in chapters[:5]: # 只打前 5 个展示
            c_title = c.get('title')
            c_id = c.get('id')
            print(f"- {c_title} (ID: {c_id})")
            
        return mid, chapters
    except Exception as e:
        print(f"获取目录出错: {e}")
        return None, []

def test_get_content(mid, chapter_id):
    # 章节信息 API: https://api-get-v2.mgsearcher.com/api/chapter/getinfo?m=${mid}&c=${id}
    print(f"\n正在获取章节内容: chapter_id={chapter_id} ...")
    url = f"https://api-get-v2.mgsearcher.com/api/chapter/getinfo?m={mid}&c={chapter_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://manhuafree.com'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        # 这里的 images 结构: data.data.info.images.images
        images = data.get('data', {}).get('info', {}).get('images', {}).get('images', [])
        print(f"找到 {len(images)} 张图片")
        
        for img in images[:3]:
            # 图片拼接规则: https://f40-1-4.g-mh.online${item.url}
            img_url = f"https://f40-1-4.g-mh.online{img.get('url')}"
            print(f"- 图片 URL: {img_url}")
            
    except Exception as e:
        print(f"获取内容出错: {e}")

if __name__ == "__main__":
    res = test_manga_search()
    if res:
        mid, chapters = test_get_toc(res[0]['url'])
        if mid and chapters:
            test_get_content(mid, chapters[0]['id'])
