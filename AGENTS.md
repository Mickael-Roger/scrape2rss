## Project summary

Scrape2RSS is a Python web server that exposes RSS feeds for websites that do not provide them.

## Key notes

- Language: Python.
- Data persistence: SQLite database.
- All stored and handled datetimes must be in UTC.
- Keep this file up to date as the project evolves.

## Implemented scrapers

- `websites/arthurchiao.py`: scrapes https://arthurchiao.art/articles/ by parsing HTML (`#articles ul.posts > li`) and extracts article date/title/url.
- `websites/anthropic_engineering.py`: scrapes https://www.anthropic.com/engineering by parsing engineering article cards (`article a[href^='/engineering/']`) and extracts article date/title/url.
- `websites/anthropic_research.py`: scrapes https://www.anthropic.com/research by parsing research cards (`main a[href^='/research/']:not([href^='/research/team/'])`) and extracts article date/title/url.
- `websites/google_developers_ai.py`: scrapes https://developers.googleblog.com/search/?technology_categories=AI by parsing search result cards (`div.search-results__results-wrapper ul > li.search-result`) and extracts article date/title/url.
- `websites/little_joe.py`: scrapes https://blog.littlejo.link/ by parsing recent article cards (`section.space-y-10.w-full > article`) and extracts article date/title/url.

## Containerization

- `Dockerfile`: builds and runs the app with `python:3.13-slim`, installs `requirements.txt`, exposes port `8082`, and starts `scrape2rss.py`.
- `.dockerignore`: excludes local virtualenv/cache/git metadata and SQLite DB from Docker build context.
- `docker-compose.yml`: defines a `scrape2rss` service that builds from the local Dockerfile, maps port `8082`, and mounts `config.yaml` read-only.
