## Project summary

Scrape2RSS is a Python web server that exposes RSS feeds for websites and newsletters that do not provide them.

## Key notes

- Language: Python.
- Data persistence: SQLite database.
- All stored and handled datetimes must be in UTC.
- Website and newsletter feeds share the existing `websites` and `news` SQLite tables.
- `GET /` returns a plain-text list of exposed RSS feeds.
- Keep this file up to date as the project evolves.

## Newsletter ingestion

- `newsletter/`: contains one Python file per newsletter parser.
- Newsletter parsers subclass `NewsletterParser`, define `meta`, `sender_email`, optional `subject_regex`, and implement `parse_email(self, message)` returning `Article` items.
- Newsletter ingestion is configured under `newsletter.imap` in `config.yaml` with SSL/TLS IMAP settings (`host`, `port`, `username`, `password`, `mailbox`, optional `processed_mailbox`, optional `refresh_period`).
- The IMAP poller reads unread messages, matches them by sender email and optional subject regex, inserts parsed articles into SQLite, and moves successfully parsed messages to `INBOX/Newsletter` by default.

## Implemented scrapers

- `websites/arthurchiao.py`: scrapes https://arthurchiao.art/articles/ by parsing HTML (`#articles ul.posts > li`) and extracts article date/title/url.
- `websites/anthropic_engineering.py`: scrapes https://www.anthropic.com/engineering by parsing engineering article cards (`article a[href^='/engineering/']`) and extracts article date/title/url.
- `websites/anthropic_research.py`: scrapes https://www.anthropic.com/research by parsing research cards (`main a[href^='/research/']:not([href^='/research/team/'])`) and extracts article date/title/url.
- `websites/google_developers_ai.py`: scrapes https://developers.googleblog.com/search/?technology_categories=AI by parsing search result cards (`div.search-results__results-wrapper ul > li.search-result`) and extracts article date/title/url.
- `websites/little_joe.py`: scrapes https://blog.littlejo.link/ by parsing recent article cards (`section.space-y-10.w-full > article`) and extracts article date/title/url.
- `websites/weeklyrobotics.py`: scrapes https://www.weeklyrobotics.com/archive/ by parsing issue cards (`div.issue-card`) to find issue links, then visits each issue page to extract individual news items from the article content (`div#article-content h2/h3`) with descriptions from paragraphs and images. Each news item's external source URL is extracted from the `div.learn-more-container` link that follows the item's description.
- `websites/qwen_ai.py`: scrapes https://qwenlm.github.io/blog/ via the JSON API at `https://qwen.ai/api/v2/article/retrieval?type=qwen_ai&language=en-US` and extracts article date/title/url/summary from `data.articles[]` using the `path`, `title`, `extra.date`, and `extra.introduction` fields. Runs once per day.
- `websites/exe_dev.py`: scrapes https://blog.exe.dev/ by parsing blog cards (`article.post-card`) and extracts article date/title/url/summary.

## Containerization

- `Dockerfile`: builds and runs the app with `python:3.13-slim`, installs `requirements.txt`, exposes port `8082`, and starts `scrape2rss.py`.
- `.dockerignore`: excludes local virtualenv/cache/git metadata and SQLite DB from Docker build context.
- `docker-compose.yml`: defines a `scrape2rss` service that builds from the local Dockerfile, maps port `8082`, and mounts `config.yaml` read-only.
