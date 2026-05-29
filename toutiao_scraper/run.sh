#!/bin/zsh

while true; do
  /usr/bin/python3 /Users/hqb/project/2026/agent/toutiao/toutiao_scraper/scraper.py --limit 100 --output /Users/hqb/project/2026/agent/toutiao/toutiao_scraper/data/tech_articles.jsonl --headless true
  sleep 360
done
