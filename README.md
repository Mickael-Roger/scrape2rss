# Scrape2RSS

Scrape2RSS is a Python web server that exposes RSS feeds for websites that do not provide them.

Each website scraper or newsletter parser runs on a schedule, stores entries in SQLite, and exposes a feed at:
`https://SERVER:PORT/FEED_NAME/`

## Directory content

- `scrape2rss.py`: The main server that exposes the RSS endpoints.
- `config.yaml`: The configuration file.
- `websites/`: A directory that contains one Python file per website to scrape.
- `newsletter/`: A directory that contains one Python file per newsletter to parse.

## Principles

- Keep the service lightweight, reliable, and easy to configure.
- Add one scraper module per website under `websites/`.
- Add one newsletter parser module per newsletter under `newsletter/`.
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

Newsletter ingestion is disabled by default. Configure an SSL/TLS IMAP mailbox to enable it:

```yaml
newsletter:
  imap:
    host: imap.example.com
    port: 993
    username: newsletters@example.com
    password: change-me
    mailbox: INBOX
    processed_mailbox: INBOX/Newsletter
    refresh_period: 5
```

The IMAP poller reads unread messages, matches them to a newsletter parser by sender email and optional subject regex, stores parsed articles, then moves successfully parsed messages to `INBOX/Newsletter` by default.

## Add a new scraper

1. Create a new file in `websites/`.
2. Subclass `WebsiteScraper`.
3. Implement `get_new_articles(self, since)` and return `Article` items.
4. Use UTC datetimes for `Article.published`.

Scrapers can override the default interval by setting `interval_seconds`.

## Add a newsletter parser

1. Create a new file in `newsletter/`.
2. Subclass `NewsletterParser`.
3. Set `meta`, `sender_email`, and optionally `subject_regex`.
4. Implement `parse_email(self, message)` and return `Article` items.
5. Use UTC datetimes for `Article.published`.

Example:

```python
from email.message import EmailMessage
from datetime import datetime, timezone
from scrape2rss import Article, NewsletterParser, WebsiteMeta


class ExampleNewsletter(NewsletterParser):
    meta = WebsiteMeta(
        name="example-newsletter",
        title="Example Newsletter",
        url="mailto:news@example.com",
        description="Items from the Example newsletter",
    )
    sender_email = "news@example.com"
    subject_regex = r"^Example Newsletter"

    def parse_email(self, message: EmailMessage) -> list[Article]:
        return [
            Article(
                id=message.get("Message-ID", "example-newsletter"),
                title=message.get("Subject", "Example Newsletter"),
                url="https://example.com/news/item",
                published=datetime.now(timezone.utc),
                summary=None,
            )
        ]
```

## Data schema and scraper structure

Each website scraper is a subclass of `WebsiteScraper` and each newsletter parser is a subclass of `NewsletterParser`.
Both return `Article` items and expose feed metadata through `WebsiteMeta`.
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
