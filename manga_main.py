import sys
import os
# 添加项目根目录到 sys.path 以便导入 src 模块
project_root = r"C:/Users/www20/source/repos/legado-downloader"
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.manga_downloader import LegadoMangaDownloader
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)

def main():
    dl = LegadoMangaDownloader()
    print("=== 老版漫画下载器 ===")
    keyword = input("请输入要搜索的漫画名: ")
    if not keyword:
        return
    
    results = dl.search_manga(keyword)
    if not results:
        print("未找到结果")
        return
        
    print("\n发现以下漫画:")
    for i, r in enumerate(results):
        print(f"[{i}] {r['title']} - {r['source']}")
        
    choice = input("\n请输入序号下载 (回车取消): ")
    if not choice.isdigit():
        return
    idx = int(choice)
    if idx < 0 or idx >= len(results):
        return
    
    target = results[idx]
    mid, chapters = dl.get_toc(target["url"])
    if not chapters:
        print("未能获取章节列表")
        return
        
    print(f"\n找到 {len(chapters)} 个章节")
    
    range_input = input("\n请输入下载范围 (例如: 1-5, 或 0 下载全部, 直接回车下载第一章): ")
    
    save_base = os.path.join("D:/book/manga", target["title"])
    if not os.path.exists(save_base):
        os.makedirs(save_base)

    if not range_input:
        # 下载第一章
        dl.download_chapter(mid, chapters[0], save_base, index=1)
    elif range_input == "0":
        # 下载全部
        for i, chapter in enumerate(chapters):
            dl.download_chapter(mid, chapter, save_base, index=i+1)
    else:
        # 处理范围 1-5
        try:
            start, end = map(int, range_input.split("-"))
            for i in range(start-1, min(end, len(chapters))):
                dl.download_chapter(mid, chapters[i], save_base, index=i+1)
        except:
            print("范围格式错误，例如 1-5")

    print(f"\n操作完成！保存位置: {save_base}")

if __name__ == "__main__":
    main()
