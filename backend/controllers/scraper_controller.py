from sqlmodel import Session
from fastapi import HTTPException
from models.website import Website, WebPage, WebsiteRead
from models.user import User
import requests
from bs4 import BeautifulSoup
import time

class ScraperController:
    @staticmethod
    def scrape_website(url: str, session: Session, current_user: User) -> WebsiteRead:
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            load_time = time.time() - start_time
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else "No title found"
            
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.decompose()
            
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_content = ' '.join(chunk for chunk in chunks if chunk)
            
            if len(clean_content) > 10000:
                clean_content = clean_content[:10000] + "... [content truncated]"
            
            word_count = len(clean_content.split())
            
            website = Website(
                base_url=url,
                title=title,
                user_id=current_user.id
            )
            session.add(website)
            session.commit()
            session.refresh(website)
            
            webpage = WebPage(
                url=url,
                title=title,
                scraped_content=clean_content,
                word_count=word_count,
                status_code=response.status_code,
                load_time=load_time,
                website_id=website.id
            )
            session.add(webpage)
            session.commit()
            
            return WebsiteRead(
                id=website.id,
                base_url=website.base_url,
                title=website.title,
                created_at=website.created_at,
                user_id=website.user_id
            )
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch website: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")