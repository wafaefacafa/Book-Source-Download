import os
import re
from ebooklib import epub
from PIL import Image
from io import BytesIO

class MangaToEpub:
    def __init__(self, manga_dir, output_file, title, chapters_per_vol=0):
        self.manga_dir = manga_dir
        self.output_file = output_file
        self.title = title
        self.chapters_per_vol = chapters_per_vol # 0 表示不分卷
        self.book = None

    def _init_book(self, vol_index=None):
        self.book = epub.EpubBook()
        display_title = self.title if vol_index is None else f"{self.title} Vol.{vol_index}"
        self.book.set_title(display_title)
        self.book.set_language('zh')

    def add_chapter(self, chapter_path, chapter_title, chapter_index):
        # ... (保持原有 add_chapter 逻辑不变，但使用 self.book)
        images = [f for f in os.listdir(chapter_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        images.sort()
        
        if not images:
            return

        chapter_id = f'chap_{chapter_index:04d}'
        content = f'<html><body><h1>{chapter_title}</h1>'
        
        for i, img_name in enumerate(images):
            img_path = os.path.join(chapter_path, img_name)
            img_ext = os.path.splitext(img_name)[1].lower()[1:]
            if img_ext == 'webp': img_ext = 'jpeg'
            
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
            content += f'<div style="text-align:center;"><img src="{img_filename}" /></div>'

        content += '</body></html>'
        epub_chap = epub.EpubHtml(title=chapter_title, file_name=f'{chapter_id}.xhtml', content=content)
        self.book.add_item(epub_chap)
        return epub_chap

    def convert(self):
        print(f"开始打包: {self.title}")
        chapters = [d for d in os.listdir(self.manga_dir) if os.path.isdir(os.path.join(self.manga_dir, d))]
        chapters.sort()

        if self.chapters_per_vol <= 0:
            # 一体化打包
            self._init_book()
            spine = ['nav']
            toc = []
            for i, chap_dir in enumerate(chapters):
                chap_path = os.path.join(self.manga_dir, chap_dir)
                display_title = re.sub(r'^\d+_', '', chap_dir)
                print(f"[{i+1}/{len(chapters)}] 正在添加到合集: {display_title}")
                epub_chap = self.add_chapter(chap_path, display_title, i)
                if epub_chap:
                    spine.append(epub_chap)
                    toc.append(epub_chap)
            
            self.book.toc = tuple(toc)
            self.book.add_item(epub.EpubNav())
            self.book.add_item(epub.EpubNcx())
            self.book.spine = spine
            epub.write_epub(self.output_file, self.book)
        else:
            # 分卷打包逻辑
            for vol_idx, i in enumerate(range(0, len(chapters), self.chapters_per_vol), 1):
                self._init_book(vol_idx)
                spine = ['nav']
                toc = []
                vol_chapters = chapters[i:i + self.chapters_per_vol]
                
                vol_output = self.output_file.replace('.epub', f'_Vol{vol_idx}.epub')
                print(f"\n正在打包第 {vol_idx} 卷 ({i+1}-{min(i+self.chapters_per_vol, len(chapters))}章)...")

                for j, chap_dir in enumerate(vol_chapters):
                    chap_path = os.path.join(self.manga_dir, chap_dir)
                    display_title = re.sub(r'^\d+_', '', chap_dir)
                    epub_chap = self.add_chapter(chap_path, display_title, i + j)
                    if epub_chap:
                        spine.append(epub_chap)
                        toc.append(epub_chap)

                self.book.toc = tuple(toc)
                self.book.add_item(epub.EpubNav())
                self.book.add_item(epub.EpubNcx())
                self.book.spine = spine
                epub.write_epub(vol_output, self.book)

        print("\n✅ 所有打包任务完成！")

if __name__ == "__main__":
    # 配置
    manga_name = "斗罗大陆4终极斗罗"
    manga_source = rf"D:\book\manga\{manga_name}"
    output_epub = rf"D:\book\manga\{manga_name}.epub"
    
    # 选项：0 为一体化打包，>0 为分卷打包（每卷包含的章节数）
    CHAPTERS_PER_VOL = 0 

    if os.path.exists(manga_source):
        converter = MangaToEpub(manga_source, output_epub, manga_name, chapters_per_vol=CHAPTERS_PER_VOL)
        converter.convert()
    else:
        print(f"错误: 找不到目录 {manga_source}")
