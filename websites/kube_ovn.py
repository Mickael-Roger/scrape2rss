from datetime import datetime, timezone
from scrape2rss import Article, WebsiteMeta, WebsiteScraper
import requests
from bs4 import BeautifulSoup


class KubeOvnNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="kube-ovn",
        title="Kube-OVN News",
        url="https://www.kube-ovn.io/news/all",
        description="Kube-OVN news and blog",
    )

    interval_seconds = 43200 # 12 hours

    BASE_URL = "https://www.kube-ovn.io"
    NEWS_URL = f"{BASE_URL}/news/all"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []
        try:
            response = requests.get(self.NEWS_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.NEWS_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.select("article.blog-index__post-wrapper"):
                title_anchor = item.select_one("h3 a[href]")
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

                date_span = item.select_one("span.blog-index__post-date")
                date_text = date_span.get_text(strip=True) if date_span else ""
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

                description_tag = item.select_one("p")
                summary = description_tag.get_text(strip=True) if description_tag else None

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
            print(f"Error: Network error scraping Kube-OVN: {str(e)}")
        except Exception as e:
            print(f"Error scraping Kube-OVN news: {str(e)}")

        return articles
