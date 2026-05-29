# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Node.js CLI tool for automating Weibo (microblog) posting on Toutiao (今日头条). Uses Playwright for browser automation with Cookie + LocalStorage persistence for login state.

## Commands

```bash
# Build TypeScript
npm run build

# Run CLI
node dist/index.js login                           # Login and save session
node dist/index.js post weibo -c "text"           # Post text directly
node dist/index.js post weibo -f path/to/md       # Post from Markdown file
node dist/index.js post weibo -f md -i image.jpg  # Post with image
node dist/index.js post weibo -d                   # Debug mode (record clicks)

# Development
npx ts-node src/index.ts post weibo -f md -d      # Run with ts-node
```

## Architecture

**Single Browser Instance Pattern**: `browser.ts` maintains global singleton `browser` and `context` variables. All commands reuse the same browser instance to preserve session state across commands.

**Login Flow** (`login.ts`):
1. Launch visible Chromium browser
2. User manually logs in via 今日头条 OAuth
3. Detect login success via URL change to `/profile_v4`
4. Persist `cookies.json` and `storage.json` (localStorage/sessionStorage)

**Publishing Flow** (`post.ts`):
1. Load saved session from storage
2. Navigate to `https://mp.toutiao.com/profile_v4/weitoutiao/publish`
3. Close modal overlay (`byte-drawer-mask`) via JavaScript dispatch
4. Focus editor (`div.ProseMirror`) using triple fallback: JS click → page.click → mouse.click
5. Type content via `keyboard.type()`
6. Upload image via `input[type="file"].setInputFiles()`
7. Click publish via JavaScript (find `span` with text "发布")

**Content Structure**: `content/YYYY-MM-DD/` directory organizes posts by date. Each directory contains Markdown files and images.

## Key Implementation Details

### Editor Focus Strategy
The ProseMirror editor requires multiple focus attempts due to overlay interference:
```typescript
// 1. JS click + focus
editor.click(); editor.focus();
// 2. Playwright click with force
page.click('div.ProseMirror', { force: true });
// 3. Mouse coordinates
page.mouse.click(box.x + box.width/2, box.y + box.height/2);
```

### Cookie Persistence
Cookies alone are insufficient -今日头条 also requires localStorage tokens. Both are saved during login and restored when creating new browser contexts.

### Image Upload
Uses Playwright's `setInputFiles()` on `input[type="file"]` elements. First match (`first()`) typically resolves to the visible upload button's input.

## Platform Notes

- Target: 今日头条创作平台 (mp.toutiao.com)
- Editor: ProseMirror-based with `byte-drawer-mask` overlays
- Publish button: `<span>发布</span>` (not a `<button>`)
- Login URL: `https://mp.toutiao.com/auth/page/login/`
- Publish URL: `https://mp.toutiao.com/profile_v4/weitoutiao/publish`
