from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class ExeDevBlogNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="exe-dev-blog",
        title="exe.dev blog",
        url="https://blog.exe.dev/",
        description="Updates, tutorials, and news from the exe.dev team.",
    )

    interval_seconds = 43200  # 12 hours

    BLOG_URL = "https://blog.exe.dev/"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.BLOG_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.BLOG_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")

            for item in soup.select("article.post-card"):
                anchor = item.select_one("a[href]")
                title_tag = item.select_one("h2")
                date_tag = item.select_one(".post-meta span")
                if anchor is None or title_tag is None or date_tag is None:
                    continue

                title = title_tag.get_text(strip=True)
                if not title:
                    continue

                href_value = anchor.get("href")
                if not isinstance(href_value, str):
                    continue
                href = href_value.strip()
                if not href:
                    continue

                date_text = date_tag.get_text(strip=True)
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

                summary_tag = item.select_one(".post-description")
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
            print(f"Error: Network error scraping exe.dev blog: {str(e)}")
        except Exception as e:
            print(f"Error scraping exe.dev blog news: {str(e)}")

        return articles
