import json
import re
from datetime import datetime, timezone

import requests

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class MistralAINews(WebsiteScraper):
    meta = WebsiteMeta(
        name="mistral-ai",
        title="Mistral AI",
        url="https://mistral.ai/news",
        description="Mistral AI news",
    )

    interval_seconds = 43200  # 12 hours

    NEWS_URL = "https://mistral.ai/news"
    BASE_URL = "https://mistral.ai"

    def _extract_posts(self, html: str) -> list[dict]:
        pushes = re.findall(
            r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL
        )
        decoder = json.JSONDecoder()
        for push in pushes:
            try:
                decoded = push.encode().decode("unicode_escape")
            except (UnicodeDecodeError, ValueError):
                continue
            start = decoded.find('"posts":[')
            if start < 0:
                continue
            j = start + len('"posts":')
            try:
                posts, _ = decoder.raw_decode(decoded, j)
                return posts
            except json.JSONDecodeError:
                continue
        return []

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.NEWS_URL, timeout=30)
            if response.status_code != 200:
                print(
                    f"HTTP {response.status_code} when fetching {self.NEWS_URL}"
                )
                return articles

            for item in self._extract_posts(response.text):
                slug = item.get("slug")
                title = item.get("title")
                date_str = item.get("date")
                if not slug or not title or not date_str:
                    continue

                published = datetime.now(timezone.utc)
                try:
                    date_obj = datetime.fromisoformat(date_str)
                    if date_obj.tzinfo is None:
                        date_obj = date_obj.replace(tzinfo=timezone.utc)
                    published = date_obj.astimezone(timezone.utc)
                except ValueError:
                    continue

                if published <= since:
                    continue

                articles.append(
                    Article(
                        id=slug,
                        title=title,
                        url=f"{self.BASE_URL}/news/{slug}",
                        published=published,
                        summary=item.get("description") or None,
                    )
                )

        except requests.RequestException as e:
            print(f"Error: Network error scraping Mistral: {str(e)}")
        except Exception as e:
            print(f"Error scraping Mistral news: {str(e)}")

        return articles
