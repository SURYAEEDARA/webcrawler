from fastapi import HTTPException
from config.ai_config import AIConfig
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class AIController:
    def __init__(self):
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        print(f"AI controller initialized with model: {AIConfig.HF_MODEL}")
        if self.api_token:
            print(f"Hugging Face API token found: {self.api_token[:10]}...")
        else:
            print("Hugging Face API token not found")
    
    def analyze_grammar(self, content: str):
        if not self.api_token:
            raise HTTPException(
                status_code=503, 
                detail="Hugging Face API token not configured."
            )
        
        try:
            if len(content) > AIConfig.MAX_CONTENT_LENGTH:
                content = content[:AIConfig.MAX_CONTENT_LENGTH] + "..."
            
            system_prompt = """You are an expert content quality analyst specializing in web content, grammar, readability, and SEO best practices. 

Analyze the provided website content and respond in this EXACT format:

SCORE: [number from 0-100]

GRAMMAR & STYLE ISSUES:
1. [Specific grammar, punctuation, or style issue with example]
2. [Specific grammar, punctuation, or style issue with example]
3. [Specific grammar, punctuation, or style issue with example]

READABILITY ISSUES:
1. [Specific readability concern]
2. [Specific readability concern]

SEO & CONTENT ISSUES:
1. [Specific SEO or content structure issue]
2. [Specific SEO or content structure issue]

SUGGESTIONS:
1. [Specific, actionable improvement with example]
2. [Specific, actionable improvement with example]
3. [Specific, actionable improvement with example]
4. [Specific, actionable improvement with example]
5. [Specific, actionable improvement with example]

Scoring guide:
95-100: Perfect professional content
85-94: Excellent with minor polish needed
75-84: Good quality, some improvements recommended
60-74: Acceptable but needs work
40-59: Poor quality, major revisions needed
0-39: Very poor, complete rewrite required

Be specific! Quote actual text when mentioning issues."""
            
            user_prompt = f"Analyze this website content for quality, grammar, readability, and SEO:\n\n{content}"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": AIConfig.HF_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 1000, 
                "temperature": 0.3,
                "top_p": 0.9
            }
            
            print(f"Calling HF Inference Providers API...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Hugging Face token. Check your HF_TOKEN or HUGGINGFACE_API_TOKEN."
                )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model '{AIConfig.HF_MODEL}' not available. Use a model from Inference Providers."
                )
            
            if response.status_code == 503:
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable. Please try again in a moment."
                )
            
            if response.status_code != 200:
                error_msg = response.text[:300]
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"HF API error: {error_msg}"
                )
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                analysis_text = result["choices"][0]["message"]["content"]
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected response format: {str(result)[:200]}"
                )
            
            analysis_text = self._clean_response(analysis_text)
            
            return {
                "success": True,
                "analysis": analysis_text,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
            
        except HTTPException:
            raise
        except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=504, 
                detail="Request timeout. Please try again."
            )
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Connection error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Analysis failed: {str(e)}"
            )
    
    def _clean_response(self, text: str) -> str:
        import re
        
        text = re.sub(r'\*\*🤔.*?\*\*', '', text, flags=re.DOTALL)
        text = re.sub(r'\*\*Analysis:\*\*', '', text)
        text = re.sub(r'\*\*💬 Response:\*\*', '', text)
        text = text.split("---")[-1]
        
        if "SCORE:" in text.upper():
            match = re.search(r'SCORE:', text, re.IGNORECASE)
            if match:
                text = text[match.start():]
        
        return text.strip()
    
    def analyze_seo(self, content: str):
        seo_prompt = f"""Analyze this content for SEO optimization:
    {content}

    Provide SEO score (0-100) and specific recommendations for:
    - Meta tags optimization
    - Keyword usage and density
    - Content structure and headings
    - Internal linking opportunities
    - Mobile responsiveness issues

    Format:
    SEO_SCORE: [0-100]
    RECOMMENDATIONS:
    1. [Specific SEO recommendation]
    2. [Specific SEO recommendation]
    3. [Specific SEO recommendation]"""
        
        return self.analyze_with_prompt(content, seo_prompt)

    def analyze_accessibility(self, content: str):
        accessibility_prompt = f"""Analyze this content for accessibility:
    {content}

    Provide accessibility score (0-100) and specific recommendations for:
    - Screen reader compatibility
    - Color contrast issues
    - Semantic HTML structure
    - Keyboard navigation
    - Alt text for images

    Format:
    ACCESSIBILITY_SCORE: [0-100]
    RECOMMENDATIONS:
    1. [Specific accessibility recommendation]
    2. [Specific accessibility recommendation]
    3. [Specific accessibility recommendation]"""
        
        return self.analyze_with_prompt(content, accessibility_prompt)

    def analyze_with_prompt(self, content: str, prompt: str):
        if not self.api_token:
            raise HTTPException(status_code=503, detail="AI service not available")
        
        try:
            if len(content) > AIConfig.MAX_CONTENT_LENGTH:
                content = content[:AIConfig.MAX_CONTENT_LENGTH] + "..."
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": AIConfig.HF_MODEL,  
                "messages": [
                    {"role": "system", "content": "You are a web content analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            analysis_text = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "analysis": analysis_text,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

ai_controller = AIController()