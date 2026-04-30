from __future__ import annotations

from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime

from scrape2rss import Article, NewsletterParser, WebsiteMeta


class VisionIANewsletter(NewsletterParser):
    meta = WebsiteMeta(
        name="vision-ia",
        title="Vision IA",
        url="https://vision-ia.beehiiv.com/",
        description="Newsletter Vision IA: actualités quotidiennes sur l'intelligence artificielle.",
    )

    sender_email = "vision-ia@mail.beehiiv.com"

    def parse_email(self, message: EmailMessage) -> list[Article]:
        subject = (message.get("Subject") or "").strip()
        if not subject:
            return []

        url = (message.get("x-newsletter") or "").strip()
        if not url:
            return []

        date_header = message.get("Date")
        if date_header:
            published = parsedate_to_datetime(date_header)
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            else:
                published = published.astimezone(timezone.utc)
        else:
            published = datetime.now(timezone.utc)

        html_part = message.get_body(preferencelist=("html",))
        summary = html_part.get_content() if html_part is not None else None

        return [
            Article(
                id=url,
                title=subject,
                url=url,
                published=published,
                summary=summary,
            )
        ]
