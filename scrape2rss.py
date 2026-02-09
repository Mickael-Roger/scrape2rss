from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.util
from pathlib import Path
import sqlite3
import sys
import threading
import time
from typing import Sequence
import xml.etree.ElementTree as ET
import yaml

@dataclass(frozen=True, slots=True)
class WebsiteMeta:
    name: str
    title: str
    url: str
    description: str

@dataclass(frozen=True, slots=True)
class Article:
    id: str
    title: str
    url: str
    published: datetime
    summary: str | None = None

class WebsiteScraper(ABC):
    meta: WebsiteMeta
    interval_seconds: int = 300

    @abstractmethod
    def get_new_articles(self, since: datetime) -> Sequence[Article]:
        raise NotImplementedError


def discover_scrapers(websites_dir: Path | None = None) -> list[type[WebsiteScraper]]:
    base_dir = websites_dir or Path(__file__).with_name("websites")
    if not base_dir.exists():
        return []

    scrapers: list[type[WebsiteScraper]] = []
    for module_path in sorted(base_dir.glob("*.py")):
        if module_path.name == "__init__.py":
            continue

        module_name = f"websites.{module_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        for obj in module.__dict__.values():
            if (
                isinstance(obj, type)
                and issubclass(obj, WebsiteScraper)
                and obj is not WebsiteScraper
            ):
                scrapers.append(obj)

    return scrapers


def load_config(config_path: Path | None = None) -> dict:
    path = config_path or Path(__file__).with_name("config.yaml")
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def init() -> dict:
    config = load_config()
    db_path = Path(__file__).with_name("rss.sqlite")

    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS websites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website_id INTEGER NOT NULL,
                link TEXT NOT NULL,
                title TEXT NOT NULL,
                publication_date TEXT NOT NULL,
                description TEXT DEFAULT NULL,
                FOREIGN KEY (website_id) REFERENCES websites(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS news_website_link_uq
            ON news (website_id, link)
            """
        )

        scrapers = discover_scrapers()
        for scraper_cls in scrapers:
            meta = scraper_cls.meta
            cursor.execute("SELECT id FROM websites WHERE name = ?", (meta.name,))
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO websites (name, title, url, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (meta.name, meta.title, meta.url, meta.description),
                )

        connection.commit()
    finally:
        connection.close()

    return config


def start_server(port: int, website_names: set[str]) -> None:
    class RSSHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path.endswith("/"):
                path = path[:-1]
            if path.startswith("/"):
                path = path[1:]

            if path and path in website_names:
                feed = build_rss_feed(path)
                if feed is None:
                    self.send_response(HTTPStatus.NOT_FOUND)
                    self.end_headers()
                    return

                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
                self.end_headers()
                self.wfile.write(feed)
                return

            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = HTTPServer(("", port), RSSHandler)
    server.serve_forever()


def build_rss_feed(website_name: str) -> bytes | None:
    db_path = Path(__file__).with_name("rss.sqlite")
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, name, title, url, description FROM websites WHERE name = ?",
            (website_name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        website_id, name, title, url, description = row
        cursor.execute(
            """
            SELECT link, title, publication_date, description
            FROM news
            WHERE website_id = ?
            ORDER BY publication_date DESC
            """,
            (website_id,),
        )
        items = cursor.fetchall()

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = url
    ET.SubElement(channel, "description").text = description

    for link, item_title, publication_date, item_description in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = item_title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = link
        try:
            published = datetime.fromisoformat(publication_date)
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            published = published.astimezone(timezone.utc)
            pub_date = published.strftime("%a, %d %b %Y %H:%M:%S %z")
            ET.SubElement(item, "pubDate").text = pub_date
        except Exception:
            ET.SubElement(item, "pubDate").text = publication_date

        if item_description:
            ET.SubElement(item, "description").text = item_description

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)


def start_scrapers(
    scrapers: list[type[WebsiteScraper]],
    default_interval_seconds: int,
    restart_delay_seconds: int = 180,
) -> None:
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def parse_utc(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def get_latest_publication_date(website_name: str) -> datetime:
        db_path = Path(__file__).with_name("rss.sqlite")
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM websites WHERE name = ?", (website_name,))
            row = cursor.fetchone()
            if row is None:
                return datetime(2000, 1, 1, tzinfo=timezone.utc)

            website_id = row[0]
            cursor.execute(
                "SELECT publication_date FROM news WHERE website_id = ?"
                " ORDER BY publication_date DESC LIMIT 1",
                (website_id,),
            )
            row = cursor.fetchone()
            if row is None or row[0] is None:
                return datetime(2000, 1, 1, tzinfo=timezone.utc)

            return parse_utc(row[0])

    def run_scraper(scraper_cls: type[WebsiteScraper]) -> None:
        scraper = scraper_cls()
        interval_seconds = (
            scraper_cls.interval_seconds
            if "interval_seconds" in scraper_cls.__dict__
            else default_interval_seconds
        )
        db_path = Path(__file__).with_name("rss.sqlite")

        while True:
            try:
                since = get_latest_publication_date(scraper.meta.name)
                articles = scraper.get_new_articles(since)
                if articles:
                    with sqlite3.connect(db_path) as connection:
                        cursor = connection.cursor()
                        before_changes = connection.total_changes
                        cursor.execute(
                            "SELECT id FROM websites WHERE name = ?",
                            (scraper.meta.name,),
                        )
                        row = cursor.fetchone()
                        if row is None:
                            raise RuntimeError(
                                f"Website {scraper.meta.name} not found in database"
                            )

                        website_id = row[0]
                        for article in articles:
                            published = article.published
                            if published.tzinfo is None:
                                published = published.replace(tzinfo=timezone.utc)
                            published = published.astimezone(timezone.utc)
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO news
                                    (website_id, link, title, publication_date, description)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    website_id,
                                    article.url,
                                    article.title,
                                    published.isoformat(),
                                    article.summary,
                                ),
                            )
                        connection.commit()
                        inserted = connection.total_changes - before_changes
                        if inserted:
                            print(
                                f"Inserted {inserted} new articles for"
                                f" {scraper.meta.name}"
                            )
            except Exception as exc:
                print(f"Scraper error for {scraper_cls.__name__}: {exc}")
            time.sleep(interval_seconds)

    def build_thread(scraper_cls: type[WebsiteScraper]) -> threading.Thread:
        return threading.Thread(target=run_scraper, args=(scraper_cls,), daemon=True)

    threads: dict[type[WebsiteScraper], threading.Thread] = {}
    restart_at: dict[type[WebsiteScraper], float | None] = {}

    for scraper_cls in scrapers:
        thread = build_thread(scraper_cls)
        threads[scraper_cls] = thread
        restart_at[scraper_cls] = None
        thread.start()

    def monitor_threads() -> None:
        while True:
            now = time.monotonic()
            for scraper_cls, thread in list(threads.items()):
                if thread.is_alive():
                    restart_at[scraper_cls] = None
                    continue

                if restart_at[scraper_cls] is None:
                    restart_at[scraper_cls] = now + restart_delay_seconds
                    print(
                        "Scraper thread for"
                        f" {scraper_cls.__name__} stopped, restarting in"
                        f" {restart_delay_seconds} seconds"
                    )
                    continue

                restart_time = restart_at[scraper_cls]
                if restart_time is not None and now >= restart_time:
                    new_thread = build_thread(scraper_cls)
                    threads[scraper_cls] = new_thread
                    restart_at[scraper_cls] = None
                    new_thread.start()

            time.sleep(5)

    monitor_thread = threading.Thread(target=monitor_threads, daemon=True)
    monitor_thread.start()


def main() -> None:
    config = init()
    scrapers = discover_scrapers()
    website_names = {scraper.meta.name for scraper in scrapers}
    refresh_period = (
        config.get("server", {}).get("refresh_period")
        if isinstance(config.get("server"), dict)
        else None
    )
    default_interval_seconds = (
        int(refresh_period) * 60 if refresh_period else WebsiteScraper.interval_seconds
    )
    start_scrapers(scrapers, default_interval_seconds)
    port = (
        config.get("server", {}).get("port")
        if isinstance(config.get("server"), dict)
        else None
    )
    start_server(int(port) if port else 8082, website_names)


if __name__ == "__main__":
    sys.modules.setdefault("scrape2rss", sys.modules[__name__])
    main()
