import { Command } from 'commander';
import * as path from 'path';
import * as fs from 'fs';
import { getBrowser } from '../lib/browser';
import { hasCookies } from '../lib/cookie';

const DATA_DIR = path.join(process.cwd(), 'data', 'toutiao');

interface ToutiaoArticle {
  title: string;
  url: string;
  content: string;
  author: string;
  publishDate: string;
  stats: {
    likes: number;
    comments: number;
    shares: number;
  };
  keyword: string;
  crawledAt: string;
}

interface CrawlIndex {
  keywords: string[];
  totalCount: number;
  lastCrawl: string;
  articles: Array<{
    title: string;
    url: string;
    stats: { likes: number; comments: number };
    file: string;
    keyword: string;
  }>;
}

function ensureDataDir(): void {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
}

function sanitizeFilename(str: string): string {
  return str.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, '_').substring(0, 50);
}

export const crawlCommand = new Command('crawl')
  .description('Crawl articles from Toutiao (科技/AI类高赞文章)')
  .option('-k, --keywords <keywords>', '搜索关键词', 'AI人工智能,大模型,ChatGPT,科技资讯,机器人')
  .option('-l, --limit <number>', '每个关键词爬取文章数', '50')
  .action(async (options) => {
    const keywords = options.keywords.split(',').map((k: string) => k.trim());
    const limit = parseInt(options.limit, 10);

    console.log('=== 今日头条文章爬虫 ===');
    console.log(`关键词: ${keywords.join(', ')}`);
    console.log(`每关键词数量: ${limit}`);
    console.log('');

    if (!hasCookies()) {
      console.log('⚠️  未检测到登录会话，将以游客模式爬取（数量有限）');
      console.log('   建议先运行 "npm run login" 登录以获取更多内容');
      console.log('');
    }

    ensureDataDir();

    const browser = await getBrowser(true);
    const context = await browser.newContext();
    const page = await context.newPage();

    const allArticles: ToutiaoArticle[] = [];
    const indexArticles: CrawlIndex['articles'] = [];

    for (const keyword of keywords) {
      console.log(`\n🔍 搜索关键词: ${keyword}`);

      const keywordDir = path.join(DATA_DIR, keyword);
      if (!fs.existsSync(keywordDir)) {
        fs.mkdirSync(keywordDir, { recursive: true });
      }

      try {
        // 访问今日头条搜索页面
        const searchUrl = `https://so.toutiao.com/search?keyword=${encodeURIComponent(keyword)}&source=input&pd=article`;

        await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(5000); // 等待动态内容加载

        // 滚动页面加载更多内容
        for (let scroll = 0; scroll < 3; scroll++) {
          await page.evaluate(() => window.scrollBy(0, 1000));
          await page.waitForTimeout(1500);
        }

        // 提取文章列表
        const articleLinks = await page.evaluate(() => {
          const links: Array<{ url: string; title: string }> = [];
          const seenUrls = new Set<string>();

          // 尝试多种选择器
          const selectors = [
            'a[href*="/article/"]',
            '.article-item',
            '.news-item',
            '.result-item',
            '[class*="article"] a',
            '[class*="news"] a'
          ];

          selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
              let href = el.getAttribute('href');
              let title = el.textContent?.trim() || '';

              // 补全相对链接
              if (href && !href.startsWith('http')) {
                href = 'https://www.toutiao.com' + href;
              }

              if (href && href.includes('toutiao.com') && !seenUrls.has(href) && title.length > 5) {
                seenUrls.add(href);
                links.push({ url: href, title });
              }
            });
          });

          return links;
        });

        console.log(`   找到 ${articleLinks.length} 篇文章`);

        // 爬取每篇文章详情
        for (let i = 0; i < Math.min(articleLinks.length, limit); i++) {
          const link = articleLinks[i];

          try {
            console.log(`   [${i + 1}/${Math.min(articleLinks.length, limit)}] 爬取: ${link.title.substring(0, 30)}...`);

            await page.goto(link.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
            await page.waitForTimeout(3000);

            // 提取文章内容
            const articleData = await page.evaluate(() => {
              // 标题
              const title = document.querySelector('h1')?.textContent?.trim() ||
                           document.querySelector('.article-title')?.textContent?.trim() ||
                           document.querySelector('[class*="title"]')?.textContent?.trim() || '';

              // 内容
              const contentEl = document.querySelector('.article-content') ||
                               document.querySelector('[class*="content"]') ||
                               document.querySelector('#J_article') ||
                               document.querySelector('article');
              let content = contentEl?.textContent?.trim() || '';

              // 作者
              const author = document.querySelector('.author-name')?.textContent?.trim() ||
                            document.querySelector('[class*="author"]')?.textContent?.trim() ||
                            document.querySelector('.name')?.textContent?.trim() || '未知';

              // 发布日期
              const date = document.querySelector('.publish-time')?.textContent?.trim() ||
                          document.querySelector('[class*="time"]')?.textContent?.trim() ||
                          document.querySelector('time')?.textContent?.trim() || '';

              // 互动数据
              const likesEl = document.querySelector('.like-count')?.textContent?.trim() ||
                            document.querySelector('[class*="like"]')?.textContent?.trim() ||
                            document.querySelector('[class*="digg"]')?.textContent?.trim();
              const likes = parseInt(likesEl?.replace(/[^0-9]/g, '') || '0', 10);

              const commentsEl = document.querySelector('.comment-count')?.textContent?.trim() ||
                               document.querySelector('[class*="comment"]')?.textContent?.trim();
              const comments = parseInt(commentsEl?.replace(/[^0-9]/g, '') || '0', 10);

              return { title, content: content.substring(0, 5000), author, date, likes, comments };
            });

            if (articleData.content.length < 50) {
              console.log(`      ⚠️  内容过短，跳过`);
              continue;
            }

            const timestamp = Date.now();
            const filename = `${timestamp}_${sanitizeFilename(articleData.title || 'untitled')}.json`;

            const article: ToutiaoArticle = {
              title: articleData.title || link.title,
              url: link.url,
              content: articleData.content,
              author: articleData.author,
              publishDate: articleData.date,
              stats: {
                likes: articleData.likes || 0,
                comments: articleData.comments || 0,
                shares: 0
              },
              keyword: keyword,
              crawledAt: new Date().toISOString()
            };

            fs.writeFileSync(
              path.join(keywordDir, filename),
              JSON.stringify(article, null, 2),
              'utf-8'
            );

            allArticles.push(article);
            indexArticles.push({
              title: article.title,
              url: article.url,
              stats: { likes: article.stats.likes, comments: article.stats.comments },
              file: `${keyword}/${filename}`,
              keyword: keyword
            });

            // 礼貌性延迟
            await page.waitForTimeout(1500);

          } catch (err) {
            console.log(`      ❌ 错误: ${err}`);
          }
        }

      } catch (err) {
        console.log(`   ❌ 搜索失败: ${err}`);
      }
    }

    // 保存索引
    const index: CrawlIndex = {
      keywords: keywords,
      totalCount: allArticles.length,
      lastCrawl: new Date().toISOString(),
      articles: indexArticles
    };

    fs.writeFileSync(
      path.join(DATA_DIR, 'index.json'),
      JSON.stringify(index, null, 2),
      'utf-8'
    );

    console.log('\n=== 爬取完成 ===');
    console.log(`总文章数: ${allArticles.length}`);
    console.log(`数据目录: ${DATA_DIR}`);
    console.log('');
    console.log('下一步: 运行 "npm run analyze" 分析文章风格');

    await context.close();
  });
