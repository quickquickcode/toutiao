import { Command } from 'commander';
import { chromium, BrowserContext } from 'playwright';
import * as path from 'path';
import * as fs from 'fs';

const STORAGE_DIR = path.join(process.cwd(), 'storage');

function ensureStorageDir(): void {
  if (!fs.existsSync(STORAGE_DIR)) {
    fs.mkdirSync(STORAGE_DIR, { recursive: true });
  }
}

export const loginCommand = new Command('login')
  .description('Open browser for manual login and save session')
  .action(async () => {
    ensureStorageDir();

    console.log('Opening login page...');
    console.log('请手动登录，登录成功后窗口会自动关闭。');

    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    // 打开登录页
    await page.goto('https://mp.toutiao.com/auth/page/login/');

    console.log('等待登录中...');

    try {
      // 轮询检查 URL 变化，等待跳转到创作者中心
      const isLoggedIn = await page.waitForFunction(() => {
        const url = window.location.href;
        return (
          url.includes('mp.toutiao.com/profile') ||
          url.includes('creator.toutiao.com') ||
          url.includes('mp.toutiao.com/dashboard') ||
          url.includes('mp.toutiao.com/profile_v4')
        );
      }, { timeout: 0 }); // 无限等待

      console.log('检测到登录成功，正在保存会话...');

      // 额外等待确保页面完全加载
      await page.waitForTimeout(2000);

      // 保存 cookies
      const cookies = await context.cookies();
      fs.writeFileSync(path.join(STORAGE_DIR, 'cookies.json'), JSON.stringify(cookies, null, 2));

      // 保存 localStorage 和 sessionStorage
      const storageData = await page.evaluate(() => {
        return {
          localStorage: { ...window.localStorage },
          sessionStorage: { ...window.sessionStorage }
        };
      });
      fs.writeFileSync(path.join(STORAGE_DIR, 'storage.json'), JSON.stringify(storageData, null, 2));

      console.log('会话已保存到 storage/ 目录');
      console.log('- cookies.json');
      console.log('- storage.json');

    } catch (error) {
      console.error('登录超时或失败:', error);
      await browser.close();
      process.exit(1);
    }

    await browser.close();
    console.log('登录完成！');
  });