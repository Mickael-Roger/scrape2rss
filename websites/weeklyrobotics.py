from datetime import datetime, timezone
from scrape2rss import Article, WebsiteMeta, WebsiteScraper
import requests
from bs4 import BeautifulSoup


class WeeklyRobotics(WebsiteScraper):
    meta = WebsiteMeta(
        name="weeklyrobotics",
        title="Weekly Robotics",
        url="https://www.weeklyrobotics.com/archive/",
        description="Weekly Robotics Newsletter",
    )

    interval_seconds = 43200  # 12 hours

    BASE_URL = "https://www.weeklyrobotics.com"
    ARCHIVE_URL = f"{BASE_URL}/archive/"

    def get_new_articles(self, since: datetime) -> list[Article]:
        articles: list[Article] = []
        try:
            response = requests.get(self.ARCHIVE_URL, timeout=30)
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching {self.ARCHIVE_URL}")
                return articles

            soup = BeautifulSoup(response.text, "html.parser")
            issue_cards = soup.find_all("div", class_="issue-card")

            issue_links = set()
            for card in issue_cards[:10]:
                link = card.find("a", href=lambda x: x and "/weekly-robotics-" in x)
                if link and link.get("href"):
                    href = link["href"].strip()
                    if href.startswith("/"):
                        full_url = f"{self.BASE_URL}{href}"
                    else:
                        full_url = href
                    issue_links.add(full_url)

            for issue_url in sorted(issue_links, reverse=True)[:5]:
                try:
                    issue_response = requests.get(issue_url, timeout=30)
                    if issue_response.status_code != 200:
                        print(
                            f"HTTP {issue_response.status_code} when fetching {issue_url}"
                        )
                        continue

                    issue_soup = BeautifulSoup(issue_response.text, "html.parser")

                    title_elem = issue_soup.find("h1", class_="article-title")
                    issue_title = (
                        title_elem.get_text(strip=True) if title_elem else issue_url
                    )

                    date_elem = issue_soup.find("div", class_="article-meta")
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        try:
                            published = datetime.strptime(
                                date_text, "%d %b %Y"
                            ).replace(tzinfo=timezone.utc)
                        except ValueError:
                            try:
                                published = datetime.strptime(
                                    date_text.split("Posted")[-1].strip(), "%d %b %Y"
                                ).replace(tzinfo=timezone.utc)
                            except ValueError:
                                continue
                    else:
                        continue

                    if published <= since:
                        continue

                    content_div = issue_soup.find("div", id="article-content")
                    if not content_div:
                        continue

                    current_title = None
                    current_link = None
                    current_summary_parts = []
                    fallback_url = issue_url

                    skip_sections = ["our sponsors", "events", "want to promote"]

                    def _flush_article():
                        """Append the current article to the list if valid."""
                        nonlocal current_title, current_link, current_summary_parts
                        if not current_title:
                            return
                        summary_text = " ".join(current_summary_parts).strip()
                        if summary_text:
                            articles.append(
                                Article(
                                    id=current_link or current_title,
                                    title=current_title,
                                    url=current_link or fallback_url,
                                    published=published,
                                    summary=summary_text[:500],
                                )
                            )

                    for child in content_div.children:
                        if child.name in ["h2", "h3"]:
                            _flush_article()
                            current_title = child.get_text(strip=True)
                            if any(
                                current_title.lower().startswith(s)
                                for s in skip_sections
                            ):
                                current_title = None
                                current_link = None
                                current_summary_parts = []
                                continue
                            # Try to get a link from the heading itself
                            link_elem = child.find("a", href=True)
                            if link_elem:
                                href = link_elem["href"].strip()
                                if href.startswith("/"):
                                    current_link = f"{self.BASE_URL}{href}"
                                else:
                                    current_link = href
                            else:
                                current_link = None
                            current_summary_parts = []
                        elif child.name == "div" and current_title:
                            # Extract the source URL from learn-more-container
                            if "learn-more-container" in (child.get("class") or []):
                                source_link = child.find("a", href=True)
                                if source_link:
                                    href = source_link["href"].strip()
                                    if href.startswith("/"):
                                        current_link = f"{self.BASE_URL}{href}"
                                    else:
                                        current_link = href
                        elif child.name == "p" and current_title:
                            text = child.get_text(strip=True)
                            if text:
                                current_summary_parts.append(text)
                        elif child.name == "picture" and current_title:
                            img = child.find("img")
                            if img and img.get("alt"):
                                current_summary_parts.append(
                                    f"[Image: {img.get('alt')}]"
                                )

                    _flush_article()

                except requests.RequestException as e:
                    print(f"Error: Network error fetching {issue_url}: {str(e)}")
                except Exception as e:
                    print(f"Error processing {issue_url}: {str(e)}")

        except requests.RequestException as e:
            print(f"Error: Network error scraping WeeklyRobotics: {str(e)}")
        except Exception as e:
            print(f"Error scraping WeeklyRobotics: {str(e)}")

        return articles
