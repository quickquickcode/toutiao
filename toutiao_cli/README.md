# 今日头条 CLI 工具

简洁的今日头条内容发布 CLI 工具，基于 Typer + Playwright 实现。

## 安装

```bash
pip3 install -r requirements.txt
playwright install chromium
```

## 命令结构

```bash
python3 cli.py --help
```

工具包含三个命令组：

| 命令组 | 命令 | 说明 |
|---|---|---|
| `auth` | `login` | 扫码登录 |
| `auth` | `status` | 检查登录状态 |
| `article` | `publish <file>` | 从 Markdown 发布图文文章 |
| `article` | `preview <file>` | 预览 Markdown 解析结果 |
| `micro` | `publish <content>` | 发布微头条 |

## 使用示例

### 登录

```bash
python3 cli.py auth login
```

会打开浏览器扫码登录，登录成功后 Cookie 会自动保存。

### 检查登录状态

```bash
python3 cli.py auth status
```

### 发布图文文章

```bash
python3 cli.py article publish articles/example.md
```

Markdown 格式要求：

- 第一行 `# 标题` 作为文章标题；
- 其余内容作为正文，支持 Markdown 语法（粗体、列表、链接、图片等）。

示例：

```markdown
# 文章标题

正文内容……

## 小标题

- 列表项 1
- 列表项 2

![图片说明](https://example.com/image.jpg)
```

### 预览 Markdown 解析结果

```bash
python3 cli.py article preview articles/example.md
```

### 发布微头条

直接输入内容：

```bash
python3 cli.py micro publish "这是微头条内容"
```

从 Markdown 文件读取：

```bash
python3 cli.py micro publish -f articles/example.md
```

带图片和话题标签（最多 9 张图片，逗号分隔）：

```bash
python3 cli.py micro publish "内容" -i "a.jpg,b.jpg" -t "科技"
```

## 重要说明

本工具目前**不会自动点击最终的“发布”按钮**。它会自动完成以下步骤：

1. 打开浏览器；
2. 完成登录；
3. 打开发布页面；
4. 自动填入标题、正文、图片等内容。

最后需要你在浏览器中**手动点击发布按钮**完成发布。
