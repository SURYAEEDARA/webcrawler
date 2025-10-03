from sqlmodel import Session
from fastapi import HTTPException
from models.website import Website
from config.openai_config import get_openai_client
import tiktoken 

class AIController:
    @staticmethod
    def analyze_grammar(content: str) -> dict:
        """Analyze text grammar and provide suggestions using OpenAI"""
        try:
            client = get_openai_client()
            
            if len(content) > 12000:
                content = content[:12000] + "... [content truncated for analysis]"
            
            prompt = f"""
            Analyze the following text for grammar, spelling, punctuation, and style issues.
            Provide a comprehensive analysis with:
            1. Overall grammar score (0-100)
            2. List of specific issues found
            3. Specific improvement suggestions
            4. Revised version of problematic sections
            
            Text to analyze:
            {content}
            
            Format your response as:
            GRAMMAR_SCORE: [number]/100
            KEY_ISSUES: [bullet points]
            SUGGESTIONS: [bullet points]
            REVISED_EXAMPLES: [specific examples with corrections]
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert English grammar and writing style analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis_text = response.choices[0].message.content
            return AIController._parse_analysis_response(analysis_text)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    
    @staticmethod
    def _parse_analysis_response(response_text: str) -> dict:
        """Parse the AI response into structured data"""
        try:
            lines = response_text.split('\n')
            grammar_score = None
            key_issues = []
            suggestions = []
            revised_examples = []
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('GRAMMAR_SCORE:'):
                    try:
                        score_text = line.split(':')[1].split('/')[0].strip()
                        grammar_score = int(score_text)
                    except (ValueError, IndexError):
                        grammar_score = 0
                elif line.startswith('KEY_ISSUES:'):
                    current_section = 'issues'
                elif line.startswith('SUGGESTIONS:'):
                    current_section = 'suggestions'
                elif line.startswith('REVISED_EXAMPLES:'):
                    current_section = 'examples'
                elif line and current_section:
                    if line.startswith('- ') or line.startswith('• '):
                        line = line[2:].strip()
                    
                    if current_section == 'issues' and line:
                        key_issues.append(line)
                    elif current_section == 'suggestions' and line:
                        suggestions.append(line)
                    elif current_section == 'examples' and line:
                        revised_examples.append(line)
            
            return {
                "grammar_score": grammar_score or 0,
                "key_issues": key_issues,
                "suggestions": suggestions,
                "revised_examples": revised_examples,
                "full_analysis": response_text
            }
            
        except Exception as e:
            return {
                "grammar_score": 0,
                "key_issues": ["Analysis parsing failed"],
                "suggestions": ["Check the full analysis for details"],
                "revised_examples": [],
                "full_analysis": response_text
            }
    
    @staticmethod
    def analyze_website(website_id: int, session: Session) -> Website:
        """Analyze a website's content using AI"""
        website = session.get(Website, website_id)
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        if not website.scraped_content:
            raise HTTPException(status_code=400, detail="No content to analyze")
        
        analysis_result = AIController.analyze_grammar(website.scraped_content)
        
        website.grammar_score = analysis_result["grammar_score"]
        website.improvement_suggestions = "\n".join(analysis_result["suggestions"])
        website.analysis_result = analysis_result["full_analysis"]
        
        session.add(website)
        session.commit()
        session.refresh(website)
        
        return website