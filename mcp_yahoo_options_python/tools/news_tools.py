from __future__ import annotations

import logging
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

def _scrape_yahoo_quote_section(
    symbol: str,
    section: str,  # "news" or "press-releases"
    count: int,
) -> List[Dict]:
    """
    Scrape a Yahoo Finance quote section (news or press-releases).

    Uses:
      <div data-testid="news-stream">
        <ul class="stream-items">
          <li class="stream-item story-item">
            <div class="content">
              <a class="subtle-link">...</a>
              <div class="footer">
                <div class="publishing yf-m1e6lz">
                    ACCESS Newswire 
                    <i aria-hidden="true">•</i> 
                    7h ago
                </div>
              </div>
            </div>
          </li>
        </ul>
      </div>
    """
    symbol = symbol.upper()
    if section not in {"news", "press-releases"}:
        raise ValueError("section must be 'news' or 'press-releases'")

    url = f"https://finance.yahoo.com/quote/{symbol}/{section}/"
    logger.info("Scraping Yahoo Finance %s page for %s", section, symbol)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "OptionsNewsMCP/0.1"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        resp = httpx.get(
            url,
            headers=headers,
            timeout=10.0,
            follow_redirects=True,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.exception("Failed to fetch Yahoo Finance %s page", section)
        raise RuntimeError(
            f"Failed to fetch Yahoo Finance {section} page: {e}"
        )

    soup = BeautifulSoup(resp.text, "html.parser")
    items: List[Dict] = []

    # 1) Find the news stream container
    news_stream_div = soup.select_one('[data-testid="news-stream"]')
    if not news_stream_div:
        logger.warning("No [data-testid=news-stream] found for %s %s", symbol, section)
        return items  # empty list

    # 2) Inside it, find the <ul class="stream-items">
    ul = news_stream_div.find("ul", class_="stream-items")
    if not ul:
        logger.warning("No <ul class='stream-items'> found in news-stream for %s", symbol)
        return items

    # 3) Each <li> is a story: class contains both 'stream-item' and 'story-item'
    li_nodes = ul.select("li.stream-item.story-item")  # read a few extra

    for li in li_nodes:
        li_classes = li.get("class", []) # type: ignore
        if "story-item" not in li_classes: # type: ignore
            # skip non-story list items
            continue

        # div.content
        content_div = li.find("div", class_="content")
        if not content_div:
            continue

        # a.subtle-link is the link/title
        link_a = content_div.find("a", class_="subtle-link")
        if not link_a:
            continue

        title = link_a.get_text(strip=True)
        if not title:
            continue

        href = link_a.get("href") or ""
        if href.startswith("/"):
            href = "https://finance.yahoo.com" + href

        # footer -> publishing -> publisher + relative time
        footer = content_div.find("div", class_="footer")
        publisher = None
        relative_time = None

        if footer:
            publishing_div = footer.find("div", class_="publishing")
            if publishing_div:
                # Example text content:
                # "ACCESS Newswire • 7h ago"
                full_text = publishing_div.get_text(separator=" ", strip=True)

                publisher = None
                relative_time = None

                if "•" in full_text:
                    before, after = full_text.split("•", 1)
                    publisher = before.strip() or None
                    relative_time = after.strip() or None
                else:
                    # Fallback: no bullet, treat everything as publisher
                    publisher = full_text or None

        items.append(
            {
                "title": title,
                "publisher": publisher,
                "relativeTime": relative_time,
                "link": href,
            }
        )

        if len(items) >= count:
            break

    return items


def register_news_tools(mcp: FastMCP) -> None:
    """
    Register news + press-release tools on the given MCP server.
    """

    @mcp.tool()
    def get_yahoo_press_releases(ticker: str, count: int = 10) -> list[dict]:
        """
        Scrape latest Yahoo Finance *press releases* for a ticker.

        Source:
          https://finance.yahoo.com/quote/<TICKER>/news/
        """
        return _scrape_yahoo_quote_section(ticker, "news", count)
