from sqlmodel import Session, select
from fastapi import HTTPException
from typing import List, Set, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from models.website import Website, WebPage, WebsiteCreate, WebPageRead
from models.user import User
from controllers.sitemap_parser import SitemapParser
from config.ai_config import ImageConfig


class RecursiveCrawler:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.to_visit: List[str] = []
        self.max_pages = 50
        self.domain = ""
        
    @staticmethod
    def is_same_domain(url: str, base_domain: str) -> bool:
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc == base_domain
        except:
            return False
    
    @staticmethod
    def normalize_url(url: str) -> str:
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                url = 'https://' + url
                parsed = urlparse(url)
            
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                params = sorted(parsed.query.split('&'))
                normalized += '?' + '&'.join(params)
            return normalized.rstrip('/')
        except Exception as e:
            print(f"URL normalization failed for {url}: {str(e)}")
            return url
    
    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract all links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
                
            try:
                full_url = urljoin(base_url, href)
                normalized_url = self.normalize_url(full_url)
                
                if (self.is_same_domain(full_url, self.domain) and
                    normalized_url not in self.visited_urls and
                    normalized_url not in self.to_visit and
                    not any(ext in full_url.lower() for ext in ['.pdf', '.jpg', '.png', '.doc', '.docx', '.zip'])):
                    links.append(normalized_url)
            except Exception as e:
                print(f"Error processing link {href}: {str(e)}")
                continue
                
        return list(set(links))
    
    def check_broken_links(self, html_content: str, base_url: str) -> List[Dict]:
        """Check all links in content and identify broken ones (404/410)"""
        soup = BeautifulSoup(html_content, 'html.parser')
        broken_links = []
        checked_urls = set()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
                
            try:
                full_url = urljoin(base_url, href)
                
                if full_url in checked_urls:
                    continue
                checked_urls.add(full_url)
                
                try:
                    response = requests.head(full_url, headers=headers, timeout=5, allow_redirects=True)
                    status_code = response.status_code
                    
                    if status_code in [404, 410]:
                        broken_links.append({
                            'url': full_url,
                            'status_code': status_code,
                            'link_text': link.get_text(strip=True)[:100],
                            'found_on_page': base_url
                        })
                except requests.exceptions.RequestException as e:
                    broken_links.append({
                        'url': full_url,
                        'status_code': 0,
                        'error': str(e)[:100],
                        'link_text': link.get_text(strip=True)[:100],
                        'found_on_page': base_url
                    })
                    
                time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error checking link {href}: {str(e)}")
                continue
        
        return broken_links

    @staticmethod
    def check_image_dimensions(img_url: str, headers: dict) -> Dict:
        """
        Check image dimensions to determine if it's a banner.
        Returns: {'is_banner': bool, 'width': int, 'height': int}
        """
        try:
            from PIL import Image
            from io import BytesIO
            
            # Download image (limit to first 500KB to avoid huge downloads)
            response = requests.get(img_url, headers=headers, timeout=5, stream=True)
            response.raw.decode_content = True
            
            # Read only what we need
            img_data = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                img_data.write(chunk)
                if img_data.tell() > 500 * 1024:  # Stop after 500KB
                    break
            
            img_data.seek(0)
            img = Image.open(img_data)
            width, height = img.size
            
            # Check if it's a banner: width >= 1200 AND aspect ratio >= 2.5
            aspect_ratio = width / height if height > 0 else 0
            is_banner_by_dimensions = (width >= 1200) and (aspect_ratio >= 2.5)
            
            return {
                'is_banner': is_banner_by_dimensions,
                'width': width,
                'height': height,
                'aspect_ratio': round(aspect_ratio, 2)
            }
            
        except Exception as e:
            print(f"Could not check dimensions for {img_url}: {str(e)}")
            return {'is_banner': False, 'width': 0, 'height': 0, 'aspect_ratio': 0}

    @staticmethod
    def is_banner_image(img, img_url: str, file_size_kb: float, headers: dict) -> Dict:
        """
        Determine if image is a banner using multiple detection methods.
        Returns: {'is_banner': bool, 'detection_method': str, 'dimensions': dict}
        """
        # Method 1: Check keywords in filename/class
        img_src = img.get('src', '').lower()
        img_class = img.get('class', '')
        if isinstance(img_class, list):
            img_class = ' '.join(img_class)
        img_class = img_class.lower()
        
        banner_keywords = ['banner', 'hero', 'header', 'jumbotron', 'cover']
        
        if any(keyword in img_src for keyword in banner_keywords) or \
           any(keyword in img_class for keyword in banner_keywords):
            return {
                'is_banner': True,
                'detection_method': 'keyword',
                'dimensions': {}
            }
        
        # Method 2: Check file size heuristic (>800KB likely banner)
        if file_size_kb > 800:
            return {
                'is_banner': True,
                'detection_method': 'size_heuristic',
                'dimensions': {}
            }
        
        # Method 3: Check actual dimensions
        dim_check = RecursiveCrawler.check_image_dimensions(img_url, headers)
        if dim_check['is_banner']:
            return {
                'is_banner': True,
                'detection_method': 'dimensions',
                'dimensions': dim_check
            }
        
        return {
            'is_banner': False,
            'detection_method': 'none',
            'dimensions': dim_check if dim_check['width'] > 0 else {}
        }
    
    def check_large_images(self, html_content: str, base_url: str) -> List[Dict]:
        """
        Check all images with enhanced banner detection
        - Banner images: OK up to 2MB
        - Regular images: considered large if > 400KB
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        large_images = []
        checked_images = set()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for img in soup.find_all('img', src=True):
            img_url = img['src']
            
            try:
                full_img_url = urljoin(base_url, img_url)
                
                if full_img_url in checked_images:
                    continue
                checked_images.add(full_img_url)
                
                try:
                    response = requests.head(full_img_url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        content_length = response.headers.get('content-length')
                        
                        if content_length:
                            file_size_bytes = int(content_length)
                            file_size_kb = file_size_bytes / 1024
                            file_size_mb = file_size_kb / 1024
                            
                            # Use combined detection
                            banner_check = self.is_banner_image(img, full_img_url, file_size_kb, headers)
                            is_banner = banner_check['is_banner']
                            
                            # Apply thresholds based on image type
                            if is_banner:
                                # Banner: flag if > 2MB
                                if file_size_bytes > ImageConfig.BANNER_MAX_THRESHOLD_BYTES:
                                    image_filename = full_img_url.split('/')[-1].split('?')[0]
                                    
                                    large_images.append({
                                        'url': full_img_url,
                                        'filename': image_filename,
                                        'size_bytes': file_size_bytes,
                                        'size_kb': round(file_size_kb, 2),
                                        'size_mb': round(file_size_mb, 2),
                                        'alt_text': img.get('alt', 'No alt text')[:100],
                                        'found_on_page': base_url,
                                        'is_banner': True,
                                        'detection_method': banner_check['detection_method'],
                                        'dimensions': banner_check.get('dimensions', {}),
                                        'severity': 'critical',
                                        'threshold_type': 'banner',
                                        'max_allowed_kb': ImageConfig.BANNER_MAX_THRESHOLD_KB,
                                        'recommendation': f"Banner image exceeds 2MB limit ({file_size_kb:.1f}KB). Optimize to under 2MB.",
                                        'percentage_over': round((file_size_kb / ImageConfig.BANNER_MAX_THRESHOLD_KB) * 100, 0)
                                    })
                            else:
                                # Regular image: flag if > 400KB
                                if file_size_bytes > ImageConfig.REGULAR_LARGE_THRESHOLD_BYTES:
                                    image_filename = full_img_url.split('/')[-1].split('?')[0]
                                    
                                    large_images.append({
                                        'url': full_img_url,
                                        'filename': image_filename,
                                        'size_bytes': file_size_bytes,
                                        'size_kb': round(file_size_kb, 2),
                                        'size_mb': round(file_size_mb, 2),
                                        'alt_text': img.get('alt', 'No alt text')[:100],
                                        'found_on_page': base_url,
                                        'is_banner': False,
                                        'detection_method': banner_check['detection_method'],
                                        'dimensions': banner_check.get('dimensions', {}),
                                        'severity': 'critical',
                                        'threshold_type': 'regular',
                                        'max_allowed_kb': ImageConfig.REGULAR_LARGE_THRESHOLD_KB,
                                        'recommendation': f"Regular image exceeds 400KB limit ({file_size_kb:.1f}KB). Optimize to under 400KB.",
                                        'percentage_over': round((file_size_kb / ImageConfig.REGULAR_LARGE_THRESHOLD_KB) * 100, 0)
                                    })
                    
                    time.sleep(0.1)
                        
                except requests.exceptions.RequestException as e:
                    print(f"Error checking image {full_img_url}: {str(e)}")
                    continue
                    
            except Exception as e:
                print(f"Error processing image {img_url}: {str(e)}")
                continue
        
        large_images.sort(key=lambda x: x['size_bytes'], reverse=True)
        
        return large_images
    
    def scrape_page(self, url: str) -> Dict:
        try:
            start_time = time.time()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            load_time = time.time() - start_time
            
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                return {
                    'url': url,
                    'title': f"Non-HTML content: {content_type}",
                    'content': "",
                    'word_count': 0,
                    'status_code': response.status_code,
                    'load_time': load_time,
                    'links': [],
                    'broken_links': [],
                    'large_images': []
                }
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else "No title found"
            
            print(f"Checking broken links on {url}...")
            broken_links = self.check_broken_links(response.content, url)
            
            print(f"Checking images on {url} (thresholds: Regular: {ImageConfig.REGULAR_LARGE_THRESHOLD_KB}KB, Banner: {ImageConfig.BANNER_MAX_THRESHOLD_KB}KB)...")
            large_images = self.check_large_images(response.content, url)
            
            if large_images:
                banner_count = sum(1 for img in large_images if img['is_banner'])
                regular_count = sum(1 for img in large_images if not img['is_banner'])
                print(f"  Found {len(large_images)} large images: {banner_count} banners over 2MB, {regular_count} regular images over 400KB")
            
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.decompose()
            
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_content = ' '.join(chunk for chunk in chunks if chunk)
            
            if len(clean_content) > 10000:
                clean_content = clean_content[:10000] + "... [content truncated]"
            
            links = self.extract_links(response.content, url)
            
            return {
                'url': url,
                'title': title,
                'content': clean_content,
                'word_count': len(clean_content.split()),
                'status_code': response.status_code,
                'load_time': load_time,
                'links': links,
                'broken_links': broken_links,
                'large_images': large_images
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return {
                'url': url,
                'title': f"Error: {str(e)}",
                'content': "",
                'word_count': 0,
                'status_code': 0,
                'load_time': 0,
                'links': [],
                'broken_links': [],
                'large_images': []
            }
    
    def crawl_website(self, base_url: str, max_pages: int = 50) -> List[Dict]:
        self.max_pages = max_pages
        self.visited_urls.clear()
        self.to_visit.clear()
        
        base_url = self.normalize_url(base_url)
        parsed_base = urlparse(base_url)
        self.domain = parsed_base.netloc
        
        if not self.domain:
            raise ValueError(f"Invalid base URL: {base_url}")
        
        print(f"Starting crawl for domain: {self.domain}")
        print(f"Image thresholds: Regular images: {ImageConfig.REGULAR_LARGE_THRESHOLD_KB}KB, Banner images: {ImageConfig.BANNER_MAX_THRESHOLD_KB}KB")
        
        self.to_visit.append(base_url)
        scraped_pages = []
        
        try:
            sitemap_url = SitemapParser.find_sitemap_url(base_url)
            if sitemap_url:
                print(f"Found sitemap: {sitemap_url}")
                sitemap_urls = SitemapParser.parse_sitemap(sitemap_url)
                for url in sitemap_urls:
                    if self.is_same_domain(url, self.domain):
                        normalized = self.normalize_url(url)
                        if normalized not in self.visited_urls and normalized not in self.to_visit:
                            self.to_visit.append(normalized)
        except Exception as e:
            print(f"Sitemap processing failed: {str(e)}")
        
        while self.to_visit and len(self.visited_urls) < self.max_pages:
            current_url = self.to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            print(f"Crawling ({len(self.visited_urls)+1}/{self.max_pages}): {current_url}")
            page_data = self.scrape_page(current_url)
            self.visited_urls.add(current_url)
            
            scraped_pages.append(page_data)
            
            for link in page_data['links']:
                if link not in self.visited_urls and link not in self.to_visit:
                    self.to_visit.append(link)
            
            time.sleep(0.5)
        
        print(f"Crawling completed. Found {len(scraped_pages)} pages.")
        
        total_broken_links = sum(len(page['broken_links']) for page in scraped_pages)
        total_large_images = sum(len(page['large_images']) for page in scraped_pages)
        
        banner_images = sum(
            sum(1 for img in page['large_images'] if img['is_banner'])
            for page in scraped_pages
        )
        regular_images = sum(
            sum(1 for img in page['large_images'] if not img['is_banner'])
            for page in scraped_pages
        )
        
        print(f"Total broken links found: {total_broken_links}")
        print(f"Total large images found: {total_large_images}")
        print(f"  - Banner images over 2MB: {banner_images}")
        print(f"  - Regular images over 400KB: {regular_images}")
        
        return scraped_pages


class RecursiveCrawlerController:
    @staticmethod
    def crawl_website_recursive(website_data: WebsiteCreate, session: Session, current_user: User):
        try:
            crawler = RecursiveCrawler()
            
            website = Website(
                base_url=website_data.base_url,
                user_id=current_user.id
            )
            session.add(website)
            session.commit()
            session.refresh(website)
            
            scraped_pages = crawler.crawl_website(
                website_data.base_url,
                website_data.max_pages
            )
            
            stored_pages = []
            for page_data in scraped_pages:
                import json
                
                webpage = WebPage(
                    url=page_data['url'],
                    title=page_data['title'],
                    scraped_content=page_data['content'],
                    word_count=page_data['word_count'],
                    status_code=page_data['status_code'],
                    load_time=page_data['load_time'],
                    website_id=website.id,
                    broken_links_data=json.dumps(page_data['broken_links']),
                    large_images_data=json.dumps(page_data['large_images'])
                )
                session.add(webpage)
                stored_pages.append(webpage)
            
            session.commit()
            
            pages_data = []
            for page in stored_pages:
                session.refresh(page)
                pages_data.append(WebPageRead(
                    id=page.id,
                    url=page.url,
                    title=page.title,
                    scraped_content=page.scraped_content,
                    word_count=page.word_count,
                    grammar_score=page.grammar_score,
                    status_code=page.status_code,
                    load_time=page.load_time,
                    created_at=page.created_at
                ))
            
            return {
                "id": website.id,
                "base_url": website.base_url,
                "title": website.title,
                "created_at": website.created_at.isoformat(),
                "user_id": website.user_id,
                "page_count": len(stored_pages),
                "pages": pages_data
            }
            
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Recursive crawling failed: {str(e)}")