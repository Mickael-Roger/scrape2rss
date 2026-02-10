from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class GoogleDevelopersAINews(WebsiteScraper):
    meta = WebsiteMeta(
        name="google-developers-ai",
        title="Google Developers Blog (AI)",
        url="https://developers.googleblog.com/search/?technology_categories=AI",
        description="AI articles from the Google Developers Blog",
    )

    interval_seconds = 43200  # 12 hours

    BASE_URL = "https://developers.googleblog.com"
    SEARCH_URL = f"{BASE_URL}/search/?technology_categories=AI"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.SEARCH_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.SEARCH_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")

            for item in soup.select(
                "div.search-results__results-wrapper ul > li.search-result"
            ):
                title_anchor = item.select_one("h3.search-result__title a[href]")
                if title_anchor is None:
                    continue

                title = title_anchor.get_text(strip=True)
                if not title:
                    continue

                href_value = title_anchor.get("href")
                if not isinstance(href_value, str):
                    continue
                href = href_value.strip()
                if not href:
                    continue

                eyebrow = item.select_one("p.search-result__eyebrow")
                if eyebrow is None:
                    continue
                eyebrow_text = eyebrow.get_text(strip=True)
                if not eyebrow_text:
                    continue

                date_text = eyebrow_text.split("/", 1)[0].strip()
                try:
                    published = datetime.strptime(date_text, "%b. %d, %Y").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue

                if published <= since:
                    continue

                summary_tag = item.select_one("p.search-result__summary")
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
            print(f"Error: Network error scraping Google Developers AI: {str(e)}")
        except Exception as e:
            print(f"Error scraping Google Developers AI news: {str(e)}")

        return articles
