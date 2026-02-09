from datetime import datetime, timezone
from scrape2rss import Article, WebsiteMeta, WebsiteScraper
import requests
from bs4 import BeautifulSoup


class KyutaiNews(WebsiteScraper):
    meta = WebsiteMeta(
        name = "kyutai",
        title = "Kyutai News",
        url = "https://kyutai.org/blog.html",
        description = "Kyutai: Openscience AI",
    )

    interval_seconds = 43200 # 12 hours

    BASE_URL = "https://kyutai.org"
    BLOG_URL = f"{BASE_URL}/blog.html"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []
        try:
            response = requests.get(self.BLOG_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.BLOG_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.find_all("li"):
                anchor = item.find("a", href=True)
                if anchor is None:
                    continue

                title_span = anchor.find("span", class_="font-semibold")
                title = title_span.get_text(strip=True) if title_span else None
                if not title:
                    continue

                date_span = anchor.find("span", string=True)
                date_value = None
                for span in anchor.find_all("span"):
                    text = span.get_text(strip=True)
                    if len(text) == 10 and text[4] == "-" and text[7] == "-":
                        date_value = text
                        break

                if not date_value:
                    continue

                try:
                    published = datetime.strptime(date_value, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue

                if published <= since:
                    continue

                description_span = anchor.select_one("span.text-textgray.text-sm.block")
                description = (
                    description_span.get_text(strip=True)
                    if description_span
                    else None
                )

                href = anchor["href"].strip()
                if not href:
                    continue

                full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                articles.append(
                    Article(
                        id=href,
                        title=title,
                        url=full_url,
                        published=published,
                        summary=description,
                    )
                )

        except requests.RequestException as e:
            print(f"Error: Network error scraping Kyutai: {str(e)}")
        except Exception as e:
            print(f"Error scraping Kyutai news: {str(e)}")

        return articles
