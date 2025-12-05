import requests
from typing import List, Dict
from urllib.parse import urljoin
from fastapi import HTTPException

class ImageAnalyzer:
    @staticmethod
    def analyze_single_image(image_url: str, base_url: str = "") -> Dict:
        try:
            if not image_url.startswith(('http://', 'https://')):
                image_url = urljoin(base_url, image_url)
            
            response = requests.head(image_url, timeout=10)
            
            analysis = {
                "url": image_url,
                "accessible": response.status_code == 200,
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type', ''),
                "issues": []
            }
            
            if response.status_code == 200:
                content_length = response.headers.get('content-length')
                if content_length:
                    file_size_kb = int(content_length) / 1024
                    analysis["file_size_kb"] = round(file_size_kb, 2)
                    
                    if file_size_kb > 500:
                        analysis["issues"].append(f"Large file size: {file_size_kb:.1f}KB")
                
                content_type = response.headers.get('content-type', '').lower()
                if 'image/' not in content_type:
                    analysis["issues"].append("Not an image file")
                    analysis["accessible"] = False
            
            else:
                analysis["issues"].append(f"HTTP Error: {response.status_code}")
            
            return analysis
            
        except requests.exceptions.RequestException as e:
            return {
                "url": image_url,
                "accessible": False,
                "issues": [f"Connection error: {str(e)}"]
            }

    @staticmethod
    def analyze_multiple_images(image_urls: List[str], base_url: str = "") -> Dict:
        results = []
        problematic_images = []
        
        for image_url in image_urls:
            result = ImageAnalyzer.analyze_single_image(image_url, base_url)
            results.append(result)
            
            if result["issues"] or not result["accessible"]:
                problematic_images.append(result)
        
        return {
            "total_images": len(image_urls),
            "problematic_images": problematic_images,
            "accessible_images": [r for r in results if r["accessible"] and not r["issues"]],
            "problematic_count": len(problematic_images),
            "accessibility_score": round((len(image_urls) - len(problematic_images)) / len(image_urls) * 100, 2) if image_urls else 0
        }