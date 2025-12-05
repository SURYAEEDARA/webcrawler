import requests
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree
from typing import List

class SitemapParser:
    @staticmethod
    def parse_sitemap(sitemap_url: str) -> List[str]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(sitemap_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            urls = []
            root = ElementTree.fromstring(response.content)
            
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            for url_elem in root.findall('ns:url', namespaces):
                loc_elem = url_elem.find('ns:loc', namespaces)
                if loc_elem is not None and loc_elem.text:
                    urls.append(loc_elem.text.strip())
            
            return urls
            
        except Exception as e:
            print(f"Sitemap parsing failed: {str(e)}")
            return []

    @staticmethod
    def find_sitemap_url(base_url: str) -> str:
        common_locations = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap.php',
            '/sitemap.txt'
        ]
        
        for location in common_locations:
            sitemap_url = urljoin(base_url, location)
            try:
                response = requests.head(sitemap_url, timeout=5)
                if response.status_code == 200:
                    return sitemap_url
            except:
                continue
                
        return None