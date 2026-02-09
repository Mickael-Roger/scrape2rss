## Project summary

Scrape2RSS is a Python web server that exposes RSS feeds for websites that do not provide them.

## Key notes

- Language: Python.
- Data persistence: SQLite database.
- All stored and handled datetimes must be in UTC.
- Keep this file up to date as the project evolves.

## Implemented scrapers

- `websites/arthurchiao.py`: scrapes https://arthurchiao.art/articles/ by parsing HTML (`#articles ul.posts > li`) and extracts article date/title/url.

## Containerization

- `Dockerfile`: builds and runs the app with `python:3.13-slim`, installs `requirements.txt`, exposes port `8082`, and starts `scrape2rss.py`.
- `.dockerignore`: excludes local virtualenv/cache/git metadata and SQLite DB from Docker build context.
- `docker-compose.yml`: defines a `scrape2rss` service that builds from the local Dockerfile, maps port `8082`, and mounts `config.yaml` read-only.
