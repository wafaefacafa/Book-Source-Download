from src.downloader_new import LegadoDownloader
import os

def main():
    source_file = r"c:\Users\www20\Downloads\墨辰整理书源大全7.0（禁止倒卖）【完整】.json"
    
    if not os.path.exists(source_file):
        print(f"找不到书源文件: {source_file}")
        return

    dl = LegadoDownloader(source_file)
    
    print("=== Legado 书源下载器 ===")
    category = input("输入想要查找的分类 (默认: 小说): ") or "小说"
    rank = input("输入最低等级要求 (如: 优++, 默认: 优): ") or "优"
    
    keyword = input("\n请输入要搜索的书名: ")
    if not keyword:
        return

    # [智能推荐逻辑]
    sources = dl.get_smart_sources(keyword, category, rank)
    print(f"\n初始匹配到 {len(sources)} 个书源，已根据书名完成优先级排序。")
    
    # 优先级 1: 绝对稳定的传统源 (手动配置，作为兜底放在最前面)
    # 如果搜索结果是轻小说类，可以考虑动态调整这部分的顺序，但目前先保持兼容
    sources.insert(0, {
        "bookSourceName": "三叉小说",
        "bookSourceUrl": "http://m.xxxbiquge.info",
        "searchUrl": "/search.php",
        "ruleSearch": {
            "bookList": ".slide-item.list1 div",
            "name": "a p@text",
            "bookUrl": "a.0@href",
            "author": "a.2@text"
        }
    })
    sources.insert(0, {
        "bookSourceName": "69书吧(稳定)",
        "bookSourceUrl": "https://www.69shuba.pro",
        "searchUrl": "/modules/article/search.php",
        "ruleSearch": {"checkKeyWord": "searchkey"}
    })
    sources.insert(0, {
        "bookSourceName": "笔趣阁(备用)",
        "bookSourceUrl": "http://www.biquge.info",
        "searchUrl": "/modules/article/search.php",
        "ruleSearch": {"checkKeyWord": "searchkey"}
    })
    sources.insert(0, {
        "bookSourceName": "笔下文学",
        "bookSourceUrl": "https://www.17bxwx.com",
        "searchUrl": "/search.html",
        "ruleSearch": {"checkKeyWord": "searchkey"}
    })
    sources.insert(0, {
        "bookSourceName": "笔趣阁(稳定)",
        "bookSourceUrl": "https://www.bqg78.com",
        "searchUrl": "/s",
        "ruleSearch": {"checkKeyWord": "q"}
    })
    sources.insert(0, {
        "bookSourceName": "新笔趣阁",
        "bookSourceUrl": "https://www.xbiquge.so",
        "searchUrl": "/modules/article/search.php",
        "ruleSearch": {"checkKeyWord": "searchkey"}
    })
    sources.insert(0, {
        "bookSourceName": "太极小说",
        "bookSourceUrl": "https://69shux.co",
        "searchUrl": "/search.php",
        "ruleSearch": {"checkKeyWord": "keyword"}
    })

    print("\n正在扫描优质源（前15个）...")
    all_results = []
    # 1. 扫描所有源并汇总
    for s in sources[:15]:
        results = dl.search_book(s, keyword)
        if results:
            print(f"✅ 在 [{s['bookSourceName']}] 发现 {len(results)} 个匹配项")
            # 记录来源
            for r in results:
                r['_source_obj'] = s
            all_results.extend(results)
        else:
            print(f"❌ 源 [{s['bookSourceName']}] 未找到结果")

    if not all_results:
        print("所有书源均未找到相关书籍，请尝试更换书名或分类。")
        return

    # 2. 展示汇总结果供用户选择
    print("\n" + "="*40)
    print(f"汇总搜索结果 (共 {len(all_results)} 条):")
    for idx, res in enumerate(all_results):
        print(f"[{idx}] {res['title']} | 作者: {res.get('author', '未知')} | 来源: {res['source']}")
    print("="*40)

    try:
        user_choice = input("\n请输入想要下载的序号 (直接按回车取消): ")
        if not user_choice:
            return
        
        selected_idx = int(user_choice)
        if 0 <= selected_idx < len(all_results):
            target = all_results[selected_idx]
            source_obj = target['_source_obj']
            
            # [新增：前置深度验证]
            dl.cleaner.reset_history() # 下载新书前清空指纹库
            is_ok, msg = dl.verify_source_health(source_obj, target)
            if not is_ok:
                print(f"⚠️  警告: 该书源未通过安全校验！\n原因: {msg}")
                confirm = input("是否忽略警告继续下载？(y/n): ")
                if confirm.lower() != 'y':
                    print("已取消下载。")
                    return

            print(f"\n🚀 正在从 [{target['source']}] 抓取全量内容: {target['title']}...")
            content = dl.get_content(source_obj, target['url'])
            
            if content['type'] != 'error' and content['data']:
                safe_title = "".join([c for c in target['title'] if c.isalnum() or c in (' ', '.', '_')]).rstrip()
                if content['type'] == 'novel':
                    filename = f"{safe_title}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content['data'])
                    print(f"✅ 全本小说下载完成！文件保存至: {filename} (大小: {len(content['data'])/1024:.1f} KB)")
                else:
                    filename = f"{safe_title}_links.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write("\n".join(content['data']))
                    print(f"✅ 链接导出成功！文件保存至: {filename}")
            else:
                print(f"❌ 内容抓取失败: {content['data']}")
        else:
            print("序号输入错误。")
    except ValueError:
        print("请输入有效的数字序号。")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()
