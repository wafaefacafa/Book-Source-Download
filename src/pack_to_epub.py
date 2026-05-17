import os
import re
from ebooklib import epub

def txt_to_epub(txt_dir, output_epub, title, author="唐家三少"):
    book = epub.EpubBook()

    # 设置元数据
    book.set_identifier('id123456')
    book.set_title(title)
    book.set_language('zh')
    book.add_author(author)

    # 获取所有txt文件并排序
    files = [f for f in os.listdir(txt_dir) if f.endswith('.txt')]
    
    # 尝试按文件名中的数字排序
    def extract_number(filename):
        nums = re.findall(r'\d+', filename)
        return int(nums[0]) if nums else 0
    
    files.sort(key=extract_number)

    chapters = []
    print(f"正在打包 {len(files)} 个章节...")

    for i, filename in enumerate(files):
        file_path = os.path.join(txt_dir, filename)
        chapter_title = filename.replace('.txt', '')
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # 将换行符转换为 HTML 段落
        html_content = f'<h1>{chapter_title}</h1>'
        paragraphs = content.split('\n')
        for p in paragraphs:
            if p.strip():
                html_content += f'<p>{p.strip()}</p>'

        # 创建 Epub 章节
        c = epub.EpubHtml(title=chapter_title, file_name=f'chap_{i+1}.xhtml', lang='zh')
        c.content = html_content
        book.add_item(c)
        chapters.append(c)
        
        if (i + 1) % 100 == 0:
            print(f"已处理 {i + 1} 章节...")

    # 定义书籍结构
    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 定义阅读顺序
    book.spine = ['nav'] + chapters

    # 保存文件
    epub.write_epub(output_epub, book, {})
    print(f"打包完成！文件保存至: {output_epub}")

if __name__ == "__main__":
    txt_dir = r"D:\book\novel\斗罗大陆4终极斗罗"
    output_epub = r"D:\book\novel\斗罗大陆4终极斗罗.epub"
    txt_to_epub(txt_dir, output_epub, "斗罗大陆4终极斗罗")
