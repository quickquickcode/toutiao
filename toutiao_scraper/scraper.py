#!/usr/bin/env python3
import argparse
import asyncio
import json
import random
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright


TECH_CHANNEL_URL = "https://www.toutiao.com/ch/news_tech/"
FEED_API_KEYWORD = "/api/pc/list/feed"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
CONTENT_SELECTORS = [
    "article",
    ".tt-article-content",
    ".article-content",
    "[data-testid='article']",
    ".content",
    ".a-con",
    ".tt-post-content",
    ".tt-article-body",
    ".article-body",
]
SKIP_CONTENT_PATTERNS = [
    re.compile(r"^\s*责任编辑[:：]"),
    re.compile(r"^\s*来源[:：]"),
    re.compile(r"^\s*举报/反馈\s*$"),
    re.compile(r"^\s*打开今日头条查看更多图片\s*$"),
]


@dataclass
class ArticleRecord:
    group_id: str
    article_url: str
    title: str
    comment_count: int
    content: str
    publish_time: Optional[str]
    scraped_at: str


@dataclass
class ErrorRecord:
    group_id: str
    article_url: str
    error_type: str
    error_message: str
    failed_at: str


@dataclass
class CrawlState:
    seen_group_ids: list[str]
    last_run_at: str
    oldest_publish_time: Optional[int]


def log(message: str) -> None:
    print(message, flush=True)


def render_progress(current: int, total: int, width: int = 24) -> str:
    if total <= 0:
        return "[unknown]"
    ratio = min(max(current / total, 0), 1)
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {current}/{total}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Toutiao tech articles with Playwright."
    )
    parser.add_argument("--limit", type=int, default=100, help="Number of articles to scrape.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/tech_articles.jsonl"),
        help="Output JSONL path.",
    )
    parser.add_argument(
        "--headless",
        type=parse_bool,
        default=True,
        help="Run browser in headless mode. Accepts true/false.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Timeout in milliseconds for page operations.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path("data/tech_articles.state.json"),
        help="State file for cross-run dedupe and resume metadata.",
    )
    parser.add_argument(
        "--rebuild-state",
        action="store_true",
        help="Rebuild the state file from the existing output file before crawling.",
    )
    parser.add_argument(
        "--dedupe-existing",
        type=parse_bool,
        default=True,
        help="Deduplicate the existing output file by group_id before crawling.",
    )
    return parser.parse_args()


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_jsonl_line(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append(payload)
    return records


def rewrite_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def normalize_publish_time(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, (int, float)):
        return int(raw)
    if isinstance(raw, str) and raw.strip():
        digits = re.sub(r"[^\d]", "", raw)
        return int(digits) if digits else None
    return None


def dedupe_output_file(path: Path) -> tuple[int, int]:
    records = read_jsonl_records(path)
    if not records:
        return 0, 0
    deduped: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    fallback_index = 0
    for record in records:
        group_id = str(record.get("group_id") or f"__missing__{fallback_index}")
        fallback_index += 1
        if group_id not in deduped:
            ordered_ids.append(group_id)
        deduped[group_id] = record
    unique_records = [deduped[group_id] for group_id in ordered_ids]
    removed = len(records) - len(unique_records)
    if removed > 0:
        rewrite_jsonl(path, unique_records)
    return len(unique_records), removed


def build_state_from_output(output_path: Path) -> CrawlState:
    records = read_jsonl_records(output_path)
    seen_group_ids: list[str] = []
    seen_set: set[str] = set()
    oldest_publish_time: Optional[int] = None
    for record in records:
        group_id = str(record.get("group_id") or "")
        if group_id and group_id not in seen_set:
            seen_set.add(group_id)
            seen_group_ids.append(group_id)
        publish_time = normalize_publish_time(record.get("publish_time"))
        if publish_time is not None:
            if oldest_publish_time is None or publish_time < oldest_publish_time:
                oldest_publish_time = publish_time
    return CrawlState(
        seen_group_ids=seen_group_ids,
        last_run_at=now_iso(),
        oldest_publish_time=oldest_publish_time,
    )


def merge_states(base: Optional[CrawlState], fresh: CrawlState) -> CrawlState:
    base_ids = base.seen_group_ids if base else []
    merged_ids: list[str] = []
    merged_set: set[str] = set()
    for group_id in list(base_ids) + list(fresh.seen_group_ids):
        if group_id and group_id not in merged_set:
            merged_set.add(group_id)
            merged_ids.append(group_id)

    oldest_publish_time = fresh.oldest_publish_time
    if base and base.oldest_publish_time is not None:
        if oldest_publish_time is None or base.oldest_publish_time < oldest_publish_time:
            oldest_publish_time = base.oldest_publish_time

    return CrawlState(
        seen_group_ids=merged_ids,
        last_run_at=now_iso(),
        oldest_publish_time=oldest_publish_time,
    )


def load_state(state_path: Path) -> Optional[CrawlState]:
    if not state_path.exists():
        return None
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    seen_group_ids = payload.get("seen_group_ids") or []
    if not isinstance(seen_group_ids, list):
        seen_group_ids = []
    return CrawlState(
        seen_group_ids=[str(item) for item in seen_group_ids if item],
        last_run_at=str(payload.get("last_run_at") or now_iso()),
        oldest_publish_time=normalize_publish_time(payload.get("oldest_publish_time")),
    )


def save_state(path: Path, state: CrawlState) -> None:
    ensure_parent(path)
    path.write_text(
        json.dumps(asdict(state), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def normalize_whitespace(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    filtered: list[str] = []
    for line in lines:
        if not line:
            continue
        if any(pattern.search(line) for pattern in SKIP_CONTENT_PATTERNS):
            continue
        filtered.append(line)
    return "\n".join(filtered)


def parse_comment_count(raw: Any) -> int:
    if raw is None:
        return 0
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, (int, float)):
        return int(raw)
    if isinstance(raw, str):
        digits = re.sub(r"[^\d]", "", raw)
        return int(digits) if digits else 0
    return 0


def clean_title(raw: str) -> str:
    text = raw.replace("展开", "").strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_article_url(item: dict[str, Any]) -> Optional[str]:
    candidates = [
        item.get("article_url"),
        item.get("url"),
        item.get("share_url"),
        item.get("display_url"),
        item.get("source_url"),
    ]
    group_id = extract_group_id(item)
    if group_id:
        candidates.append(f"https://www.toutiao.com/article/{group_id}/")
    for candidate in candidates:
        if isinstance(candidate, str) and "/article/" in candidate:
            if candidate.startswith("//"):
                return "https:" + candidate
            if candidate.startswith("/"):
                return "https://www.toutiao.com" + candidate
            return candidate
    return None


def extract_group_id(item: dict[str, Any]) -> Optional[str]:
    for key in ("group_id", "gid", "item_id", "id"):
        value = item.get(key)
        if value is not None:
            return str(value)
    return None


def looks_like_article(item: dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False
    if not extract_group_id(item):
        return False
    if item.get("has_video") or item.get("video_id") or item.get("video_duration"):
        return False
    title = item.get("title")
    if not isinstance(title, str) or not title.strip():
        return False
    url = extract_article_url(item)
    return bool(url)


def iter_feed_items(payload: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for entry in payload:
            if isinstance(entry, dict):
                items.extend(iter_feed_items(entry))
        return items
    if not isinstance(payload, dict):
        return items
    for key in ("data", "list", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, str):
                    try:
                        decoded = json.loads(entry)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(decoded, dict):
                        items.append(decoded)
                elif isinstance(entry, dict):
                    items.append(entry)
    return items


def build_record(item: dict[str, Any]) -> ArticleRecord:
    group_id = extract_group_id(item)
    article_url = extract_article_url(item)
    if not group_id or not article_url:
        raise ValueError("feed item missing group_id or article_url")
    return ArticleRecord(
        group_id=group_id,
        article_url=article_url,
        title=clean_title(str(item.get("title", "")).strip()),
        comment_count=parse_comment_count(item.get("comment_count")),
        content="",
        publish_time=str(item.get("publish_time")) if item.get("publish_time") is not None else None,
        scraped_at=now_iso(),
    )


async def dismiss_popups(page: Page) -> None:
    selectors = [
        "button[aria-label='关闭弹窗']",
        ".ttp-modal-close-btn",
        "text=暂不登录",
        "text=以后再说",
        "text=关闭",
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            await locator.wait_for(state="visible", timeout=500)
            await locator.click()
            await page.wait_for_timeout(300)
        except Exception:
            continue


async def harden_feed_page(page: Page) -> None:
    # Some feed cards trigger repeated window.open calls while scrolling into view.
    # Block only article/group popup targets and return a fake window object so the
    # page logic still thinks the call succeeded.
    await page.add_init_script(
        """
        (() => {
          const shouldBlockUrl = (value) => {
            const href = String(value || '');
            return href.includes('/article/') || href.includes('/group/');
          };

          const fakeWindow = {
            closed: false,
            close() { this.closed = true; },
            focus() {},
            blur() {},
            postMessage() {},
            location: { href: '' },
            opener: null,
            parent: null,
            top: null,
          };

          const originalOpen = window.open.bind(window);
          window.open = function(url, ...rest) {
            if (shouldBlockUrl(url)) {
              fakeWindow.location.href = String(url || '');
              return fakeWindow;
            }
            return originalOpen(url, ...rest);
          };

          try {
            document.documentElement.style.scrollBehavior = 'auto';
          } catch (e) {}
        })();
        """
    )


async def get_scroll_y(page: Page) -> int:
    return await page.evaluate("() => Math.floor(window.scrollY || window.pageYOffset || 0)")


async def scroll_feed_page(page: Page, delta_y: int) -> int:
    return await page.evaluate(
        """(delta) => {
        window.scrollBy(0, delta);
        return Math.floor(window.scrollY || window.pageYOffset || 0);
    }""",
        delta_y,
    )


async def collect_feed_records(
    page: Page,
    limit: int,
    timeout_ms: int,
    seen_group_ids: set[str],
) -> tuple[list[ArticleRecord], Optional[int]]:
    seen_ids: set[str] = set()
    records: list[ArticleRecord] = []
    pending_tasks: set[asyncio.Task[Any]] = set()
    oldest_publish_time: Optional[int] = None
    popup_tasks: set[asyncio.Task[Any]] = set()

    async def capture_response(response) -> None:
        nonlocal oldest_publish_time
        if FEED_API_KEYWORD not in response.url:
            return
        try:
            payload = await response.json()
        except Exception:
            return
        for item in iter_feed_items(payload):
            if not looks_like_article(item):
                continue
            group_id = extract_group_id(item)
            if not group_id or group_id in seen_ids or group_id in seen_group_ids:
                continue
            try:
                record = build_record(item)
            except ValueError:
                continue
            seen_ids.add(group_id)
            records.append(record)
            publish_time = normalize_publish_time(item.get("publish_time"))
            if publish_time is not None:
                if oldest_publish_time is None or publish_time < oldest_publish_time:
                    oldest_publish_time = publish_time
            if len(records) <= 5 or len(records) % 10 == 0 or len(records) == limit:
                log(
                    f"[feed] collected {len(records)}/{limit}: "
                    f"{record.title[:48]}"
                )

    def on_response(response) -> None:
        task = asyncio.create_task(capture_response(response))
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)

    def on_popup(popup_page: Page) -> None:
        async def close_popup() -> None:
            try:
                log(f"[feed] blocked popup: {popup_page.url}")
                await popup_page.close()
            except Exception:
                pass

        task = asyncio.create_task(close_popup())
        popup_tasks.add(task)
        task.add_done_callback(popup_tasks.discard)

    await harden_feed_page(page)
    page.on("response", on_response)
    page.on("popup", on_popup)
    log(f"[feed] opening tech channel: {TECH_CHANNEL_URL}")
    await page.goto(TECH_CHANNEL_URL, wait_until="domcontentloaded", timeout=timeout_ms)
    await dismiss_popups(page)

    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightTimeoutError:
        pass

    scroll_attempts = 0
    stagnant_rounds = 0
    previous_count = 0
    max_scroll_attempts = 200
    max_stagnant_rounds = 25
    max_scroll_y = await get_scroll_y(page)

    while len(records) < limit and scroll_attempts < max_scroll_attempts and stagnant_rounds < max_stagnant_rounds:
        delta_y = random.randint(1400, 2200)
        current_scroll_y = await scroll_feed_page(page, delta_y)
        if current_scroll_y > max_scroll_y:
            max_scroll_y = current_scroll_y
        await page.wait_for_timeout(random.randint(1200, 2200))
        await dismiss_popups(page)
        current_scroll_y = await get_scroll_y(page)
        if current_scroll_y + 300 < max_scroll_y:
            await page.evaluate(
                "(targetY) => window.scrollTo(0, targetY)",
                max_scroll_y,
            )
            current_scroll_y = await get_scroll_y(page)
            log(
                f"[feed] restored scroll position from jump, "
                f"current={current_scroll_y} max={max_scroll_y}"
            )
        scroll_attempts += 1
        current_count = len(records)
        if current_count == previous_count:
            stagnant_rounds += 1
        else:
            stagnant_rounds = 0
            previous_count = current_count
        if scroll_attempts <= 3 or scroll_attempts % 5 == 0:
            log(
                f"[feed] scroll {scroll_attempts}, "
                f"records={len(records)}, stagnant={stagnant_rounds}, "
                f"scrollY={current_scroll_y}"
            )

    if pending_tasks:
        await asyncio.gather(*pending_tasks, return_exceptions=True)
    if popup_tasks:
        await asyncio.gather(*popup_tasks, return_exceptions=True)
    page.remove_listener("response", on_response)
    page.remove_listener("popup", on_popup)
    log(f"[feed] finished with {len(records)} records")
    return records[:limit], oldest_publish_time


async def extract_title(page: Page) -> str:
    selectors = [
        "h1",
        ".article-title",
        "[data-testid='article-title']",
        ".tt-article-title",
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            text = clean_title((await locator.inner_text(timeout=1500)).strip())
            if text:
                return text
        except Exception:
            continue
    return ""


async def is_video_detail(page: Page) -> bool:
    locator = page.locator("script[type='application/ld+json']")
    try:
        texts = await locator.all_inner_texts()
    except Exception:
        return False
    return any("VideoObject" in text for text in texts)


async def extract_content(page: Page) -> str:
    for selector in CONTENT_SELECTORS:
        locator = page.locator(selector).first
        try:
            text = await locator.inner_text(timeout=2000)
        except Exception:
            continue
        normalized = normalize_whitespace(text)
        if len(normalized) >= 80:
            return normalized

    paragraphs = page.locator("article p, .article-content p, .tt-article-content p")
    try:
        texts = await paragraphs.all_inner_texts()
    except Exception:
        texts = []
    normalized = normalize_whitespace("\n".join(texts))
    return normalized


async def enrich_record(context: BrowserContext, record: ArticleRecord, timeout_ms: int) -> ArticleRecord:
    page = await context.new_page()
    try:
        await page.goto(record.article_url, wait_until="domcontentloaded", timeout=timeout_ms)
        await dismiss_popups(page)
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass

        if await is_video_detail(page):
            raise ValueError("video detail page")

        title = await extract_title(page)
        content = await extract_content(page)
        if not content:
            raise ValueError("empty article content")

        record.title = title or record.title
        record.content = content
        record.scraped_at = now_iso()
        return record
    finally:
        await page.close()


async def run(args: argparse.Namespace) -> None:
    error_path = args.output.with_suffix(".errors.jsonl")
    if args.dedupe_existing:
        unique_count, removed_count = dedupe_output_file(args.output)
        if args.output.exists():
            log(
                f"[dedupe] output unique={unique_count} removed={removed_count}"
            )

    output_state = build_state_from_output(args.output)
    if args.rebuild_state:
        state = output_state
        log(
            f"[state] rebuilt from output: seen={len(state.seen_group_ids)} "
            f"oldest_publish_time={state.oldest_publish_time}"
        )
    else:
        file_state = load_state(args.state_file)
        state = merge_states(file_state, output_state)
        if file_state is None:
            log(
                f"[state] initialized from output: seen={len(state.seen_group_ids)} "
                f"oldest_publish_time={state.oldest_publish_time}"
            )
        else:
            log(
                f"[state] merged file+output: seen={len(state.seen_group_ids)} "
                f"oldest_publish_time={state.oldest_publish_time}"
            )
    save_state(args.state_file, state)

    seen_group_ids = set(state.seen_group_ids)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=args.headless)
        context = await browser.new_context(user_agent=USER_AGENT, locale="zh-CN")
        page = await context.new_page()

        try:
            log(
                f"[start] limit={args.limit} output={args.output} "
                f"headless={args.headless} timeout={args.timeout}"
            )
            feed_records, oldest_publish_time = await collect_feed_records(
                page,
                args.limit,
                args.timeout,
                seen_group_ids,
            )
            if not feed_records:
                log("[done] no new articles found")
                state.last_run_at = now_iso()
                save_state(args.state_file, state)
                return
            log(f"[detail] starting detail crawl for {len(feed_records)} articles")

            success_count = 0
            error_count = 0
            attempted_group_ids: set[str] = set()
            for index, record in enumerate(feed_records, start=1):
                if record.group_id in attempted_group_ids:
                    log(f"[detail] skipped duplicate in current run: {record.group_id}")
                    continue
                attempted_group_ids.add(record.group_id)
                prefix = render_progress(index, len(feed_records))
                log(f"{prefix} fetching: {record.title[:60]}")
                try:
                    enriched = await enrich_record(context, record, args.timeout)
                    write_jsonl_line(args.output, asdict(enriched))
                    success_count += 1
                    seen_group_ids.add(enriched.group_id)
                    state.seen_group_ids = sorted(seen_group_ids)
                    state.last_run_at = now_iso()
                    save_state(args.state_file, state)
                    log(
                        f"{prefix} ok "
                        f"(success={success_count}, failed={error_count}, "
                        f"content_len={len(enriched.content)})"
                    )
                except Exception as exc:
                    error = ErrorRecord(
                        group_id=record.group_id,
                        article_url=record.article_url,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                        failed_at=now_iso(),
                    )
                    write_jsonl_line(error_path, asdict(error))
                    error_count += 1
                    log(
                        f"{prefix} failed "
                        f"(success={success_count}, failed={error_count}) "
                        f"{type(exc).__name__}: {exc}"
                    )
                if index < len(feed_records):
                    await page.wait_for_timeout(random.randint(800, 1800))
            state.seen_group_ids = sorted(seen_group_ids)
            state.last_run_at = now_iso()
            if oldest_publish_time is not None:
                if (
                    state.oldest_publish_time is None
                    or oldest_publish_time < state.oldest_publish_time
                ):
                    state.oldest_publish_time = oldest_publish_time
            save_state(args.state_file, state)
            log(
                f"[done] total={len(feed_records)} "
                f"success={success_count} failed={error_count}"
            )
        finally:
            await context.close()
            await browser.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
