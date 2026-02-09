from datetime import datetime, timezone
from scrape2rss import Article, WebsiteMeta, WebsiteScraper
import requests
from bs4 import BeautifulSoup


class KubeVirtNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="kubevirt",
        title="KubeVirt Blogs",
        url="https://kubevirt.io/blogs/",
        description="KubeVirt blogs and news",
    )

    interval_seconds = 43200 # 12 hours

    BASE_URL = "https://kubevirt.io"
    BLOG_URL = f"{BASE_URL}/blogs/"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []
        try:
            response = requests.get(self.BLOG_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.BLOG_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.select("ul.posts > li"):
                title_anchor = item.select_one("h2.posts-title a[href]")
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

                date_div = item.select_one("div.posts-date")
                date_text = date_div.get_text(strip=True) if date_div else ""
                if not date_text:
                    continue

                try:
                    published = datetime.strptime(date_text, "%B %d, %Y").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue

                if published <= since:
                    continue

                summary = None
                if date_div is not None:
                    for sibling in date_div.next_siblings:
                        if not isinstance(sibling, str):
                            continue
                        text = sibling.strip()
                        if text:
                            summary = text
                            break

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
            print(f"Error: Network error scraping KubeVirt: {str(e)}")
        except Exception as e:
            print(f"Error scraping KubeVirt news: {str(e)}")

        return articles
