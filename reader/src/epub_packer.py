import os
import re
from ebooklib import epub
from PIL import Image
from io import BytesIO

class MangaToEpub:
    def __init__(self, manga_dir, output_file, title):
        self.manga_dir = manga_dir
        self.output_file = output_file
        self.title = title
        self.book = epub.EpubBook()
        self.book.set_title(title)
        self.book.set_language('zh')

    def add_chapter(self, chapter_path, chapter_title, chapter_index):
        # 获取所有图片并排序
        images = [f for f in os.listdir(chapter_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        images.sort()
        
        if not images:
            return

        chapter_id = f'chap_{chapter_index:04d}'
        # 创建章节 HTML 内容
        content = f'<html><body><h1>{chapter_title}</h1>'
        
        chapter_items = []
        for i, img_name in enumerate(images):
            img_path = os.path.join(chapter_path, img_name)
            img_ext = os.path.splitext(img_name)[1].lower()[1:]
            if img_ext == 'webp': img_ext = 'jpeg' # 某些阅读器对 webp 支持有限，虽然 ebooklib 支持，但这里保持原样或转换
            
            # 读取并优化图片 (可选：缩小尺寸以减小 epub 体积)
            with open(img_path, 'rb') as f:
                img_data = f.read()
            
            img_filename = f'images/{chapter_id}_{i:03d}{os.path.splitext(img_name)[1]}'
            epub_img = epub.EpubItem(
                uid=f'{chapter_id}_{i:03d}',
                file_name=img_filename,
                content=img_data,
                media_type=f'image/{img_ext}'
            )
            self.book.add_item(epub_img)
            content += f'<div style="text-align:center;"><img src="{img_filename}" alt="{img_name}" /></div>'
            chapter_items.append(epub_img)

        content += '</body></html>'
        
        # 创建章节对象
        epub_chap = epub.EpubHtml(title=chapter_title, file_name=f'{chapter_id}.xhtml', content=content)
        self.book.add_item(epub_chap)
        return epub_chap

    def convert(self):
        print(f"开始打包: {self.title}")
        # 获取所有章节文件夹并排序
        chapters = [d for d in os.listdir(self.manga_dir) if os.path.isdir(os.path.join(self.manga_dir, d))]
        chapters.sort()

        spine = ['nav']
        toc = []

        for i, chap_dir in enumerate(chapters):
            chap_path = os.path.join(self.manga_dir, chap_dir)
            # 移除 0001_ 这种前缀作为标题
            display_title = re.sub(r'^\d+_', '', chap_dir)
            print(f"正在处理: {display_title}...")
            
            epub_chap = self.add_chapter(chap_path, display_title, i)
            if epub_chap:
                self.book.add_item(epub_chap)
                spine.append(epub_chap)
                toc.append(epub_chap)

        self.book.toc = tuple(toc)
        self.book.add_item(epub.EpubNav())
        self.book.add_item(epub.EpubNcx())
        self.book.spine = spine

        print(f"正在保存到: {self.output_file} ...")
        epub.write_epub(self.output_file, self.book)
        print("打包完成！")

if __name__ == "__main__":
    manga_source = r"D:\book\manga\斗罗大陆3龙王传说"
    output_epub = r"D:\book\manga\斗罗大陆3龙王传说.epub"
    
    if os.path.exists(manga_source):
        converter = MangaToEpub(manga_source, output_epub, "斗罗大陆3 龙王传说")
        converter.convert()
    else:
        print(f"错误: 找不到目录 {manga_source}")
