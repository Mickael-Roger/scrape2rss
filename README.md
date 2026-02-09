# Scrape2RSS

Scrape2RSS is a Python web server that exposes RSS feeds for websites that do not provide them.

Each website scraper runs on a schedule, stores entries in SQLite, and exposes a feed at:
`https://SERVER:PORT/WEBSITE_NAME/`

## Directory content

- `scrape2rss.py`: The main server that exposes the RSS endpoints.
- `config.yaml`: The configuration file.
- `websites/`: A directory that contains one Python file per website to scrape.

## Principles

- Keep the service lightweight, reliable, and easy to configure.
- Add one scraper module per website under `websites/`.
- Use SQLite for persistence and avoid external dependencies unless needed.
- Prefer clear, explicit RSS output over clever heuristics.
- All stored and handled datetimes must be in UTC.

## Run the server

```bash
python scrape2rss.py
```

The server binds `server.port` from `config.yaml` (default `8082`).

## Configuration

`config.yaml` controls the server port and global refresh period:

```yaml
server:
  port: 8082
  refresh_period: 480
```

`refresh_period` is in minutes and is used as the default scraping interval.

## Add a new scraper

1. Create a new file in `websites/`.
2. Subclass `WebsiteScraper`.
3. Implement `get_new_articles(self, since)` and return `Article` items.
4. Use UTC datetimes for `Article.published`.

Scrapers can override the default interval by setting `interval_seconds`.

## Data schema and scraper structure

Each website scraper is a subclass of `WebsiteScraper` and returns `Article` items.
The scraper exposes metadata through `WebsiteMeta`.
Scraping frequency defaults to `server.refresh_period` in `config.yaml` and can be overridden per scraper with `interval_seconds`.

Example:

```python
from datetime import datetime, timezone
from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class ExampleNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="example-news",
        title="Example News",
        url="https://example.com/news",
        description="Latest news from Example",
    )

    interval_seconds = 600

    def get_new_articles(self, since: datetime) -> list[Article]:
        # fetch and parse the website here
        return [
            Article(
                id="example-1",
                title="Hello RSS",
                url="https://example.com/news/hello",
                published=datetime.now(timezone.utc),
                summary="Short summary",
            )
        ]
```
