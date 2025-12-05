import re
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from config.database import get_session
from config.dependencies import get_current_active_user
from models.user import User
from models.website import Website, WebPage
from controllers.audit_controller import AuditController
from controllers.logger import AppLogger
from datetime import datetime
from config.ai_config import ImageConfig

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/website/{website_id}/json")
def export_website_json(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        website = session.get(Website, website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Website not found")
        
        statement = select(WebPage).where(WebPage.website_id == website_id)
        pages = session.exec(statement).all()
        
        audit_report = AuditController.generate_audit_report(website_id, session)
        
        all_broken_links = []
        all_large_images = []
        
        for page in pages:
            if page.broken_links_data:
                try:
                    page_broken_links = json.loads(page.broken_links_data)
                    for link in page_broken_links:
                        all_broken_links.append({
                            **link,
                            'page_id': page.id,
                            'page_url': page.url,
                            'page_title': page.title
                        })
                except json.JSONDecodeError:
                    pass
            
            if page.large_images_data:
                try:
                    page_large_images = json.loads(page.large_images_data)
                    for image in page_large_images:
                        all_large_images.append({
                            **image,
                            'page_id': page.id,
                            'page_url': page.url,
                            'page_title': page.title
                        })
                except json.JSONDecodeError:
                    pass
        
        banner_images = [img for img in all_large_images if img.get('is_banner')]
        regular_images = [img for img in all_large_images if not img.get('is_banner')]
        
        total_image_size_mb = sum(img.get('size_mb', 0) for img in all_large_images)
        
        export_data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "export_type": "comprehensive_website_analysis",
                "export_version": "2.1",
                "generated_by": "WebAnalyzer Platform"
            },
            "website": {
                "id": website.id,
                "base_url": website.base_url,
                "title": website.title,
                "created_at": website.created_at.isoformat(),
                "user_id": website.user_id
            },
            "audit_summary": {
                "website_id": audit_report.website_id if audit_report else None,
                "total_pages": audit_report.total_pages if audit_report else len(pages),
                "average_grammar_score": audit_report.average_grammar_score if audit_report else None,
                "overall_health_score": audit_report.overall_health_score if audit_report else None,
                "seo_score": audit_report.seo_score if audit_report else None,
                "accessibility_score": audit_report.accessibility_score if audit_report else None
            },
            "issues_summary": {
                "broken_links": {
                    "total_count": len(all_broken_links),
                    "pages_affected": len(set(link['page_id'] for link in all_broken_links)),
                    "by_status_code": {
                        "404": sum(1 for link in all_broken_links if link.get('status_code') == 404),
                        "410": sum(1 for link in all_broken_links if link.get('status_code') == 410),
                        "connection_errors": sum(1 for link in all_broken_links if link.get('status_code') == 0)
                    }
                },
                "large_images": {
                    "total_count": len(all_large_images),
                    "banner_images_over_2mb": len(banner_images),
                    "regular_images_over_400kb": len(regular_images),
                    "pages_affected": len(set(img['page_id'] for img in all_large_images)),
                    "total_size_mb": round(total_image_size_mb, 2),
                    "thresholds": {
                        "regular_image_limit_kb": ImageConfig.REGULAR_LARGE_THRESHOLD_KB,
                        "banner_image_limit_kb": ImageConfig.BANNER_MAX_THRESHOLD_KB,
                        "optimal_target_kb": ImageConfig.OPTIMAL_TARGET_KB
                    }
                }
            },
            "broken_links_detail": all_broken_links,
            "large_images_detail": all_large_images,
            "pages": [
                {
                    "id": page.id,
                    "url": page.url,
                    "title": page.title,
                    "scraped_content": page.scraped_content,
                    "content_preview": (page.scraped_content or '')[:500] + '...' if page.scraped_content and len(page.scraped_content) > 500 else page.scraped_content,
                    "word_count": page.word_count,
                    "character_count": len(page.scraped_content or ''),
                    "status_code": page.status_code,
                    "load_time": page.load_time,
                    "created_at": page.created_at.isoformat(),
                    "grammar_score": page.grammar_score,
                    "analysis_result": page.analysis_result,
                    "improvement_suggestions": page.improvement_suggestions,
                    "has_analysis": page.grammar_score is not None,
                    "issues_on_page": {
                        "broken_links_count": len([l for l in all_broken_links if l['page_id'] == page.id]),
                        "large_images_count": len([i for i in all_large_images if i['page_id'] == page.id])
                    },
                    "content_metrics": {
                        "readability_score": calculate_readability_score(page.scraped_content) if page.scraped_content else None,
                        "keyword_density": calculate_keyword_density(page.scraped_content) if page.scraped_content else {},
                        "content_categories": categorize_content(page.scraped_content) if page.scraped_content else []
                    }
                }
                for page in pages
            ],
            "recommendations": generate_recommendations(all_broken_links, all_large_images, pages),
            "export_settings": {
                "include_full_content": True,
                "include_ai_analysis": True,
                "include_issues_detail": True,
                "include_technical_metrics": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        logger._create_log(
            level="info",
            action="export_json_comprehensive",
            message=f"Exported comprehensive JSON for {website.base_url} - {len(all_broken_links)} broken links, {len(all_large_images)} large images",
            user_id=current_user.id,
            website_id=website_id
        )
        
        return JSONResponse(
            content=export_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=website_analysis_{website_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("export_json_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/website/{website_id}/report")
def export_website_report(
    website_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    logger = AppLogger(session)
    
    try:
        website = session.get(Website, website_id)
        if not website or website.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Website not found")
        
        statement = select(WebPage).where(WebPage.website_id == website_id)
        pages = session.exec(statement).all()
        
        all_broken_links = []
        all_large_images = []
        
        for page in pages:
            if page.broken_links_data:
                try:
                    page_broken_links = json.loads(page.broken_links_data)
                    for link in page_broken_links:
                        all_broken_links.append({**link, 'page_title': page.title, 'page_url': page.url})
                except json.JSONDecodeError:
                    pass
            
            if page.large_images_data:
                try:
                    page_large_images = json.loads(page.large_images_data)
                    for img in page_large_images:
                        all_large_images.append({**img, 'page_title': page.title, 'page_url': page.url})
                except json.JSONDecodeError:
                    pass
        
        analyzed_pages = [p for p in pages if p.grammar_score is not None]
        average_score = round(sum(p.grammar_score for p in analyzed_pages) / len(analyzed_pages), 2) if analyzed_pages else None
        
        banner_images = [img for img in all_large_images if img.get('is_banner')]
        regular_images = [img for img in all_large_images if not img.get('is_banner')]
        
        broken_links_section = ""
        if all_broken_links:
            broken_links_section = f"""
BROKEN LINKS REPORT ({len(all_broken_links)} total):
{'='*80}

Critical Issues Found:
- 404 Not Found: {sum(1 for l in all_broken_links if l.get('status_code') == 404)}
- 410 Gone: {sum(1 for l in all_broken_links if l.get('status_code') == 410)}
- Connection Errors: {sum(1 for l in all_broken_links if l.get('status_code') == 0)}

Detailed Broken Links:
"""
            for i, link in enumerate(all_broken_links[:50], 1):  
                broken_links_section += f"""
{i}. [{link.get('status_code', 'ERROR')}] {link.get('url', 'Unknown URL')}
   Link Text: "{link.get('link_text', 'N/A')[:100]}"
   Found on: {link.get('page_title', 'Unknown')} ({link.get('page_url', 'N/A')})
"""
            if len(all_broken_links) > 50:
                broken_links_section += f"\n... and {len(all_broken_links) - 50} more broken links (see JSON export for full list)\n"
        else:
            broken_links_section = f"""
BROKEN LINKS REPORT:
{'='*80}
✓ No broken links found! All links are working properly.
"""
        
        large_images_section = ""
        if all_large_images:
            total_size_mb = sum(img.get('size_mb', 0) for img in all_large_images)
            
            large_images_section = f"""
LARGE IMAGES REPORT ({len(all_large_images)} total):
{'='*80}

Image Size Analysis:
- Banner images over 2MB: {len(banner_images)} images
- Regular images over 400KB: {len(regular_images)} images
- Total Size: {total_size_mb:.2f} MB
"""
            if banner_images:
                large_images_section += "\nBANNER IMAGES (over 2MB limit):\n"
                for i, img in enumerate(banner_images[:30], 1):
                    large_images_section += f"""
{i}. 🚨 {img.get('filename', 'Unknown')} - {img.get('size_kb', 0):.1f} KB ({img.get('percentage_over', 0):.0f}% over 2MB limit)
   Recommendation: {img.get('recommendation', 'Optimize this banner image')}
   Location: {img.get('page_title', 'Unknown')}
   URL: {img.get('url', 'N/A')}
"""
            
            if regular_images:
                large_images_section += f"\nREGULAR IMAGES (over 400KB limit):\n"
                for i, img in enumerate(regular_images[:20], 1):
                    large_images_section += f"""
{i}. ⚠️ {img.get('filename', 'Unknown')} - {img.get('size_kb', 0):.1f} KB ({img.get('percentage_over', 0):.0f}% over 400KB limit)
   Recommendation: {img.get('recommendation', 'Optimize this image')}
   Location: {img.get('page_title', 'Unknown')}
"""
        else:
            large_images_section = f"""
LARGE IMAGES REPORT:
{'='*80}
✓ No large images found! All images are properly sized.
• Banner images under 2MB ✓
• Regular images under 400KB ✓
"""
        
        report_text = f"""
{'='*80}
COMPREHENSIVE WEBSITE AUDIT REPORT
{'='*80}

WEBSITE INFORMATION:
- URL: {website.base_url}
- Title: {website.title or 'No title available'}
- Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Total Pages Crawled: {len(pages)}

EXECUTIVE SUMMARY:
{'='*80}
Overall Quality Score: {average_score or 'N/A'} / 100
Pages Analyzed: {len(analyzed_pages)} of {len(pages)}

ISSUES OVERVIEW:
- Broken Links: {len(all_broken_links)} {'NEEDS ATTENTION' if all_broken_links else '✓ None'}
- Large Images: {len(all_large_images)} ({len(banner_images)} banners over 2MB, {len(regular_images)} regular over 400KB)
  {'NEEDS OPTIMIZATION' if all_large_images else '✓ All optimized'}

{broken_links_section}

{large_images_section}

CONTENT QUALITY ANALYSIS:
{'='*80}
Grammar & Content Scores by Page:
"""
        
        for page in pages:
            status = "✓ Analyzed" if page.grammar_score else "⏳ Pending"
            score_display = f"Score: {page.grammar_score}" if page.grammar_score else "Not analyzed"
            issues_count = len([l for l in all_broken_links if l.get('page_url') == page.url]) + \
                          len([i for i in all_large_images if i.get('page_url') == page.url])
            issues_marker = f" | {issues_count} issues" if issues_count > 0 else ""
            
            report_text += f"\n- {page.url} | {status} | {score_display}{issues_marker}"
        
        recommendations = generate_recommendations(all_broken_links, all_large_images, pages)
        
        report_text += f"""

KEY RECOMMENDATIONS:
{'='*80}
{chr(10).join(f"{i+1}. {rec}" for i, rec in enumerate(recommendations))}

ACTION PLAN:
{'='*80}
Priority 1 - Critical Issues:
{f"• Fix {len(all_broken_links)} broken links to restore user experience" if all_broken_links else "✓ No broken links"}
{f"• Optimize {len(banner_images)} banner images over 2MB" if banner_images else "✓ Banner images optimized"}
{f"• Optimize {len(regular_images)} regular images over 400KB" if regular_images else "✓ Regular images optimized"}

Priority 2 - Performance Optimization:
• Analyze {len(pages) - len(analyzed_pages)} pending pages for content quality

Priority 3 - Ongoing Monitoring:
• Re-run audit after implementing fixes
• Monitor for new broken links and oversized images
• Maintain content quality scores above 80

IMAGE OPTIMIZATION GUIDELINES:
{'='*80}
• Banner images: Should be under 2MB (ideally 500KB-1MB)
• Regular images: Should be under 400KB (ideally under 100KB)

Recommended optimization tools:
- TinyPNG (tinypng.com) - Lossy compression, excellent results
- ImageOptim (imageoptim.com) - Lossless compression for Mac
- Squoosh (squoosh.app) - Google's web-based optimizer
- WebP Converter - Convert to modern formats for better compression

---
Report Generated by: WebAnalyzer AI Platform
Export Timestamp: {datetime.now().isoformat()}
        """.strip()
        
        logger._create_log(
            level="info",
            action="export_comprehensive_report",
            message=f"Generated comprehensive report for {website.base_url}",
            user_id=current_user.id,
            website_id=website_id
        )
        
        return JSONResponse(
            content={"report": report_text},
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error("export_report_error", str(e), current_user.id)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


def generate_recommendations(broken_links: list, large_images: list, pages: list) -> list:
    """Generate specific, actionable recommendations based on actual findings"""
    recommendations = []
    
    if broken_links:
        recommendations.append(f"URGENT: Fix {len(broken_links)} broken links - these harm SEO and user experience")
        
        by_status = {}
        for link in broken_links:
            status = link.get('status_code', 0)
            by_status[status] = by_status.get(status, 0) + 1
        
        for status, count in by_status.items():
            if status == 404:
                recommendations.append(f"  • {count} links return 404 Not Found - verify URLs or remove links")
            elif status == 410:
                recommendations.append(f"  • {count} links return 410 Gone - remove these permanently deleted resources")
            elif status == 0:
                recommendations.append(f"  • {count} links have connection errors - check for SSL or DNS issues")
    
    banner_images = [img for img in large_images if img.get('is_banner')]
    regular_images = [img for img in large_images if not img.get('is_banner')]
    
    if banner_images:
        total_size = sum(img.get('size_mb', 0) for img in banner_images)
        recommendations.append(f"Optimize {len(banner_images)} banner images over 2MB limit (total: {total_size:.1f}MB)")
        recommendations.append(f"  • Banner images should be under 2MB for optimal loading")
    
    if regular_images:
        total_size = sum(img.get('size_mb', 0) for img in regular_images)
        recommendations.append(f"Optimize {len(regular_images)} regular images over 400KB limit (total: {total_size:.1f}MB)")
        recommendations.append(f"  • Regular images should be under 400KB for optimal performance")
    
    analyzed_pages = [p for p in pages if p.grammar_score is not None]
    if analyzed_pages:
        low_scoring = [p for p in analyzed_pages if p.grammar_score < 70]
        if low_scoring:
            recommendations.append(f"Improve content quality on {len(low_scoring)} pages with scores below 70")
    
    pending_pages = len(pages) - len(analyzed_pages)
    if pending_pages > 0:
        recommendations.append(f"Run grammar analysis on {pending_pages} remaining pages")
    
    if not recommendations:
        recommendations = [
            "✓ Website is in excellent condition!",
            "• All links are working properly",
            "• All images are optimized",
            "• Content quality is good",
            "• Continue monitoring with regular audits"
        ]
    
    return recommendations


def calculate_readability_score(content: str = '') -> float:
    if not content:
        return 0
    try:
        words = content.split()
        sentences = content.split('.')
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        readability = max(0, 100 - (avg_sentence_length * 0.5 + avg_word_length * 2))
        return round(readability, 2)
    except:
        return 0


def calculate_keyword_density(content: str = '') -> dict:
    if not content:
        return {}
    
    from collections import Counter
    import re
    
    words = re.findall(r'\b\w+\b', content.lower())
    word_counts = Counter(words)
    total_words = len(words)
    
    common_keywords = ['website', 'content', 'page', 'analysis', 'quality', 'seo', 'accessibility']
    densities = {}
    
    for keyword in common_keywords:
        if keyword in word_counts:
            density = (word_counts[keyword] / total_words) * 100
            densities[keyword] = round(density, 4)
    
    return densities


def categorize_content(content: str = '') -> list:
    if not content:
        return []
    
    content_lower = content.lower()
    categories = []
    
    if any(word in content_lower for word in ['product', 'service', 'buy', 'purchase']):
        categories.append("commercial")
    if any(word in content_lower for word in ['about', 'company', 'team', 'mission']):
        categories.append("informational")
    if any(word in content_lower for word in ['blog', 'article', 'news', 'update']):
        categories.append("blog_content")
    if any(word in content_lower for word in ['contact', 'email', 'phone', 'address']):
        categories.append("contact")
    
    return categories if categories else ["general"]