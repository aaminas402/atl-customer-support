# scripts/scrape_docs_depth_limited.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from pathlib import Path

# Base URLs to crawl with output folders
START_URLS = {
    "https://docs.atlan.com/": "data/raw/atlan_docs",
    "https://developer.atlan.com/": "data/raw/atlan_sdk"
}

visited = set()
MAX_DEPTH = 2  # limit recursion depth

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def save_page(content, url, out_dir):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    filename = urlparse(url).path.strip("/")
    if not filename:
        filename = "index"
    filename = filename.replace("/", "_") + ".html"
    filepath = Path(out_dir) / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {url} -> {filepath}")

def crawl(url, base_domain, out_dir, depth=0):
    if depth > MAX_DEPTH:
        return
    url, _ = urldefrag(url)  # remove #fragments
    if url in visited:
        return
    visited.add(url)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return
    except Exception as e:
        print(f"Failed {url}: {e}")
        return

    save_page(response.text, url, out_dir)

    soup = BeautifulSoup(response.text, "html.parser")
    for link in soup.find_all("a", href=True):
        new_url = urljoin(url, link["href"])
        if is_valid_url(new_url) and base_domain in new_url:
            crawl(new_url, base_domain, out_dir, depth + 1)

def main():
    for start_url, out_dir in START_URLS.items():
        domain = urlparse(start_url).netloc
        print(f"\nCrawling {start_url} up to depth {MAX_DEPTH} ...\n")
        crawl(start_url, domain, out_dir)

if __name__ == "__main__":
    main()

