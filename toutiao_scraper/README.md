# Toutiao Tech Scraper

Playwright-based Python scraper for Toutiao's tech channel. It collects the latest tech articles and writes one JSON object per line.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Run

```bash
python3 scraper.py --limit 100 --output data/tech_articles.jsonl --headless true
/usr/bin/python3 scraper.py --limit 100 --output data/tech_articles.jsonl --headless true
```

Useful flags:

- `--limit 100`: target article count.
- `--output data/tech_articles.jsonl`: success output file.
- `--headless false`: watch the browser while debugging.
- `--timeout 30000`: per-page timeout in milliseconds.
- `--state-file data/tech_articles.state.json`: cross-run dedupe state file.
- `--rebuild-state`: rebuild state from the existing output file before crawling.
- `--dedupe-existing true`: remove historical duplicates in the output file before crawling.

## Output

Successful records are written to `data/tech_articles.jsonl` with these fields:

- `group_id`
- `article_url`
- `title`
- `comment_count`
- `content`
- `publish_time`
- `scraped_at`

Failures are written to `data/tech_articles.errors.jsonl` with the article id, URL, error type, and message.

Both files are append-only. Re-running the scraper adds new lines to the end instead of overwriting existing data.

## Notes

- The scraper uses Playwright to drive the browser, but reads feed metadata from network responses for more stable `comment_count` extraction.
- It runs anonymously. Login prompts, captchas, or empty content pages are recorded as failures and skipped.
- Successful records are deduplicated across runs by `group_id`. The crawler skips already-seen articles and keeps scrolling deeper to find new ones.
- If the output file already contains duplicates from older runs, the scraper can clean them before crawling and rebuild its state file.

## Open Toutiao Saved HTML

If you saved `https://open.toutiao.com/` locally as `web/open.toutiao.com.html`, you can extract the active category feed from the saved file without Playwright:

```bash
python3 open_toutiao_scraper.py --category 科技 --input web/open.toutiao.com.html --output data/open_toutiao_tech.jsonl
```

This parser appends one JSON object per card with:

- `category`
- `group_id`
- `item_id`
- `card_type`
- `title`
- `source`
- `read_count`
- `publish_time`
- `scraped_at`
