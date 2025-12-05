import requests
from typing import List, Dict
from urllib.parse import urljoin
from fastapi import HTTPException

class LinkChecker:
    @staticmethod
    def check_single_link(url: str, base_url: str = "") -> Dict:
        try:
            if not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "working": response.status_code < 400,
                "final_url": str(response.url),
                "redirected": len(response.history) > 0
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "status_code": 0,
                "working": False,
                "error": str(e)
            }

    @staticmethod
    def check_multiple_links(links: List[str], base_url: str = "") -> Dict:
        results = []
        broken_links = []
        
        for link in links:
            result = LinkChecker.check_single_link(link, base_url)
            results.append(result)
            
            if not result["working"]:
                broken_links.append(result)
        
        return {
            "total_links": len(links),
            "broken_links": broken_links,
            "working_links": [r for r in results if r["working"]],
            "broken_count": len(broken_links),
            "health_score": round((len(links) - len(broken_links)) / len(links) * 100, 2) if links else 0
        }