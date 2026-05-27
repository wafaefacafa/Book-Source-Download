import re
import os

def cn2an(cn):
    char_map = {'零':0, '一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9}
    unit_map = {'十':10, '百':100, '千':1000, '万':10000}
    val = 0
    temp = 0
    if cn.startswith('十'): cn = '一' + cn
    for char in cn:
        if char in char_map:
            temp = char_map[char]
        elif char in unit_map:
            u = unit_map[char]
            if temp == 0: temp = 1
            val += temp * u
            temp = 0
    val += temp
    return val

def get_sort_key(title):
    num_match = re.search(r'(\d+)', title)
    if num_match:
        return int(num_match.group(1))
    cn_match = re.search(r'第([一二三四五六七八九十百千万]+)[章节]', title)
    if cn_match:
        try:
            return cn2an(cn_match.group(1))
        except:
            pass
    return 999999

def clean_content(text):
    replacements = {
        'ddtxt9點com': '他', 'ddtxt9.com': '他', 'ddtxt9点com': '他',
        'nxalmヽcom': '你', 'ncxsw.cc': '', 'ncxsw。cc': '',
        'bqgdo.cc': '', 'bqgdo♀cc': '', 'bqgdo。cc': '',
        '笔＠趣＠阁': '', '笔？趣？阁': '', '笔×趣×阁': '',
        '天籁小说．2': '', '天籁小说': '',
        'ｗWｗ。ｂiquge。ｉｎfo': '', 'ｗWｗ。ｂｉｑｕｇｅ。ｉｎｆｏ': '',
        '未完待续。': '', '(未完待续)': ''
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'https?://[a-zA-Z0-9.\-/]+', '', text)
    return text

def process_novel():
    input_files = [
        r"C:\Users\www20\source\repos\legado-downloader\斗罗大陆3龙王传说_修复版.txt",
        r"C:\Users\www20\source\repos\legado-downloader\斗罗大陆3龙王传说.txt"
    ]
    output_path = r"C:\Users\www20\source\repos\legado-downloader\龙王传说_SUPREME_Final.txt"
    chapter_dict = {}
    
    # 更加严谨的标题匹配：必须独占一行，或者以【】包裹
    # 增加对假标题的过滤，例如正文里提到的“第xxx章”
    title_pattern = re.compile(r'^\s*(【?第[一二三四五六七八九十百千万\d]+[章节][^】\n\d]*】?)\s*$')

    for file_path in input_files:
        if not os.path.exists(file_path): continue
        print(f"正在深度解析: {os.path.basename(file_path)}")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_title = "START"
            current_content = []
            for line in f:
                raw_line = line.strip()
                # 过滤掉过短的行或纯广告行作为标题
                if 2 < len(raw_line) < 50 and title_pattern.match(raw_line):
                    # 识别到可能的新章节
                    if current_title != "START":
                        txt = "\n".join(current_content).strip()
                        if txt:
                            # 拼接逻辑：如果该章节号已存在，对比内容，如果不同则合并
                            if current_title in chapter_dict:
                                if len(txt) > len(chapter_dict[current_title]) * 1.5: # 如果新内容由于原内容很多，替换
                                     chapter_dict[current_title] = txt
                                elif txt[:20] not in chapter_dict[current_title]: # 如果开头不同，可能是续写，合并
                                     chapter_dict[current_title] += "\n" + txt
                            else:
                                chapter_dict[current_title] = txt
                    
                    current_title = raw_line
                    current_content = []
                else:
                    current_content.append(line)
            
            # 处理最后一个章节
            if current_title != "START":
                txt = "\n".join(current_content).strip()
                if txt:
                    if current_title in chapter_dict:
                        if len(txt) > len(chapter_dict[current_title]):
                             chapter_dict[current_title] = txt
                    else:
                        chapter_dict[current_title] = txt

    # 移除重复和无用的干扰项
    valid_keys = [k for k in chapter_dict.keys() if k != "START"]
    # 再次过滤：标题下内容少于50字的很可能是误判的广告标题，除非是序言
    valid_keys = [k for k in valid_keys if len(chapter_dict[k]) > 50 or "引子" in k or "序" in k]
    
    sorted_titles = sorted(valid_keys, key=get_sort_key)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for title in sorted_titles:
            # 清洗正文
            content = clean_content(chapter_dict[title])
            f.write(title + "\n\n" + content + "\n\n")
    print(f"终极版已生成！共 {len(sorted_titles)} 章。已保存至: {output_path}")

process_novel()
