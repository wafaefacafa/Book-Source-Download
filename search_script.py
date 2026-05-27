import sys
import os

# Set encoding to utf-8 for terminal output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(r'C:/Users/www20/source/repos/legado-downloader')
from src.downloader_new import LegadoDownloader
from src.manga_downloader import LegadoMangaDownloader

source_file = r"c:\Users\www20\Downloads\墨辰整理书源大全7.0（禁止倒卖）【完整】.json"

def search():
    print("--- 搜索漫画 ---")
    manga_dl = LegadoMangaDownloader()
    manga_results = manga_dl.search_manga('史莱克天团')
    for i, r in enumerate(manga_results):
        print(f"Manga [{i}]: {r['title']} - {r['url']}")
    
    print("\n--- 搜索小说 ---")
    novel_dl = LegadoDownloader(source_file)
    # Search in a few known good sources
    good_sources = [s for s in novel_dl.sources if s.get('bookSourceName') in ['笔趣阁', '爱下电子书', '80电子书', '顶点小说', '69书吧']]
    if not good_sources:
        # Fallback to sources that have simple searchUrl
        good_sources = [s for s in novel_dl.sources if '{{key}}' in str(s.get('searchUrl'))][:10]
    
    for s in good_sources:
        print(f"Searching novel in source: {s['bookSourceName']}")
        try:
            results = novel_dl.search_book(s, '史莱克天团')
            if results:
                for j, r in enumerate(results):
                    print(f"  Novel [{j}]: {r.get('name')} - {r.get('author')} - {r.get('bookUrl')}")
        except Exception:
            pass

if __name__ == "__main__":
    search()
