import sys
import os
import zipfile
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import (QApplication, QMainWindow, QListWidget, QSplitter, 
                             QVBoxLayout, QWidget, QFileDialog, QToolBar, QStatusBar)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl

class EpubReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简单 EPUB 阅读器")
        self.setGeometry(100, 100, 1000, 700)
        
        self.epub_path = None
        self.chapters = [] # 存储章节信息: {"title": str, "content": str}

        self.init_ui()

    def init_ui(self):
        # 菜单栏/工具栏
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        open_action = toolbar.addAction("打开 EPUB")
        open_action.triggered.connect(self.open_file)

        # 主内容区域使用拆分器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧章节列表
        self.chapter_list = QListWidget()
        self.chapter_list.itemClicked.connect(self.display_chapter)
        self.chapter_list.setMaximumWidth(250)
        
        # 右侧 Web 视图
        self.web_view = QWebEngineView()
        # 设置一点默认样式
        self.web_view.setHtml("<html><body style='font-family: sans-serif; padding: 20px; line-height: 1.6;'><h1>欢迎使用</h1><p>点击上方工具栏打开一个 EPUB 文件开始阅读。</p></body></html>")

        splitter.addWidget(self.chapter_list)
        splitter.addWidget(self.web_view)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 EPUB 文件", "D:\\book", "EPUB Files (*.epub)")
        if file_path:
            self.load_epub(file_path)

    def load_epub(self, path):
        self.epub_path = path
        self.chapters = []
        self.chapter_list.clear()
        
        try:
            with zipfile.ZipFile(path, 'r') as z:
                # 简单处理：寻找所有的 html/xhtml 文件
                # 在真实应用中应该解析 content.opf 获取正确的顺序
                file_list = z.namelist()
                html_files = sorted([f for f in file_list if f.endswith(('.html', '.xhtml'))])
                
                for f_name in html_files:
                    with z.open(f_name) as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # 尝试提取标题
                        title = "未命名章节"
                        if soup.h1:
                            title = soup.h1.get_text()
                        elif soup.title:
                            title = soup.title.get_text()
                        
                        # 简易清理：移除一些可能冲突的样式，或者在这里注入自定义 CSS
                        # 这里我们保留原始内容，但在 WebEngine 中渲染
                        self.chapters.append({"title": title, "content": content})
                        self.chapter_list.addItem(title)
            
            self.status_bar.showMessage(f"成功加载: {os.path.basename(path)} (共 {len(self.chapters)} 章)")
            if self.chapters:
                self.chapter_list.setCurrentRow(0)
                self.display_chapter(self.chapter_list.item(0))
                
        except Exception as e:
            self.status_bar.showMessage(f"加载失败: {str(e)}")

    def display_chapter(self, item):
        row = self.chapter_list.row(item)
        if 0 <= row < len(self.chapters):
            chapter = self.chapters[row]
            # 注入 CSS 以符合 PC 阅读习惯 (大字体、间距、居中背景等)
            custom_css = """
            <style>
                body {
                    font-family: "Microsoft YaHei", sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 40px;
                    line-height: 1.8;
                    color: #333;
                    background-color: #f4f4f4;
                }
                h1 { border-bottom: 2px solid #ddd; padding-bottom: 10px; color: #1a1a1a; }
                p { margin-bottom: 1.5em; text-indent: 2em; text-align: justify; }
            </style>
            """
            full_html = custom_css + chapter['content']
            self.web_view.setHtml(full_html)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = EpubReader()
    reader.show()
    sys.exit(app.exec())
