from sqlmodel import Session, select
from fastapi import HTTPException
from models.website import Website
from models.user import User
from typing import List
import requests
from bs4 import BeautifulSoup

class ScraperController:
    @staticmethod
    def scrape_website(url: str, session: Session, current_user: User) -> Website:
        """Scrape website content and store in database"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
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
            
            website = Website(
                url=url,
                title=title,
                scraped_content=clean_content,
                word_count=len(clean_content.split()),
                user_id=current_user.id
            )
            
            session.add(website)
            session.commit()
            session.refresh(website)
            
            return website
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch website: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")

    @staticmethod
    def get_websites(session: Session, current_user: User, offset: int = 0, limit: int = 100) -> List[Website]:
        """Get websites for current user only"""
        statement = select(Website).where(Website.user_id == current_user.id).offset(offset).limit(limit)
        websites = session.exec(statement).all()
        return websites

    @staticmethod
    def get_website(website_id: int, session: Session, current_user: User) -> Website:
        website = session.get(Website, website_id)
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        if website.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this website")
        
        return website

    @staticmethod
    def delete_website(website_id: int, session: Session, current_user: User) -> dict:
        website = session.get(Website, website_id)
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        if website.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this website")
        
        session.delete(website)
        session.commit()
        return {"message": "Website deleted successfully"}