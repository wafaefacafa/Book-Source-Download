import re
import os

def diagnose_novel(file_path):
    print(f"--- 正在诊断文件: {os.path.basename(file_path)} ---")
    chapters = []
    # 匹配标题模式，例如 【第七百八十二章 ...】 或 第四章 入学
    pattern = re.compile(r'(【?第[一二三四五六七八九十百千万\d]+[章节][^】\n]*】?)')
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f, 1):
            match = pattern.search(line)
            if match:
                chapters.append((i, match.group(1)))
    
    print(f"总计提取到 {len(chapters)} 个章节标题标识。")
    print("前 10 个章节标识:")
    for i, (line_num, title) in enumerate(chapters[:10]):
        print(f"  行 {line_num}: {title}")
    
    print("\n末尾 10 个章节标识:")
    for i, (line_num, title) in enumerate(chapters[-10:]):
        print(f"  行 {line_num}: {title}")

diagnose_novel(r"C:\Users\www20\source\repos\legado-downloader\斗罗大陆3龙王传说.txt")
diagnose_novel(r"C:\Users\www20\source\repos\legado-downloader\斗罗大陆3龙王传说_修复版.txt")
