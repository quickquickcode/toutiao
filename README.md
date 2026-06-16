# Toutiao 自动化工具集合

本项目包含多个独立的今日头条相关自动化工具，分别适用于不同场景。

## 子项目入口一览

| 子项目 | 主要入口 | 适用场景 |
|---|---|---|
| `toutiao_mcp_server` | `python start_server.py` | 功能最完整的 MCP 服务器，支持自动登录、图文/微头条发布、数据分析、多平台兼容（小红书格式）。 |
| `toutiao_cli` | `python3 cli.py` | Python 命令行工具，支持登录、发布图文文章、发布微头条、检查登录状态。 |
| `toutiao_npm_cli` | `node dist/index.js` | Node.js 命令行工具，主要用于发布微头条，支持 Markdown 文件。 |
| `toutiao_scraper` | `python3 scraper.py` | Playwright 爬虫，抓取今日头条科技频道文章到 JSONL。 |
| `toutiao_scraper/web/今日头条.html` | 浏览器打开 | 今日头条网页静态快照。 |
| `toutiao_skill` | 多个调试脚本 | 实验性调试脚本和 scraper 集合，非正式入口。 |

## 快速选择

- **要发布内容到今日头条** → 推荐 `toutiao_mcp_server`，功能最全、自动化程度最高。
- **只要一个简单的 Python 命令行发布工具** → 使用 `toutiao_cli`。
- **偏好 Node.js / TypeScript** → 使用 `toutiao_npm_cli`。
- **要抓取头条文章数据** → 使用 `toutiao_scraper`。
- **要查看保存的头条页面快照** → 打开 `toutiao_scraper/web/今日头条.html`。

## 各子项目详情

各子项目均有独立的 README，详情请进入对应目录查看：

- [toutiao_cli/README.md](./toutiao_cli/README.md)
- [toutiao_mcp_server/README.md](./toutiao_mcp_server/README.md)
- [toutiao_npm_cli/README.md](./toutiao_npm_cli/README.md)
- [toutiao_scraper/README.md](./toutiao_scraper/README.md)
