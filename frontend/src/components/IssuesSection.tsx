import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';

interface BrokenLink {
  url: string;
  status_code: number;
  link_text?: string;
  found_on_page: string;
  error?: string;
  page_id: number;
  page_title?: string;
}

interface LargeImage {
  url: string;
  filename: string;
  size_bytes: number;
  size_kb: number;
  size_mb: number;
  alt_text?: string;
  found_on_page: string;
  page_id: number;
  page_title?: string;
  is_banner: boolean;
  severity: 'critical';
  threshold_type: 'banner' | 'regular';
  max_allowed_kb: number;
  recommendation: string;
  percentage_over: number;
}

interface IssuesSectionProps {
  websiteId: number;
  websiteName: string;
}

const IssuesSection: React.FC<IssuesSectionProps> = ({ websiteId, websiteName }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [brokenLinks, setBrokenLinks] = useState<BrokenLink[]>([]);
  const [largeImages, setLargeImages] = useState<LargeImage[]>([]);
  const [activeTab, setActiveTab] = useState<'broken-links' | 'large-images'>('broken-links');
  const [imageFilter, setImageFilter] = useState<'all' | 'banner' | 'regular'>('all');

  useEffect(() => {
    loadIssues();
  }, [websiteId]);

  const loadIssues = async () => {
    try {
      setLoading(true);
      setError('');

      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/issues/website/${websiteId}/all-issues`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load issues');
      }

      const data = await response.json();
      setBrokenLinks(data.broken_links || []);
      setLargeImages(data.large_images || []);
    } catch (err: any) {
      console.error('Issues load error:', err);
      setError(err.message || 'Failed to load issues');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeVariant = (statusCode: number) => {
    if (statusCode === 404) return 'destructive';
    if (statusCode === 410) return 'secondary';
    return 'outline';
  };

  const getImageTypeBadge = (isBanner: boolean) => {
    if (isBanner) {
      return <Badge variant="destructive" className="bg-purple-600">BANNER</Badge>;
    }
    return <Badge variant="secondary" className="bg-orange-500 text-white">REGULAR</Badge>;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const filteredImages = largeImages.filter(img => {
    if (imageFilter === 'all') return true;
    if (imageFilter === 'banner') return img.is_banner;
    if (imageFilter === 'regular') return !img.is_banner;
    return true;
  });

  const bannerCount = largeImages.filter(img => img.is_banner).length;
  const regularCount = largeImages.filter(img => !img.is_banner).length;

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading Issues...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">Loading broken links and large images...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Website Issues Report</CardTitle>
        <CardDescription>
          Broken links (404/410) and large images found on {websiteName}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card className="cursor-pointer hover:bg-muted/50" onClick={() => setActiveTab('broken-links')}>
            <CardContent className="p-4 text-center">
              <div className={`text-3xl font-bold ${brokenLinks.length > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {brokenLinks.length}
              </div>
              <div className="text-sm text-muted-foreground">Broken Links</div>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:bg-muted/50" onClick={() => { setActiveTab('large-images'); setImageFilter('banner'); }}>
            <CardContent className="p-4 text-center">
              <div className={`text-3xl font-bold ${bannerCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {bannerCount}
              </div>
              <div className="text-sm text-muted-foreground">Banner Images (2MB+)</div>
            </CardContent>
          </Card>

          <Card className="cursor-pointer hover:bg-muted/50" onClick={() => { setActiveTab('large-images'); setImageFilter('regular'); }}>
            <CardContent className="p-4 text-center">
              <div className={`text-3xl font-bold ${regularCount > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                {regularCount}
              </div>
              <div className="text-sm text-muted-foreground">Regular Images (400KB+)</div>
            </CardContent>
          </Card>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-4 border-b">
          <Button
            variant={activeTab === 'broken-links' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('broken-links')}
            className="rounded-b-none"
          >
            🔗 Broken Links ({brokenLinks.length})
          </Button>
          <Button
            variant={activeTab === 'large-images' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('large-images')}
            className="rounded-b-none"
          >
            🖼️ Large Images ({largeImages.length})
          </Button>
        </div>

        {/* Broken Links Tab */}
        {activeTab === 'broken-links' && (
          <div className="space-y-4">
            {brokenLinks.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed rounded-lg">
                <div className="text-green-600 text-lg font-semibold mb-2">✓ No Broken Links Found!</div>
                <div className="text-muted-foreground">All links on this website are working properly.</div>
              </div>
            ) : (
              <>
                <Alert>
                  <AlertDescription>
                    <strong>Found {brokenLinks.length} broken link(s)</strong> that need attention.
                    Broken links hurt user experience and SEO rankings.
                  </AlertDescription>
                </Alert>

                {brokenLinks.map((link, index) => (
                  <Card key={index} className="bg-red-50 border-red-200">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0 mr-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant={getStatusBadgeVariant(link.status_code)}>
                              {link.status_code === 0 ? 'Connection Error' : `HTTP ${link.status_code}`}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              on page: {link.page_title || 'Untitled'}
                            </span>
                          </div>
                          <div className="font-mono text-sm break-all text-red-700 mb-1">
                            {link.url}
                          </div>
                          {link.link_text && (
                            <div className="text-xs text-muted-foreground">
                              Link text: &quot;{link.link_text}&quot;
                            </div>
                          )}
                          {link.error && (
                            <div className="text-xs text-red-600 mt-1">
                              Error: {link.error}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground mt-2 pt-2 border-t">
                        Found on: <a href={link.found_on_page} target="_blank" rel="noopener noreferrer"
                          className="text-blue-600 hover:underline break-all">
                          {link.found_on_page}
                        </a>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </>
            )}
          </div>
        )}

        {/* Large Images Tab */}
        {activeTab === 'large-images' && (
          <div className="space-y-4">
            {/* Filter Buttons */}
            <div className="flex gap-2 mb-4">
              <Button
                variant={imageFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setImageFilter('all')}
              >
                All ({largeImages.length})
              </Button>
              <Button
                variant={imageFilter === 'banner' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setImageFilter('banner')}
                className={imageFilter === 'banner' ? 'bg-purple-600' : ''}
              >
                Banner ({bannerCount})
              </Button>
              <Button
                variant={imageFilter === 'regular' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setImageFilter('regular')}
                className={imageFilter === 'regular' ? 'bg-orange-500' : ''}
              >
                Regular ({regularCount})
              </Button>
            </div>

            {filteredImages.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed rounded-lg">
                <div className="text-green-600 text-lg font-semibold mb-2">✓ No Large Images Found!</div>
                <div className="text-muted-foreground">
                  {imageFilter === 'all' 
                    ? 'All images on this website are properly optimized.'
                    : `No ${imageFilter} images found.`}
                </div>
              </div>
            ) : (
              <>
                <Alert>
                  <AlertDescription>
                    <div className="space-y-1">
                      <div><strong>Found {filteredImages.length} large image(s)</strong></div>
                      <div className="text-sm">
                        • <span className="text-purple-600 font-semibold">Banner ({bannerCount})</span>: Over 2MB - needs optimization
                      </div>
                      <div className="text-sm">
                        • <span className="text-orange-600 font-semibold">Regular ({regularCount})</span>: Over 400KB - should be reviewed
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>

                {filteredImages.map((image, index) => (
                  <Card 
                    key={index} 
                    className={image.is_banner ? 'bg-purple-50 border-purple-300' : 'bg-orange-50 border-orange-200'}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1 min-w-0 mr-4">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            {getImageTypeBadge(image.is_banner)}
                            <Badge variant="outline" className="font-mono">
                              {formatFileSize(image.size_bytes)}
                            </Badge>
                            <Badge variant="secondary">
                              {image.percentage_over}% over {image.is_banner ? '2MB' : '400KB'} limit
                            </Badge>
                          </div>
                          
                          <div className="font-semibold text-base mb-1">
                            📁 {image.filename}
                          </div>
                          
                          <div className="text-xs text-muted-foreground mb-2 font-mono break-all">
                            {image.url}
                          </div>

                          <div className="bg-white p-2 rounded border mb-2">
                            <div className="text-sm font-medium mb-1">
                              {image.is_banner ? '🚨' : '⚠️'} {image.recommendation}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Target: ~{image.is_banner ? '500KB-1MB' : '100KB'} for optimal performance
                            </div>
                          </div>

                          {image.alt_text && image.alt_text !== 'No alt text' && (
                            <div className="text-xs text-muted-foreground mt-1">
                              Alt text: &quot;{image.alt_text}&quot;
                            </div>
                          )}

                          <div className="text-xs text-muted-foreground">
                            Page: <span className="font-medium">{image.page_title || 'Untitled'}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center mt-2 pt-2 border-t">
                        <div className="text-xs text-muted-foreground">
                          Found on: <a href={image.found_on_page} target="_blank" rel="noopener noreferrer"
                            className="text-blue-600 hover:underline break-all">
                            {image.found_on_page}
                          </a>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="font-medium text-sm mb-2">💡 Image Optimization Tips:</h4>
                  <ul className="text-xs space-y-1 text-muted-foreground list-disc list-inside">
                    <li>Use <strong>TinyPNG</strong> (tinypng.com) or <strong>ImageOptim</strong> to compress images</li>
                    <li>Convert to modern formats like <strong>WebP</strong> or <strong>AVIF</strong> for better compression</li>
                    <li>Resize images to match their display size on the page</li>
                    <li>Use lazy loading for images below the fold</li>
                    <li>Consider using a CDN with automatic image optimization</li>
                    <li><strong>Targets:</strong></li>
                    <li>• Banner images: Keep under 2MB, aim for 500KB-1MB</li>
                    <li>• Regular images: Keep under 400KB, aim for ~100KB</li>
                  </ul>
                </div>
              </>
            )}
          </div>
        )}

        <div className="mt-6 flex gap-2">
          <Button onClick={loadIssues} variant="outline">
            🔄 Refresh Issues
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default IssuesSection;