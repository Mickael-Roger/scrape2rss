## Project summary

Scrape2RSS is a Python web server that exposes RSS feeds for websites that do not provide them.

## Key notes

- Language: Python.
- Data persistence: SQLite database.
- All stored and handled datetimes must be in UTC.
- Keep this file up to date as the project evolves.

## Implemented scrapers

- `websites/arthurchiao.py`: scrapes https://arthurchiao.art/articles/ by parsing HTML (`#articles ul.posts > li`) and extracts article date/title/url.
