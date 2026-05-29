# 今日头条 CLI 工具

命令行工具，用于自动化发布微头条。支持从 Markdown 文件解析内容发布。

## 功能

- 登录状态持久化（Cookie + LocalStorage）
- 发布微头条（支持 Markdown 文件或直接输入文本）
- 图片上传
- Debug 模式（调试定位器）

## 安装

```bash
npm install
npm run build
```

## 使用

### 1. 登录

```bash
node dist/index.js login
```

打开浏览器后手动登录，登录成功后会自动保存 Cookie 到 `storage/cookies.json`。

### 2. 发布微头条

**直接输入内容：**
```bash
node dist/index.js post weibo -c "这是内容"
```

**从 Markdown 文件发布：**
```bash
node dist/index.js post weibo -f content/2026-04-15/article.md
```

**带图片发布：**
```bash
node dist/index.js post weibo -f content/2026-04-15/article.md -i content/2026-04-15/image.jpg
```

### 3. Debug 模式

```bash
node dist/index.js post weibo -d
```

打开浏览器并记录你的点击操作，用于调试定位器。

## 项目结构

```
toutiao_npm_cli/
├── src/
│   ├── index.ts           # CLI 入口
│   ├── commands/
│   │   ├── login.ts       # 登录命令
│   │   └── post.ts        # 发布命令
│   └── lib/
│       ├── browser.ts     # Playwright 浏览器管理
│       ├── cookie.ts      # Cookie 持久化
│       └── md.ts          # Markdown 解析
├── content/               # 发布内容（按日期组织）
│   └── 2026-04-15/
│       ├── article.md     # 文章 Markdown 文件
│       └── image.jpg      # 图片文件
├── storage/
│   ├── cookies.json       # 保存的登录 Cookie
│   └── storage.json       # 保存的 LocalStorage
└── dist/                  # 编译后的 JS 文件
```

## 内容管理

建议将待发布的内容放在 `content/YYYY-MM-DD/` 目录下：

```
content/
├── 2026-04-15/
│   ├── ai-intro.md
│   ├── ai-venice-beach.md
│   └── venice-beach.jpg
└── 2026-04-16/
    └── another-post.md
```

## 技术栈

- [Playwright](https://playwright.dev/) - 浏览器自动化
- [Commander.js](https://github.com/tj/commander.js) - CLI 框架
- [marked](https://marked.js.org/) - Markdown 解析
