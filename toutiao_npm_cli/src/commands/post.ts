import { Command } from 'commander';
import * as path from 'path';
import * as fs from 'fs';
import { getBrowser } from '../lib/browser';
import { hasCookies } from '../lib/cookie';
import { parseMarkdown } from '../lib/md';

export const postCommand = new Command('post')
  .description('Post weibo or article');

postCommand
  .command('weibo')
  .description('Post a micro weibo')
  .option('-c, --content <text>', 'Content to post')
  .option('-f, --file <path>', 'Parse content from markdown file')
  .option('-i, --image <path>', 'Upload an image')
  .option('-d, --debug', 'Record user clicks to analyze click flow')
  .action(async (options) => {
    if (!hasCookies()) {
      console.error('Please run "login" command first to authenticate.');
      process.exit(1);
    }

    let content = '';
    if (options.file) {
      content = await parseMarkdown(options.file);
    } else if (options.content) {
      content = options.content;
    }

    // Debug 模式：监听用户点击
    if (options.debug) {
      console.log('=== DEBUG MODE: Click Recording ===');
      console.log('Browser will open. Click anywhere on the page.');
      console.log('After 2 minutes, click log will be saved.\n');

      const browser = await getBrowser(false);
      const cookieFile = path.join(process.cwd(), 'storage', 'cookies.json');

      const context = await browser.newContext();
      if (fs.existsSync(cookieFile)) {
        const cookies = JSON.parse(fs.readFileSync(cookieFile, 'utf-8'));
        await context.addCookies(cookies);
      }

      const page = await context.newPage();

      console.log('Opening micro weibo publish page...');
      await page.goto('https://mp.toutiao.com/profile_v4/weitoutiao/publish');
      await page.waitForTimeout(2000);

      // 在页面中注入点击监听器
      await page.evaluate(() => {
        (window as any).clickLog = [];

        document.addEventListener('click', (e) => {
          const target = e.target as HTMLElement;
          const clickEntry = {
            timestamp: Date.now(),
            x: e.clientX,
            y: e.clientY,
            tagName: target.tagName,
            className: target.className || '',
            id: target.id || '',
            textContent: target.textContent?.trim().substring(0, 80) || '',
            outerHTML: target.outerHTML.substring(0, 150)
          };
          (window as any).clickLog.push(clickEntry);

          // 同时打印到控制台
          console.log(`[CLICK] (${e.clientX}, ${e.clientY}) <${target.tagName}> class="${target.className}" text="${target.textContent?.trim().substring(0, 50)}"`);
        }, true);
      });

      console.log('Listening for clicks on page...');

      // 等待 2 分钟，让用户点击
      await page.waitForTimeout(120000);

      // 获取点击日志
      const clickLog = await page.evaluate(() => (window as any).clickLog || []);

      console.log('\n=== Click Log Summary ===');
      console.log(`Total clicks recorded: ${clickLog.length}`);
      for (let i = 0; i < clickLog.length; i++) {
        const c = clickLog[i];
        console.log(`\n[Click ${i + 1}] ${new Date(c.timestamp).toISOString()}`);
        console.log(`  Position: (${c.x}, ${c.y})`);
        console.log(`  Element: <${c.tagName}> class="${c.className}" id="${c.id}"`);
        console.log(`  Text: "${c.textContent}"`);
      }

      const logFile = path.join(process.cwd(), 'storage', 'click-log.json');
      fs.writeFileSync(logFile, JSON.stringify(clickLog, null, 2));
      console.log(`\nClick log saved to: ${logFile}`);

      await browser.close();
      return;
    }

    // 正常发布流程
    const { getPage, closeBrowser } = await import('../lib/browser');
    const page = await getPage();
    console.log('Navigating to micro weibo page...');
    await page.goto('https://mp.toutiao.com/profile_v4/weitoutiao/publish');

    // 等待页面完全加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 使用 JavaScript 直接操作 DOM 来关闭遮罩
    await page.evaluate(() => {
      const masks = document.querySelectorAll('div.byte-drawer-mask');
      masks.forEach(mask => {
        const event = new MouseEvent('click', { bubbles: true, cancelable: true });
        mask.dispatchEvent(event);
      });
    });
    await page.waitForTimeout(1000);

    // 使用多种方式确保编辑器获得焦点
    const focusEditor = async () => {
      // 方法1: 直接用 JavaScript 点击并聚焦
      await page.evaluate(() => {
        const editor = document.querySelector('div.ProseMirror');
        if (editor) {
          // 先点击
          (editor as HTMLElement).click();
          // 再聚焦
          (editor as HTMLElement).focus();
        }
      });
      await page.waitForTimeout(300);

      // 检查是否获得焦点
      let hasFocus = await page.evaluate(() => {
        const editor = document.querySelector('div.ProseMirror');
        return editor?.classList.contains('ProseMirror-focused');
      });

      if (!hasFocus) {
        // 方法2: 使用 page.click 通过 Playwright
        await page.click('div.ProseMirror', { force: true });
        await page.waitForTimeout(300);

        hasFocus = await page.evaluate(() => {
          const editor = document.querySelector('div.ProseMirror');
          return editor?.classList.contains('ProseMirror-focused');
        });
      }

      if (!hasFocus) {
        // 方法3: 使用 mouse.click 在编辑器中心点击
        const box = await page.locator('div.ProseMirror').boundingBox();
        if (box) {
          await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
          await page.waitForTimeout(300);
        }
      }

      return hasFocus;
    };

    const hasFocus = await focusEditor();
    console.log(`Editor has focus: ${hasFocus}`);

    // 清空可能存在的占位符文本
    await page.keyboard.press('ControlOrMeta+a');
    await page.waitForTimeout(100);
    await page.keyboard.press('Backspace');
    await page.waitForTimeout(200);

    // 输入内容
    console.log(`Typing content: ${content.substring(0, 50)}...`);
    await page.keyboard.type(content, { delay: 50 });
    await page.waitForTimeout(500);

    // 验证内容是否输入成功
    const editorText = await page.evaluate(() => {
      const editor = document.querySelector('div.ProseMirror');
      return editor?.textContent || '';
    });
    console.log(`Editor text length: ${editorText.length}`);

    if (options.image) {
      console.log('Uploading image...');

      // 等待图片按钮可见并点击
      await page.waitForSelector('button:has-text("图片")', { timeout: 5000 });
      await page.locator('button:has-text("图片")').click();
      await page.waitForTimeout(1000); // 等待上传对话框打开

      // 等待文件输入框出现
      await page.waitForSelector('input[type="file"]', { timeout: 5000 });
      await page.locator('input[type="file"]').first().setInputFiles(options.image);
      await page.waitForTimeout(2000); // 等待图片上传

      // 点击确定按钮
      await page.locator('button:has-text("确定")').click();
      await page.waitForTimeout(1000);
    }

    console.log('Publishing...');
    await page.waitForTimeout(500);

    // 使用 JavaScript 点击发布按钮
    await page.evaluate(() => {
      const buttons = document.querySelectorAll('span');
      for (const btn of buttons) {
        if (btn.textContent?.trim() === '发布') {
          (btn as HTMLElement).click();
          break;
        }
      }
    });

    console.log('发布按钮已点击，等待 10 秒确认...');
    await page.waitForTimeout(10000); // 等待 10 秒让发布完成

    // 检查是否有发布成功的提示
    const pageContent = await page.content();
    if (pageContent.includes('发布成功') || pageContent.includes('已发布')) {
      console.log('发布成功！');
    } else {
      console.log('发布可能已完成，请检查页面');
    }

    console.log('再等待 10 秒后关闭浏览器...');
    await page.waitForTimeout(10000); // 额外等待

    console.log('Post published successfully!');
    await closeBrowser();
  });

postCommand
  .command('article')
  .description('Post an article')
  .option('-c, --content <text>', 'Content to post')
  .option('-f, --file <path>', 'Parse content from markdown file')
  .action(async (options) => {
    const { closeBrowser } = await import('../lib/browser');
    console.log('Article posting not yet implemented.');
    await closeBrowser();
  });