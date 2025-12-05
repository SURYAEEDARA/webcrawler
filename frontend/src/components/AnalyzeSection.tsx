import React, { useState } from 'react';
import { apiService } from '../services/api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

interface AnalyzeSectionProps {
  onWebsiteAdded: (website: any) => void;
}

const AnalyzeSection: React.FC<AnalyzeSectionProps> = ({ onWebsiteAdded }) => {
  const [url, setUrl] = useState('');
  const [maxPages, setMaxPages] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setAnalysisResult(null);

    try {
      if (!url.trim()) {
        throw new Error('Please enter a website URL');
      }

      let processedUrl = url.trim();
      if (!processedUrl.startsWith('http://') && !processedUrl.startsWith('https://')) {
        processedUrl = 'https://' + processedUrl;
      }

      console.log('Crawling website recursively:', processedUrl);
      const crawlData = { base_url: processedUrl, max_pages: maxPages };
      
      const crawledWebsite = await apiService.crawlWebsiteRecursive(crawlData);
      console.log('Crawled website:', crawledWebsite);
      
      setAnalysisResult({
        pages_crawled: crawledWebsite.page_count,
        message: `Successfully crawled ${crawledWebsite.page_count} pages`
      });
      onWebsiteAdded(crawledWebsite);
      setUrl('');
    } catch (err: any) {
      console.error('Analysis error:', err);
      let errorMessage = err.message || 'Failed to crawl website. Please try again.';
      
      if (errorMessage.includes('404') || errorMessage.includes('Not Found')) {
        errorMessage = 'Website not found. Please check the URL and try again.';
      } else if (errorMessage.includes('Network') || errorMessage.includes('Failed to fetch')) {
        errorMessage = 'Cannot connect to the server. Make sure the backend is running on localhost:8000.';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Crawl & Analyze Website</CardTitle>
        <CardDescription>
          Crawl and analyze multiple pages from a website. All pages will be checked for broken links, 
          large images, and content quality. Individual pages can be analyzed for grammar after crawling.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleAnalyze} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>
                <div className="flex flex-col">
                  <span>{error}</span>
                  {error.includes('localhost:8000') && (
                    <span className="text-sm mt-1">
                      Make sure your backend server is running: <code>python main.py</code>
                    </span>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          <div className="flex gap-4 items-end">
            <div className="flex-1 space-y-2">
              <Label htmlFor="url">Website URL</Label>
              <Input
                id="url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter website URL (e.g., https://example.com)"
                required
                disabled={loading}
              />
            </div>
            
            <div className="w-32 space-y-2">
              <Label htmlFor="maxPages">Max Pages</Label>
              <Select value={maxPages.toString()} onValueChange={(value) => setMaxPages(Number(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5 pages</SelectItem>
                  <SelectItem value="10">10 pages</SelectItem>
                  <SelectItem value="20">20 pages</SelectItem>
                  <SelectItem value="50">50 pages</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Button
              type="submit"
              disabled={loading}
              className="whitespace-nowrap"
            >
              {loading ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Crawling...
                </>
              ) : (
                'Crawl Website'
              )}
            </Button>
          </div>

          {analysisResult && (
            <Card className="bg-muted/50 mt-4">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-lg">Crawling Complete</h3>
                  <Badge variant="default" className="text-lg px-3 py-1">
                    {analysisResult.pages_crawled} pages
                  </Badge>
                </div>
                <div className="space-y-3">
                  <div className="text-sm text-muted-foreground">
                    {analysisResult.message}
                  </div>
                  <Alert>
                    <AlertDescription>
                      <div className="text-sm space-y-1">
                        <div>✓ <strong>Broken links detected</strong> - View in "⚠️ View Issues"</div>
                        <div>✓ <strong>Large images identified</strong> - View in "⚠️ View Issues"</div>
                        <div>📝 <strong>Ready for grammar analysis</strong> - Analyze individual pages in "View History"</div>
                      </div>
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="text-xs text-muted-foreground">
            <strong>What happens during crawl:</strong>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Discovers and scrapes all linked pages (up to max pages limit)</li>
              <li>Checks all links for broken references (404/410 errors)</li>
              <li>Identifies images larger than 400KB that need optimization</li>
              <li>Extracts content for later AI grammar analysis</li>
            </ul>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default AnalyzeSection;