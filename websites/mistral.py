from datetime import datetime, timezone
from scrape2rss import Article, WebsiteMeta, WebsiteScraper
import requests



class ExampleNews(WebsiteScraper):
    meta = WebsiteMeta(
        name="mistral-ai",
        title="Mistral AI",
        url="https://mistral.ai/en/news",
        description="Mistral AI news",
    )

    interval_seconds = 43200 # 12h

    CMS_URL = "https://cms.mistral.ai/items/posts?fields=*,translations.*,category.*,parent.id&sort=-date&limit=10&page=1"
    BASE_URL = "https://mistral.ai"
    
    def get_new_articles(self, since: datetime) -> list[Article]:

        articles = []

        try:
            response = requests.get(self.CMS_URL, timeout=30)
            
            if response.status_code != 200:
                print(f"HTTP {response.status_code} when fetching Mistral CMS")
                return articles
            
            data = response.json()
            articles = []
            
            # Process articles from CMS data
            for item in data.get('data', []):
                item_id = item.get('id')
                date = item.get('date')
                slug = item.get('slug')
                
                if not all([item_id, date, slug]):
                    continue
                
                # Find English translation
                title_en = ""
                description_en = ""
                
                for translation in item.get('translations', []):
                    if translation.get('languages_code') == 'en':
                        title_en = translation.get('title')
                        description_en = translation.get('description')
                        break
                
                if not title_en:
                    continue  # Skip if no English translation
                
                # Format date
                article_date = datetime.now(timezone.utc)
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    if date_obj.tzinfo is None:
                        date_obj = date_obj.replace(tzinfo=timezone.utc)
                    article_date = date_obj.astimezone(timezone.utc)
                except Exception:
                    pass

                if article_date <= since:
                    continue
                
                # Build article URL
                article_url = f"{self.BASE_URL}/en/news/{slug}"

                articles.append(Article(
                    id = f"{item_id}",
                    title = title_en,
                    url = article_url,
                    published = article_date,
                    summary = description_en
                ))
            
            
            return articles
            
        except requests.RequestException as e:
            print(f"Network error scraping Mistral: {str(e)}")
            return articles
        
        except Exception as e:
            print(f"Error scraping Mistral news: {str(e)}")
            return articles
