import os
from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__)

# 配置漫画根目录
MANGA_ROOT = r"D:\book\manga"

def get_manga_list():
    if not os.path.exists(MANGA_ROOT):
        return []
    return sorted([d for d in os.listdir(MANGA_ROOT) if os.path.isdir(os.path.join(MANGA_ROOT, d))])

def get_chapter_list(manga_name):
    manga_path = os.path.join(MANGA_ROOT, manga_name)
    if not os.path.exists(manga_path):
        return []
    return sorted([d for d in os.listdir(manga_path) if os.path.isdir(os.path.join(manga_path, d))])

def get_images(manga_name, chapter_name):
    chapter_path = os.path.join(MANGA_ROOT, manga_name, chapter_name)
    if not os.path.exists(chapter_path):
        return []
    images = [f for f in os.listdir(chapter_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    return sorted(images)

@app.route('/')
def index():
    mangas = get_manga_list()
    return render_template('index.html', mangas=mangas)

@app.route('/manga/<manga_name>')
def manga_detail(manga_name):
    chapters = get_chapter_list(manga_name)
    return render_template('manga.html', manga_name=manga_name, chapters=chapters)

@app.route('/manga/<manga_name>/<chapter_name>')
def read_chapter(manga_name, chapter_name):
    chapters = get_chapter_list(manga_name)
    images = get_images(manga_name, chapter_name)
    
    # 查找上一章和下一章
    try:
        idx = chapters.index(chapter_name)
        prev_chap = chapters[idx-1] if idx > 0 else None
        next_chap = chapters[idx+1] if idx < len(chapters) - 1 else None
    except ValueError:
        prev_chap = next_chap = None

    return render_template('reader.html', 
                           manga_name=manga_name, 
                           chapter_name=chapter_name, 
                           images=images,
                           prev_chap=prev_chap,
                           next_chap=next_chap)

@app.route('/image/<path:filename>')
def serve_image(filename):
    # 注意：在 Windows 下路径处理
    path_parts = filename.split('/')
    directory = os.path.join(MANGA_ROOT, *path_parts[:-1])
    return send_from_directory(directory, path_parts[-1])

if __name__ == '__main__':
    print(f"漫画服务器启动中... 根目录: {MANGA_ROOT}")
    app.run(debug=True, port=5000)
