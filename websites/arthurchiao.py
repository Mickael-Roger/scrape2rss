from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class ArthurChiaoNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="arthurchiao",
        title="ArthurChiao Articles",
        url="https://arthurchiao.art/articles/",
        description="ArthurChiao blog articles (English)",
    )

    interval_seconds = 43200  # 12 hours

    BASE_URL = "https://arthurchiao.art"
    ARTICLES_URL = f"{BASE_URL}/articles/"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.ARTICLES_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.ARTICLES_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")

            for item in soup.select("#articles ul.posts > li"):
                date_span = item.select_one("span.date")
                anchor = item.select_one("a[href]")
                if date_span is None or anchor is None:
                    continue

                title = anchor.get_text(strip=True)
                if not title:
                    continue

                href_value = anchor.get("href")
                if not isinstance(href_value, str):
                    continue
                href = href_value.strip()
                if not href:
                    continue

                date_text = date_span.get_text(strip=True)
                if not date_text:
                    continue

                try:
                    published = datetime.strptime(date_text, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue

                if published <= since:
                    continue

                full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                articles.append(
                    Article(
                        id=href,
                        title=title,
                        url=full_url,
                        published=published,
                        summary=None,
                    )
                )

        except requests.RequestException as e:
            print(f"Error: Network error scraping ArthurChiao: {str(e)}")
        except Exception as e:
            print(f"Error scraping ArthurChiao articles: {str(e)}")

        return articles
