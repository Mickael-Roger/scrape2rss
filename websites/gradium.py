from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class GradiumBlog(WebsiteScraper):
    meta = WebsiteMeta(
        name="gradium-blog",
        title="Gradium Blog",
        url="https://gradium.ai/blog",
        description="Updates, announcements, and research from the Gradium team.",
    )

    interval_seconds = 43200  # 12 hours

    BLOG_URL = "https://gradium.ai/blog"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.BLOG_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.BLOG_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")

            for card in soup.select('section#blog div.space-y-12 > a'):
                href_value = card.get("href")
                if not isinstance(href_value, str):
                    continue
                href = href_value.strip()
                if not href:
                    continue

                title_tag = card.select_one("article h2")
                if title_tag is None:
                    continue
                title = title_tag.get_text(strip=True)
                if not title:
                    continue

                time_tag = card.select_one("article time")
                if time_tag is None:
                    continue
                date_str = time_tag.get("dateTime") or time_tag.get_text(strip=True)
                if not date_str:
                    continue

                try:
                    published = datetime.strptime(date_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue

                if published <= since:
                    continue

                summary_tag = card.select_one("article p.text-lightgray")
                summary = summary_tag.get_text(strip=True) if summary_tag else None
                full_url = urljoin(self.BLOG_URL, href)

                articles.append(
                    Article(
                        id=href,
                        title=title,
                        url=full_url,
                        published=published,
                        summary=summary,
                    )
                )

        except requests.RequestException as e:
            print(f"Error: Network error scraping Gradium blog: {str(e)}")
        except Exception as e:
            print(f"Error scraping Gradium blog: {str(e)}")

        return articles
