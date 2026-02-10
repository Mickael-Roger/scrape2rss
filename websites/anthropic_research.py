from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class AnthropicResearchNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="anthropic-research",
        title="Anthropic Research",
        url="https://www.anthropic.com/research",
        description="Research publications from Anthropic",
    )

    interval_seconds = 43200  # 12 hours

    BASE_URL = "https://www.anthropic.com"
    RESEARCH_URL = f"{BASE_URL}/research"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.RESEARCH_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.RESEARCH_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")
            seen_ids: set[str] = set()

            for item in soup.select(
                "main a[href^='/research/']:not([href^='/research/team/'])"
            ):
                href_value = item.get("href")
                if not isinstance(href_value, str):
                    continue
                href = href_value.strip()
                if not href or href in seen_ids:
                    continue

                date_tag = item.select_one("time")
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

                title_tag = item.select_one("h2, h3, h4")
                if title_tag is None:
                    title_tag = item.select_one("span[class*='title']")
                if title_tag is None:
                    continue

                title = title_tag.get_text(strip=True)
                if not title:
                    continue

                summary_tag = item.select_one("p")
                summary = summary_tag.get_text(strip=True) if summary_tag else None

                full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                seen_ids.add(href)
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
            print(f"Error: Network error scraping Anthropic Research: {str(e)}")
        except Exception as e:
            print(f"Error scraping Anthropic Research news: {str(e)}")

        return articles
