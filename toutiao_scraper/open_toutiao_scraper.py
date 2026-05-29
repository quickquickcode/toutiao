#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class OpenToutiaoRecord:
    category: str
    group_id: str
    item_id: str
    card_type: str
    title: str
    source: str
    read_count: str
    publish_time: str
    scraped_at: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse saved open.toutiao.com HTML and extract one category feed."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("web/open.toutiao.com.html"),
        help="Saved open.toutiao.com HTML file.",
    )
    parser.add_argument(
        "--category",
        default="科技",
        help="Category name to extract from the saved page.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/open_toutiao_tech.jsonl"),
        help="Append-only JSONL output path.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_jsonl_line(path: Path, payload: dict) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def parse_saved_html(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def find_category_index(soup: BeautifulSoup, category: str) -> int:
    tabs = soup.select(".fx-tab-cell")
    for index, tab in enumerate(tabs):
        if tab.get_text(strip=True) == category:
            return index
    raise ValueError(f"category not found: {category}")


def pane_for_category(soup: BeautifulSoup, category: str) -> BeautifulSoup:
    panes = soup.select(".fx-tab-pane")
    category_index = find_category_index(soup, category)
    if category_index >= len(panes):
        raise ValueError(
            f"pane index out of range for category {category}: {category_index} >= {len(panes)}"
        )
    return panes[category_index]


def text_or_empty(node: Optional[BeautifulSoup]) -> str:
    return node.get_text(strip=True) if node else ""


def extract_card_type(card) -> str:
    for candidate in ("text-card", "small-img-card", "large-img-card"):
        if card.select_one(f".{candidate}"):
            return candidate
    return "unknown"


def extract_item_id(card) -> str:
    item_node = card.select_one("[data-id]")
    return item_node.get("data-id", "") if item_node else ""


def extract_info_spans(card) -> tuple[str, str]:
    spans = [span.get_text(strip=True) for span in card.select(".info-panel > span")]
    if len(spans) >= 2:
        return spans[0], spans[1]
    if len(spans) == 1:
        return spans[0], ""
    return "", ""


def extract_records(soup: BeautifulSoup, category: str) -> list[OpenToutiaoRecord]:
    pane = pane_for_category(soup, category)
    records: list[OpenToutiaoRecord] = []
    for card in pane.select(".fx-feed-card-wrapper"):
        title = text_or_empty(card.select_one(".title"))
        if not title:
            continue
        read_count, publish_time = extract_info_spans(card)
        record = OpenToutiaoRecord(
            category=category,
            group_id=card.get("data-group-id", ""),
            item_id=extract_item_id(card),
            card_type=extract_card_type(card),
            title=title,
            source=text_or_empty(card.select_one(".info-panel__source span")),
            read_count=read_count,
            publish_time=publish_time,
            scraped_at=now_iso(),
        )
        records.append(record)
    return records


def main() -> None:
    args = parse_args()
    soup = parse_saved_html(args.input)
    records = extract_records(soup, args.category)
    if not records:
        raise SystemExit(f"no records found for category: {args.category}")
    for record in records:
        write_jsonl_line(args.output, asdict(record))


if __name__ == "__main__":
    main()
