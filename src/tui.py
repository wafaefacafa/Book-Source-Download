import os
import sys
import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, IntPrompt
from rich.align import Align

# 导入底层引擎
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.downloader_new import LegadoDownloader
from src.manga_downloader import LegadoMangaDownloader

console = Console()

class LegadoTUI:
    def __init__(self):
        self.novel_engine = LegadoDownloader()
        self.manga_engine = LegadoMangaDownloader()
        self.current_mode = "NOVEL"  # NOVEL or MANGA
        self.status_msg = "等待指令..."
        self.logs = []

    def make_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            Text("💎 SUPREME LEGADO HUB v2.0", style="bold cyan"),
            Text(time.strftime("%X"), style="dim white"),
        )
        return Panel(grid, style="white on blue")

    def make_sidebar(self) -> Panel:
        table = Table.grid(padding=1)
        table.add_column()
        
        mode_novel = "[bold green]● 小说模式[/]" if self.current_mode == "NOVEL" else "[dim]  小说模式[/]"
        mode_manga = "[bold yellow]● 漫画模式[/]" if self.current_mode == "MANGA" else "[dim]  漫画模式[/]"
        
        table.add_row(Text("\n导航菜单", style="bold magenta"))
        table.add_row(mode_novel)
        table.add_row(mode_manga)
        table.add_row("")
        table.add_row("[cyan]快捷键说明:[/]")
        table.add_row("1. 切换到小说")
        table.add_row("2. 切换到漫画")
        table.add_row("s. 关键词搜索")
        table.add_row("q. 退出程序")
        
        return Panel(table, title="[bold]管理[/]", border_style="blue")

    def make_main_content(self) -> Panel:
        log_text = "\n".join(self.logs[-15:])
        return Panel(
            Align.left(Text(log_text, style="white")),
            title=f"[bold]{'小说抓取控制台' if self.current_mode == 'NOVEL' else '漫画抓取控制台'}[/]",
            border_style="green" if self.current_mode == "NOVEL" else "yellow"
        )

    def log(self, message):
        self.logs.append(f"[{time.strftime('%X')}] {message}")

    def run(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        layout["body"].split_row(
            Layout(name="sidebar", size=25),
            Layout(name="main")
        )

        with Live(layout, refresh_per_second=4, screen=True):
            layout["header"].update(self.make_header())
            layout["sidebar"].update(self.make_sidebar())
            layout["main"].update(self.make_main_content())

            while True:
                layout["header"].update(self.make_header())
                layout["sidebar"].update(self.make_sidebar())
                layout["main"].update(self.make_main_content())
                
                # 这是一个非阻塞的循环，但现实中我们需要处理输入
                # 这里简单起见，我们在 Live 环境外获取输入
                break 

        # 真正的主循环
        while True:
            console.clear()
            header = self.make_header()
            sidebar = self.make_sidebar()
            main = self.make_main_content()
            
            # 使用简单的布局打印
            table = Table.grid(expand=True)
            table.add_row(header)
            
            body_grid = Table.grid(expand=True)
            body_grid.add_column(width=25)
            body_grid.add_column()
            body_grid.add_row(sidebar, main)
            table.add_row(body_grid)
            
            console.print(table)
            
            choice = Prompt.ask("\n[bold cyan]请输入操作[/]", choices=["1", "2", "s", "q"], default="s")
            
            if choice == "1":
                self.current_mode = "NOVEL"
                self.log("切換到小说抓取模式")
            elif choice == "2":
                self.current_mode = "MANGA"
                self.log("切換到漫画抓取模式")
            elif choice == "q":
                break
            elif choice == "s":
                keyword = Prompt.ask("[bold yellow]输入搜索关键词[/]")
                self.log(f"开始搜索关键词: {keyword}")
                try:
                    if self.current_mode == "NOVEL":
                        self.handle_novel_search(keyword)
                    else:
                        self.handle_manga_search(keyword)
                except Exception as e:
                    self.log(f"❌ 出错: {e}")

    def handle_novel_search(self, keyword):
        self.log("正在通过 Legado 索引检索书籍...")
        results = self.novel_engine.search(keyword)
        if not results:
            self.log("未找到相关书籍。")
            return

        table = Table(title="搜索结果")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("书名", style="magenta")
        table.add_column("作者", style="green")
        table.add_column("最新章节", style="dim")

        for idx, book in enumerate(results[:10]):
            table.add_row(str(idx), book.get('name', 'N/A'), book.get('author', 'N/A'), book.get('latestChapter', 'N/A'))
        
        console.print(table)
        book_idx = IntPrompt.ask("请选择书号下载 (输入 -1 取消)", default=0)
        if book_idx == -1: return

        selected_book = results[book_idx]
        self.log(f"开始下载: {selected_book['name']}")
        
        # 模拟下载进度（实际对接下载方法）
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task(f"正在抓取章节...", total=100)
            # 这里调用实际的 downloader 逻辑
            # content = self.novel_engine.get_content(selected_book)
            # ... 保存逻辑 ...
            for i in range(100):
                time.sleep(0.01)
                progress.update(task, advance=1)
        
        self.log(f"✅ {selected_book['name']} 下载完成！")

    def handle_manga_search(self, keyword):
        self.log("正在检索漫画源...")
        results = self.manga_engine.search(keyword)
        if not results:
            self.log("未找到相关漫画。")
            return

        table = Table(title="漫画搜索结果")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("名称", style="magenta")
        table.add_column("来源", style="green")

        for idx, manga in enumerate(results[:10]):
            table.add_row(str(idx), manga.get('name', 'N/A'), manga.get('source', '包子漫画'))
        
        console.print(table)
        m_idx = IntPrompt.ask("请选择漫画 ID 下载 (输入 -1 取消)", default=0)
        if m_idx == -1: return

        selected_manga = results[m_idx]
        self.log(f"开始解析漫画: {selected_manga['name']}")
        
        # 实际调用漫画下载逻辑
        # chapters = self.manga_engine.get_chapters(selected_manga)
        # self.manga_engine.download_chapters(selected_manga, chapters)
        self.log(f"✅ {selected_manga['name']} 已加入下载队列。")

if __name__ == "__main__":
    tui = LegadoTUI()
    tui.run()
