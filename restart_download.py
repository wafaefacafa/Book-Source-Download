import json
import os
from src.downloader_new import LegadoDownloader

KEYWORD = '我家老婆来意一千年前'

def safe_name(title):
    return "".join(c for c in title if c.isalnum() or c in (' ', '.', '_')).rstrip()

source_file = r"C:\Users\www20\Downloads\墨辰整理书源大全7.0（禁止倒卖）【完整】.json"
if not os.path.exists(source_file):
    print('未找到书源文件:', source_file)
    raise SystemExit(1)

dl = LegadoDownloader(source_file)

results = []
# 优先使用 filter 后的来源列表（小说类、优级）
try:
    candidates = dl.filter_sources('小说', '优')
except Exception:
    candidates = dl.sources

print(f"将从 {len(candidates)} 个候选书源中检索: {KEYWORD}")
for s in candidates:
    print('搜索来源:', s.get('bookSourceName'))
    try:
        res = dl.search_book(s, KEYWORD)
        if res:
            print(f"在 {s.get('bookSourceName')} 找到 {len(res)} 条结果")
            for r in res:
                r['_source_obj'] = s
            results.extend(res)
        else:
            print(f"{s.get('bookSourceName')} 未找到")
    except Exception as e:
        print('搜索出错:', e)

if not results:
    print('未在书源中找到目标书目。')
    raise SystemExit(0)

# 选择最可能的结果
chosen = None
for r in results:
    title = r.get('title', '') or r.get('name', '')
    if KEYWORD in title or title.replace(' ', '') == KEYWORD:
        chosen = r
        break
if not chosen:
    chosen = results[0]

print('选择下载:', chosen.get('title'), '来自', chosen.get('source'))
content = dl.get_content(chosen['_source_obj'], chosen.get('url') or chosen.get('bookUrl') or chosen.get('url_list'))
if content.get('type') == 'novel' and content.get('data'):
    fname = safe_name(chosen.get('title', KEYWORD)) + '.txt'
    outp = os.path.join(os.path.dirname(__file__), fname)
    with open(outp, 'w', encoding='utf-8') as f:
        f.write(content['data'])
    print('下载完成，保存为:', outp)
else:
    print('抓取失败或返回非小说类型:', content)
