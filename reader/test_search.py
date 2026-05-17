import os
import sys

# 将 src 目录添加到路径
sys.path.append(os.path.join(os.getcwd(), "src"))

from downloader_new import LegadoDownloader

def main():
    source_file = r'c:\Users\www20\Downloads\墨辰整理书源大全7.0（禁止倒卖）【完整】.json'
    
    print("=== Legado 书源下载器 (增强版) ===")
    
    if not os.path.exists(source_file):
        print(f"错误: 找不到文件 {source_file}")
        return

    downloader = LegadoDownloader(source_file)
    
    # 模拟用户输入
    group = "小说"
    rank = "优"
    
    all_sources = downloader.filter_sources(group, rank)
    
    # 手动添加一些经过分析后已知格式的候选源
    manual_sources = [
        {
            "bookSourceName": "太极小说 (直连)",
            "bookSourceUrl": "https://69shux.co",
            "searchUrl": "/search",
            "ruleSearch": {"checkKeyWord": "key"}
        },
        {
            "bookSourceName": "69书吧 (稳定)",
            "bookSourceUrl": "https://www.69shuba.pro",
            "searchUrl": "/modules/article/search.php",
            "ruleSearch": {"checkKeyWord": "searchkey"}
        },
        {
            "bookSourceName": "三叉小说",
            "bookSourceUrl": "http://m.xxxbiquge.info",
            "searchUrl": "/search.php",
            "ruleSearch": {"checkKeyWord": "keyword"}
        }
    ]
    
    sources = manual_sources + all_sources
    print(f"匹配到 {len(sources)} 个源。")
    
    keyword = "斗罗大陆"
    print(f"搜素关键词: {keyword}")

    found_books = []
    # 尝试前 15 个源
    for source in sources[:15]:
        results = downloader.search_book(source, keyword)
        if results:
            print(f"✅ 从 [{source['bookSourceName']}] 发现 {len(results)} 本书")
            found_books.extend(results)
            # 如果找到了精准匹配的书，可以提前停止
            if any(keyword in r['title'] for r in results):
                break

    if not found_books:
        print("❌ 未能在前 15 个源中找到结果。")
        return

    print("\n--- 搜索结果 ---")
    for i, book in enumerate(found_books[:10]):
        print(f"{i+1}. {book['title']} ({book['source']}) - {book['url']}")

    # 下一步可以实现选择书籍并下载
    print("\n[待办] 请选择编号进行解析内容...")

if __name__ == "__main__":
    main()
