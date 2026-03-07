from datetime import datetime, timezone

import requests

from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class QwenAI(WebsiteScraper):
    meta = WebsiteMeta(
        name="qwen-ai",
        title="Qwen AI Blog",
        url="https://qwenlm.github.io/blog/",
        description="Blog articles from the Qwen AI team",
    )

    interval_seconds = 86400  # once per day

    API_URL = "https://qwen.ai/api/v2/article/retrieval?type=qwen_ai&language=en-US"
    BASE_ARTICLE_URL = "https://qwenlm.github.io/blog/"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []

        try:
            response = requests.get(self.API_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.API_URL}")
                return articles

            payload = response.json()
            if not payload.get("success"):
                print("Qwen AI API returned success=false")
                return articles

            raw_articles = payload.get("data", {}).get("articles", [])

            for raw in raw_articles:
                path = raw.get("path", "").strip()
                if not path:
                    continue

                title = raw.get("title", "").strip()
                if not title:
                    continue

                extra = raw.get("extra") or {}
                date_str = extra.get("date", "")
                if not date_str:
                    continue

                try:
                    published = datetime.fromisoformat(date_str).astimezone(
                        timezone.utc
                    )
                except ValueError:
                    continue

                if published <= since:
                    continue

                url = f"{self.BASE_ARTICLE_URL}{path}"
                summary = extra.get("introduction") or None

                articles.append(
                    Article(
                        id=path,
                        title=title,
                        url=url,
                        published=published,
                        summary=summary,
                    )
                )

        except requests.RequestException as e:
            print(f"Error: Network error scraping Qwen AI: {str(e)}")
        except Exception as e:
            print(f"Error scraping Qwen AI: {str(e)}")

        return articles
