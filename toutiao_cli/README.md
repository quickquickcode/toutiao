# 今日头条 CLI 工具

简洁的今日头条内容发布 CLI 工具。

## 安装

```bash
pip3 install -r requirements.txt
playwright install chromium
```

## 使用

### 登录
```bash
python3 cli.py login
```

### 发布文章
```bash
python3 cli.py publish articles/example.md
```

### 发布微头条
```bash
python3 cli.py micro "这是微头条内容"
```

### 检查状态
```bash
python3 cli.py status
```
