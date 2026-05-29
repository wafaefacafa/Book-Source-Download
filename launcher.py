import subprocess
import os
import sys

def launch():
    # 定义路径
    project_root = r"c:\Users\www20\source\repos\legado-downloader"
    python_exe = r"C:/Users/www20/AppData/Local/Python/bin/python3.14.exe"

    if not os.path.exists(python_exe):
        python_exe = sys.executable

    # 启动统一 TUI 管理界面
    tui_cmd = f"cd '{project_root}'; & '{python_exe}' src/tui.py"

    print("🚀 正在初始化 SUPREME 全能管理终端...")

    try:
        # 启动统一 TUI
        subprocess.Popen(['powershell', '-NoExit', '-Command', tui_cmd], creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        print("\n" + "="*40)
        print("✅ SUPREME TUI 已部署！")
        print("📊 统一界面: [小说/漫画/索引/清洗] 全集成")
        print("="*40)
        print("请在弹出的新窗口中管理您的任务。")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    launch()
