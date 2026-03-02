from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class LittleJoBlogNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="little-jo-blog",
        title="Le blog de Little Jo",
        url="https://blog.littlejo.link/",
        description="Recent articles from Little Jo's blog",
    )

    interval_seconds = 43200  # 12 hours

    BLOG_URL = "https://blog.littlejo.link/"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.BLOG_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.BLOG_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")

            for item in soup.select("section.space-y-10.w-full > article"):
                anchor = item.select_one("header a[href]")
                time_tag = item.select_one("time[datetime]")
                if anchor is None or time_tag is None:
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

                datetime_value = time_tag.get("datetime")
                if not isinstance(datetime_value, str):
                    continue

                try:
                    published = datetime.fromisoformat(datetime_value)
                except ValueError:
                    continue

                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
                published = published.astimezone(timezone.utc)

                if published <= since:
                    continue

                summary_tag = item.select_one("div.prose")
                summary = summary_tag.get_text(strip=True) if summary_tag else None

                full_url = (
                    f"https://blog.littlejo.link{href}"
                    if href.startswith("/")
                    else href
                )
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
            print(f"Error: Network error scraping Little Jo blog: {str(e)}")
        except Exception as e:
            print(f"Error scraping Little Jo blog news: {str(e)}")

        return articles
