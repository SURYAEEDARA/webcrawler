import React, { useState, useEffect } from 'react';
import type { WebPage, CrawledWebsite, AuditSummary } from '../services/api';
import { apiService } from '../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import IssuesSection from './IssuesSection';

interface EnhancedWebPage extends WebPage {
  content_metrics?: {
    readability_score?: number;
    keyword_density?: Record<string, number>;
    content_categories?: string[];
  };
  scraped_content_preview?: string;
}

interface WebsiteAnalysis {
  id: number;
  base_url: string;
  title?: string;
  created_at: string;
  user_id: number;
  page_count: number;
  pages: EnhancedWebPage[];
  audit_summary?: AuditSummary;
}

const HistorySection: React.FC = () => {
  const [websites, setWebsites] = useState<WebsiteAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [analyzingPages, setAnalyzingPages] = useState<Set<number>>(new Set());
  const [analyzingWebsites, setAnalyzingWebsites] = useState<Set<number>>(new Set());
  const [expandedWebsite, setExpandedWebsite] = useState<number | null>(null);
  const [expandedPage, setExpandedPage] = useState<number | null>(null);
  const [showFullContent, setShowFullContent] = useState<Set<number>>(new Set());
  const [selectedWebsiteForIssues, setSelectedWebsiteForIssues] = useState<number | null>(null);

  useEffect(() => {
    loadWebsites();
  }, []);

  const loadWebsites = async () => {
    try {
      setLoading(true);
      setError('');
      const crawledResults = await apiService.getCrawledWebsites();
      console.log('Crawled websites:', crawledResults);
     
      const websitesWithFullData: WebsiteAnalysis[] = await Promise.all(
        crawledResults.map(async (website: CrawledWebsite) => {
          let auditSummary: AuditSummary | undefined;
         
          try {
            auditSummary = await apiService.getAuditReport(website.id);
            console.log(`Audit summary for website ${website.id}:`, auditSummary);
          } catch (error) {
            console.warn(`Audit not found for website ${website.id}, generating new one...`);
            try {
              auditSummary = await apiService.regenerateAuditReport(website.id);
              console.log(`Generated new audit for website ${website.id}:`, auditSummary);
            } catch (genError) {
              console.error(`Could not generate audit for ${website.id}:`, genError);
            }
          }
         
          const enhancedPages: EnhancedWebPage[] = await Promise.all(
            website.pages.map(async (page: WebPage) => {
              let fullAnalysis: any = null;
             
              if (page.grammar_score !== undefined && page.grammar_score !== null) {
                try {
                  fullAnalysis = await apiService.getFullAnalysis(page.id);
                  console.log(`Full analysis for page ${page.id}:`, fullAnalysis);
                } catch (error) {
                  console.warn(`Could not load full analysis for page ${page.id}:`, error);
                }
              }
             
              return {
                ...page,
                analysis_result: fullAnalysis?.full_analysis || page.analysis_result,
                improvement_suggestions: fullAnalysis?.suggestions || page.improvement_suggestions,
                scraped_content_preview: page.scraped_content ?
                  page.scraped_content.substring(0, 500) + (page.scraped_content.length > 500 ? '...' : '') : '',
                content_metrics: {
                  readability_score: calculateReadabilityScore(page.scraped_content),
                  keyword_density: calculateKeywordDensity(page.scraped_content),
                  content_categories: categorizeContent(page.scraped_content)
                }
              };
            })
          );

          return {
            ...website,
            pages: enhancedPages,
            audit_summary: auditSummary
          };
        })
      );

      console.log('Final websites with full data:', websitesWithFullData);
      setWebsites(websitesWithFullData);
    } catch (err: any) {
      console.error('Load error:', err);
      setError(err.message || 'Failed to load websites');
    } finally {
      setLoading(false);
    }
  };

  const calculateReadabilityScore = (content: string = '') => {
    if (!content) return 0;
    const words = content.split(' ');
    const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const avgSentenceLength = words.length / (sentences.length || 1);
    const avgWordLength = words.reduce((sum, word) => sum + word.length, 0) / (words.length || 1);
   
    const score = Math.max(0, 100 - (avgSentenceLength * 0.5 + avgWordLength * 2));
    return Math.round(score);
  };

  const calculateKeywordDensity = (content: string = '') => {
    if (!content) return {};
    const words = content.toLowerCase().match(/\b\w+\b/g) || [];
    const totalWords = words.length;
    if (totalWords === 0) return {};
   
    const commonKeywords = ['website', 'content', 'page', 'analysis', 'quality', 'seo', 'accessibility'];
    const densities: Record<string, number> = {};
   
    commonKeywords.forEach(keyword => {
      const count = words.filter(word => word === keyword).length;
      if (count > 0) {
        densities[keyword] = Math.round((count / totalWords) * 10000) / 100;
      }
    });
   
    return densities;
  };

  const categorizeContent = (content: string = '') => {
    if (!content) return ['general'];
    const contentLower = content.toLowerCase();
    const categories = [];
   
    if (contentLower.includes('product') || contentLower.includes('service') || contentLower.includes('buy') || contentLower.includes('purchase')) {
      categories.push('commercial');
    }
    if (contentLower.includes('about') || contentLower.includes('company') || contentLower.includes('team') || contentLower.includes('mission')) {
      categories.push('informational');
    }
    if (contentLower.includes('blog') || contentLower.includes('article') || contentLower.includes('news') || contentLower.includes('update')) {
      categories.push('blog');
    }
    if (contentLower.includes('contact') || contentLower.includes('email') || contentLower.includes('phone') || contentLower.includes('address')) {
      categories.push('contact');
    }
   
    return categories.length > 0 ? categories : ['general'];
  };

  const handleAnalyzePage = async (pageId: number) => {
    try {
      setError('');
      setAnalyzingPages(prev => new Set(prev).add(pageId));
      await apiService.analyzePage(pageId);
      await loadWebsites();
    } catch (err: any) {
      setError(err.message || 'Failed to analyze page. Please try again.');
    } finally {
      setAnalyzingPages(prev => {
        const newSet = new Set(prev);
        newSet.delete(pageId);
        return newSet;
      });
    }
  };

  const handleAnalyzeWebsite = async (websiteId: number) => {
    try {
      setError('');
      setAnalyzingWebsites(prev => new Set(prev).add(websiteId));
      await apiService.analyzeWebsite(websiteId);
      await loadWebsites();
    } catch (err: any) {
      setError(err.message || 'Failed to analyze website. Please try again.');
    } finally {
      setAnalyzingWebsites(prev => {
        const newSet = new Set(prev);
        newSet.delete(websiteId);
        return newSet;
      });
    }
  };

  const toggleFullContent = (pageId: number) => {
    setShowFullContent(prev => {
      const newSet = new Set(prev);
      if (newSet.has(pageId)) {
        newSet.delete(pageId);
      } else {
        newSet.add(pageId);
      }
      return newSet;
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreVariant = (score: number) => {
    if (score >= 80) return "default";
    if (score >= 60) return "secondary";
    return "destructive";
  };

  const getScoreText = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  const getAnalyzedPagesCount = (website: WebsiteAnalysis) => {
    return website.pages?.filter(page => page.grammar_score !== undefined && page.grammar_score !== null).length || 0;
  };

  const toggleWebsiteExpansion = (websiteId: number) => {
    setExpandedWebsite(expandedWebsite === websiteId ? null : websiteId);
  };

  const togglePageExpansion = (pageId: number) => {
    setExpandedPage(expandedPage === pageId ? null : pageId);
  };

  const toggleIssuesSection = (websiteId: number) => {
    setSelectedWebsiteForIssues(selectedWebsiteForIssues === websiteId ? null : websiteId);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Comprehensive Analysis History</CardTitle>
          <CardDescription>Loading your complete website analyses...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">Loading comprehensive analysis data...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Comprehensive Analysis History</CardTitle>
        <CardDescription>Detailed view of all website analyses with complete metrics and insights</CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <div className="space-y-6">
          {websites.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed rounded-lg">
              <div className="text-muted-foreground">
                No website analyses yet. Analyze a website to see comprehensive results here.
              </div>
            </div>
          ) : (
            websites.map((website) => (
              <Card key={website.id} className="bg-muted/50">
                <CardContent className="p-6">
                  {/* Website Header */}
                  <div className="flex justify-between items-start mb-6">
                    <div className="flex-1">
                      <h3 className="font-semibold text-xl mb-2 break-all">
                        {website.title || website.base_url}
                      </h3>
                      <p className="text-sm text-muted-foreground break-all mb-3">
                        {website.base_url}
                      </p>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>Analyzed: {formatDate(website.created_at)}</span>
                        <span>•</span>
                        <span>{website.page_count} total pages</span>
                        <span>•</span>
                        <span>{getAnalyzedPagesCount(website)} analyzed</span>
                      </div>
                    </div>
                    <div className="flex gap-3 flex-wrap justify-end">
                      <Button
                        onClick={() => toggleWebsiteExpansion(website.id)}
                        variant="outline"
                        size="sm"
                      >
                        {expandedWebsite === website.id ? 'Collapse' : 'Expand All'}
                      </Button>
                      <Button
                        onClick={() => handleAnalyzeWebsite(website.id)}
                        disabled={analyzingWebsites.has(website.id)}
                        size="sm"
                      >
                        {analyzingWebsites.has(website.id) ? (
                          <>
                            <div className="mr-2 h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                            Analyzing...
                          </>
                        ) : (
                          'Re-analyze All'
                        )}
                      </Button>
                      <Button
                        onClick={() => toggleIssuesSection(website.id)}
                        variant={selectedWebsiteForIssues === website.id ? "default" : "secondary"}
                        size="sm"
                        className="min-w-[120px]"
                      >
                        {selectedWebsiteForIssues === website.id ? '✓ Hide Issues' : '⚠️ View Issues'}
                      </Button>
                    </div>
                  </div>

                  {/* Website Summary Metrics */}
                  {website.audit_summary && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <Card className="text-center">
                        <CardContent className="p-4">
                          <div className="text-2xl font-bold text-blue-600">
                            {website.audit_summary.overall_health_score || 'N/A'}
                          </div>
                          <div className="text-xs text-muted-foreground">Overall Score</div>
                        </CardContent>
                      </Card>
                      <Card className="text-center">
                        <CardContent className="p-4">
                          <div className="text-2xl font-bold text-green-600">
                            {website.audit_summary.average_grammar_score || 'N/A'}
                          </div>
                          <div className="text-xs text-muted-foreground">Grammar Score</div>
                        </CardContent>
                      </Card>
                      <Card className="text-center">
                        <CardContent className="p-4">
                          <div className="text-2xl font-bold text-purple-600">
                            {website.audit_summary.seo_score || 'N/A'}
                          </div>
                          <div className="text-xs text-muted-foreground">SEO Score</div>
                        </CardContent>
                      </Card>
                      <Card className="text-center">
                        <CardContent className="p-4">
                          <div className="text-2xl font-bold text-orange-600">
                            {website.audit_summary.accessibility_score || 'N/A'}
                          </div>
                          <div className="text-xs text-muted-foreground">Accessibility</div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {/* Issues Section - NEW */}
                  {selectedWebsiteForIssues === website.id && (
                    <div className="mb-6 border-t pt-6">
                      <IssuesSection 
                        websiteId={website.id} 
                        websiteName={website.base_url}
                      />
                    </div>
                  )}

                  {/* Individual Pages */}
                  {expandedWebsite === website.id && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-lg mb-4">Individual Page Analysis</h4>
                      {website.pages?.map((page) => (
                        <Card key={page.id} className="bg-background">
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start mb-3">
                              <div className="flex-1">
                                <h5 className="font-medium text-lg mb-1">{page.title || 'No Title'}</h5>
                                <p className="text-sm text-muted-foreground break-all mb-2">{page.url}</p>
                                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                  <span>{page.word_count || 0} words</span>
                                  <span>•</span>
                                  <span>{page.load_time ? `${page.load_time.toFixed(2)}s` : 'N/A'}</span>
                                  <span>•</span>
                                  <span>{page.status_code || 'N/A'} status</span>
                                </div>
                              </div>
                              <div className="flex gap-2 items-center">
                                {page.grammar_score !== undefined && page.grammar_score !== null ? (
                                  <Badge
                                    variant={getScoreVariant(page.grammar_score)}
                                    className="text-sm px-3 py-1"
                                  >
                                    {page.grammar_score} - {getScoreText(page.grammar_score)}
                                  </Badge>
                                ) : (
                                  <Button
                                    onClick={() => handleAnalyzePage(page.id)}
                                    disabled={analyzingPages.has(page.id)}
                                    size="sm"
                                  >
                                    {analyzingPages.has(page.id) ? 'Analyzing...' : 'Analyze'}
                                  </Button>
                                )}
                                <Button
                                  onClick={() => togglePageExpansion(page.id)}
                                  variant="outline"
                                  size="sm"
                                >
                                  {expandedPage === page.id ? 'Hide' : 'Show'}
                                </Button>
                              </div>
                            </div>

                            {/* Expanded Page Details */}
                            {expandedPage === page.id && (
                              <div className="mt-4 space-y-4 border-t pt-4">
                                {/* Scraped Content */}
                                {page.scraped_content && (
                                  <div>
                                    <h6 className="font-medium mb-2">Scraped Content</h6>
                                    <div className="text-sm bg-gray-50 p-3 rounded border">
                                      {showFullContent.has(page.id) ? (
                                        <div className="whitespace-pre-wrap max-h-96 overflow-y-auto">
                                          {page.scraped_content}
                                          <Button
                                            onClick={() => toggleFullContent(page.id)}
                                            variant="link"
                                            className="mt-2 p-0 h-auto"
                                          >
                                            Show Less
                                          </Button>
                                        </div>
                                      ) : (
                                        <div>
                                          <div className="whitespace-pre-wrap max-h-48 overflow-y-auto">
                                            {page.scraped_content_preview}
                                          </div>
                                          {page.scraped_content.length > 500 && (
                                            <Button
                                              onClick={() => toggleFullContent(page.id)}
                                              variant="link"
                                              className="mt-2 p-0 h-auto"
                                            >
                                              Read More
                                            </Button>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {/* Content Metrics */}
                                {page.content_metrics && (
                                  <div>
                                    <h6 className="font-medium mb-2">Content Metrics</h6>
                                    <div className="grid grid-cols-3 gap-4 text-sm">
                                      <div>
                                        <span className="font-medium">Readability:</span>{' '}
                                        {page.content_metrics.readability_score}/100
                                      </div>
                                      <div>
                                        <span className="font-medium">Categories:</span>{' '}
                                        {page.content_metrics.content_categories?.join(', ')}
                                      </div>
                                      <div>
                                        <span className="font-medium">Keywords:</span>{' '}
                                        {Object.keys(page.content_metrics.keyword_density || {}).length} found
                                      </div>
                                    </div>
                                  </div>
                                )}

                                {/* AI Analysis */}
                                {page.analysis_result && (
                                  <div>
                                    <h6 className="font-medium mb-2">AI Analysis</h6>
                                    <div className="text-sm bg-blue-50 p-3 rounded border whitespace-pre-wrap max-h-96 overflow-y-auto">
                                      {page.analysis_result}
                                    </div>
                                  </div>
                                )}

                                {/* Improvement Suggestions */}
                                {page.improvement_suggestions && (
                                  <div>
                                    <h6 className="font-medium mb-2">Improvement Suggestions</h6>
                                    <div className="text-sm bg-yellow-50 p-3 rounded border whitespace-pre-wrap">
                                      {page.improvement_suggestions}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default HistorySection;