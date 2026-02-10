from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class AnthropicEngineeringNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="anthropic-engineering",
        title="Engineering at Anthropic",
        url="https://www.anthropic.com/engineering",
        description="Engineering articles from Anthropic",
    )

    interval_seconds = 43200  # 12 hours

    BASE_URL = "https://www.anthropic.com"
    ENGINEERING_URL = f"{BASE_URL}/engineering"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.ENGINEERING_URL, timeout=30)
            if response.status_code != 200:
                print(
                    f"HTTP {response.status_code} when fetching {self.ENGINEERING_URL}"
                )
                return articles

            soup = BeautifulSoup(response.text, "html.parser")

            for item in soup.select("article a[href^='/engineering/']"):
                title_tag = item.select_one("h2, h3")
                if title_tag is None:
                    continue

                title = title_tag.get_text(strip=True)
                if not title:
                    continue

                href_value = item.get("href")
                if not isinstance(href_value, str):
                    continue
                href = href_value.strip()
                if not href:
                    continue

                date_tag = item.select_one("div[class*='__date']")
                if date_tag is None:
                    continue

                date_text = date_tag.get_text(strip=True)
                if not date_text:
                    continue

                try:
                    published = datetime.strptime(date_text, "%b %d, %Y").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue

                if published <= since:
                    continue

                summary_tag = item.select_one("p")
                summary = summary_tag.get_text(strip=True) if summary_tag else None

                full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
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
            print(f"Error: Network error scraping Anthropic Engineering: {str(e)}")
        except Exception as e:
            print(f"Error scraping Anthropic Engineering news: {str(e)}")

        return articles
