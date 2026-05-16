# Legado Book Source Downloader (阅读书源下载器)

这是一个基于 [Legado (阅读)](https://github.com/gedoor/legado) 书源协议的小说/漫画下载工具。它可以自动解析书源规则，从多个优质源中搜索并批量下载全本小说。

## 🌟 核心功能

- **多源聚合搜索**：一次性扫描多个优质书源，并汇总结果，支持手动选择最佳源。
- **全量下载**：打破下载限制，支持数千章节一键抓取并合并为单个文件。
- **智能排序与修复**：内置章节自动检测与排序逻辑，解决 API 返回乱序的问题。
- **完全兼容 Legado**：直接适配阅读书源规则（支持 API 类和 DOM 类抓取）。
- **TXT 自动导出**：下载完成后自动生成干净、规范的 TXT 电子书。

## 🚀 快速开始

### 环境依赖
- Python 3.10+
- 依赖库：`requests`, `beautifulsoup4`

### 安装
```bash
git clone https://github.com/wafaefacafa/Book-Source-Download.git
cd Book-Source-Download
pip install -r requirements.txt
```

### 使用
运行主程序并输入书名即可：
```bash
python main.py
```

## 🛠️ 技术路线

1. **规则解析**：模拟阅读 App 的书源处理流程，解析搜索、目录和正文逻辑。
2. **多模式匹配**：支持 API 全局网关、GET 传参及常规网页爬虫抓取。
3. **内容清洗**：自动剔除 HTML 标签、Base64 杂质及广告脚本。

## 📅 开发计划 (Roadmap)

- [x] 小说全量批量下载
- [x] 章节排序自动校准机制
- [ ] **漫画下载支持** (测试中...)
- [ ] 导出为 EPUB/PDF 格式
- [ ] 并发下载加速

## 🤝 贡献
欢迎提交 Issue 或 Pull Request 来优化书源解析效率。

---
*声明：本工具仅供学习交流使用。所有抓取内容版权归原作者所有。*

