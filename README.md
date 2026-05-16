# Legado Book Downloader

这是一个基于“阅读” (Legado) 书源格式的电子书下载器。

## 功能
- 加载 Legado 格式的 JSON 书源。
- 根据书源规则搜索书籍。
- 提取章节列表并下载正文。
- 支持小说和漫画类源。

## 环境要求
- Python 3.8+
- 依赖项：`requests`, `beautifulsoup4`, `lxml`

## 安装
```bash
pip install -r requirements.txt
```

## 使用
1. 将书源 JSON 文件放在项目目录下或指定路径。
2. 运行 `python main.py` 开始搜索和下载。
