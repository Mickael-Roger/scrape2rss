from datetime import datetime
from scrape2rss import Article, WebsiteMeta, WebsiteScraper


class ExampleNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="example-news",
        title="Example News",
        url="https://example.com/news",
        description="Latest news from Example",
    )

    interval_seconds = 600

    def get_new_articles(self, since: datetime) -> list[Article]:
        # fetch and parse the website here
        return [
            Article(
                id="example-1",
                title="Hello RSS",
                url="https://example.com/news/hello",
                published=datetime.utcnow(),
                summary="Short summary",
            )
        ]
