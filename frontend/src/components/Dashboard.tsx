import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import ScoreMeter from './ScoreMeter';

interface DashboardStats {
  overview: {
    total_websites: number;
    total_pages: number;
    analyzed_pages: number;
    pending_analysis: number;
    average_score: number;
    score_distribution: {
      excellent: number;
      good: number;
      needs_improvement: number;
    };
  };
  recent_activity: Array<{
    id: number;
    action: string;
    message: string;
    timestamp: string;
    level: string;
  }>;
  top_performing_pages: Array<{
    id: number;
    url: string;
    title: string;
    score: number;
    website_id: number;
  }>;
  pages_needing_improvement: Array<{
    id: number;
    url: string;
    title: string;
    score: number;
    website_id: number;
  }>;
  websites?: Array<{
    id: number;
    base_url: string;
    title?: string;
    created_at: string;
    total_pages: number;
    analyzed_pages: number;
    average_score: number | null;
    status: string;
  }>;
  quick_stats?: {
    analyses_this_week: number;
    crawls_this_week: number;
    last_activity: string | null;
  };
}

interface WebsiteOption {
  id: number;
  base_url: string;
  title?: string;
  page_count: number;
}

interface UserLog {
  id: number;
  action: string;
  message: string;
  timestamp: string;
  level: string;
  url?: string;
}

interface IssuesSummary {
  total_broken_links: number;
  total_large_images: number;
  pages_with_broken_links: number;
  pages_with_large_images: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [exportLoading, setExportLoading] = useState(false);
  const [websiteOptions, setWebsiteOptions] = useState<WebsiteOption[]>([]);
  const [selectedWebsiteId, setSelectedWebsiteId] = useState<number | null>(null);
  const [userLogs, setUserLogs] = useState<UserLog[]>([]);
  const [issuesSummaries, setIssuesSummaries] = useState<Map<number, IssuesSummary>>(new Map());
  const [loadingIssues, setLoadingIssues] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError('');
      const [dashboardData, singleWebsites, crawledWebsites, logsData] = await Promise.all([
        apiService.getDashboardData().catch(() => null),
        apiService.getUserWebsites(),
        apiService.getCrawledWebsites(),
        apiService.getUserLogs().catch(() => null)
      ]);

      if (dashboardData?.success && dashboardData.data) {
        setStats(dashboardData.data);
      } else {
        await loadCalculatedDashboard(singleWebsites, crawledWebsites);
      }

      if (logsData?.success) {
        setUserLogs(logsData.logs.slice(0, 10));
      }

      const options: WebsiteOption[] = [];
     
      singleWebsites.forEach(website => {
        options.push({
          id: website.id,
          base_url: website.base_url,
          title: website.title,
          page_count: website.page ? 1 : 0
        });
      });
     
      crawledWebsites.forEach(website => {
        options.push({
          id: website.id,
          base_url: website.base_url,
          title: website.title,
          page_count: website.page_count || website.pages?.length || 0
        });
      });

      setWebsiteOptions(options);
     
      if (options.length > 0 && !selectedWebsiteId) {
        setSelectedWebsiteId(options[0].id);
      }

      await loadIssuesSummaries([...singleWebsites, ...crawledWebsites]);

    } catch (err: any) {
      console.error('Dashboard load error:', err);
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadIssuesSummaries = async (websites: any[]) => {
    try {
      setLoadingIssues(true);
      const summaries = new Map<number, IssuesSummary>();

      await Promise.all(
        websites.map(async (website) => {
          try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/issues/website/${website.id}/all-issues`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            });

            if (response.ok) {
              const data = await response.json();
              summaries.set(website.id, {
                total_broken_links: data.summary?.total_broken_links || 0,
                total_large_images: data.summary?.total_large_images || 0,
                pages_with_broken_links: data.summary?.pages_with_broken_links || 0,
                pages_with_large_images: data.summary?.pages_with_large_images || 0
              });
            }
          } catch (error) {
            console.log(`Could not load issues for website ${website.id}`);
          }
        })
      );

      setIssuesSummaries(summaries);
    } catch (error) {
      console.error('Error loading issues summaries:', error);
    } finally {
      setLoadingIssues(false);
    }
  };

  const getTotalIssues = () => {
    let totalBrokenLinks = 0;
    let totalLargeImages = 0;

    issuesSummaries.forEach((summary) => {
      totalBrokenLinks += summary.total_broken_links;
      totalLargeImages += summary.total_large_images;
    });

    return { totalBrokenLinks, totalLargeImages };
  };

  const loadCalculatedDashboard = async (singleWebsites: any[], crawledWebsites: any[]) => {
    try {
      const allWebsites = [...singleWebsites, ...crawledWebsites];
      const allPages: any[] = [];

      crawledWebsites.forEach(website => {
        if (website.pages) {
          allPages.push(...website.pages);
        }
      });

      singleWebsites.forEach(website => {
        if (website.page) {
          allPages.push(website.page);
        }
      });

      const analyzedPages = allPages.filter(page => page.grammar_score != null);
      const totalPages = allPages.length;
      const analyzedCount = analyzedPages.length;
     
      const averageScore = analyzedCount > 0
        ? Math.round(analyzedPages.reduce((sum, page) => sum + (page.grammar_score || 0), 0) / analyzedCount * 100) / 100
        : 0;

      const scoreDistribution = {
        excellent: analyzedPages.filter(page => (page.grammar_score || 0) >= 80).length,
        good: analyzedPages.filter(page => (page.grammar_score || 0) >= 60 && (page.grammar_score || 0) < 80).length,
        needs_improvement: analyzedPages.filter(page => (page.grammar_score || 0) < 60).length
      };

      const topPerformingPages = analyzedPages
        .sort((a, b) => (b.grammar_score || 0) - (a.grammar_score || 0))
        .slice(0, 5)
        .map(page => ({
          id: page.id,
          url: page.url,
          title: page.title || 'No title',
          score: page.grammar_score || 0,
          website_id: page.website_id || 0
        }));

      const pagesNeedingImprovement = analyzedPages
        .filter(page => (page.grammar_score || 0) < 60)
        .sort((a, b) => (a.grammar_score || 0) - (b.grammar_score || 0))
        .slice(0, 5)
        .map(page => ({
          id: page.id,
          url: page.url,
          title: page.title || 'No title',
          score: page.grammar_score || 0,
          website_id: page.website_id || 0
        }));

      let recentActivity = userLogs.slice(0, 5).map(log => ({
        id: log.id,
        action: log.action,
        message: log.message,
        timestamp: log.timestamp,
        level: log.level
      }));

      if (recentActivity.length === 0) {
        recentActivity = [
          {
            id: 1,
            action: "dashboard_loaded",
            message: "Dashboard data calculated from your websites",
            timestamp: new Date().toISOString(),
            level: "info"
          }
        ];
      }

      const calculatedStats: DashboardStats = {
        overview: {
          total_websites: allWebsites.length,
          total_pages: totalPages,
          analyzed_pages: analyzedCount,
          pending_analysis: totalPages - analyzedCount,
          average_score: averageScore,
          score_distribution: scoreDistribution
        },
        recent_activity: recentActivity,
        top_performing_pages: topPerformingPages,
        pages_needing_improvement: pagesNeedingImprovement,
        websites: allWebsites.map(website => ({
          id: website.id,
          base_url: website.base_url,
          title: website.title,
          created_at: website.created_at,
          total_pages: website.page_count || (website.page ? 1 : 0),
          analyzed_pages: website.page?.grammar_score ? 1 : 0,
          average_score: website.page?.grammar_score || null,
          status: website.page?.grammar_score ? "analyzed" : "pending"
        }))
      };

      setStats(calculatedStats);
     
    } catch (err) {
      throw new Error('Failed to calculate dashboard data');
    }
  };

  const handleExportJSON = async (websiteId: number) => {
    if (!websiteId) {
      setError('Please select a website to export');
      return;
    }
    try {
      setExportLoading(true);
      setError('');
     
      const data = await apiService.exportWebsiteJSON(websiteId);
     
      const websiteName = data.website?.base_url?.replace(/https?:\/\//, '').split('/')[0] || `website_${websiteId}`;
      const timestamp = new Date().toISOString().split('T')[0];
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `detailed_analysis_${websiteName}_${timestamp}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
     
      console.log('Exported detailed JSON for website:', websiteId);
     
    } catch (err: any) {
      console.error('Export error:', err);
      setError('Failed to export data: ' + (err.message || 'Unknown error. Please try again.'));
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportReport = async (websiteId: number) => {
    if (!websiteId) {
      setError('Please select a website to export');
      return;
    }
    try {
      setExportLoading(true);
      setError('');
     
      const data = await apiService.exportWebsiteReport(websiteId);
     
      const websiteName = data.website?.base_url?.replace(/https?:\/\//, '').split('/')[0] || `website_${websiteId}`;
      const timestamp = new Date().toISOString().split('T')[0];
      const blob = new Blob([data.report], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `comprehensive_report_${websiteName}_${timestamp}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
     
      console.log('Exported detailed report for website:', websiteId);
     
    } catch (err: any) {
      console.error('Export error:', err);
      setError('Failed to export report: ' + (err.message || 'Unknown error. Please try again.'));
    } finally {
      setExportLoading(false);
    }
  };

  const getSelectedWebsiteName = (): string => {
    if (!selectedWebsiteId) return 'No website selected';
    const website = websiteOptions.find(w => w.id === selectedWebsiteId);
    return website?.base_url || `Website ${selectedWebsiteId}`;
  };

  const formatLogLevel = (level: string) => {
    switch (level) {
      case 'error': return 'destructive';
      case 'warning': return 'secondary';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Dashboard</CardTitle>
          <CardDescription>Loading your analytics...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  const { totalBrokenLinks, totalLargeImages } = getTotalIssues();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dashboard Overview</CardTitle>
        <CardDescription>
          {stats ? 'Your website analysis statistics and insights' : 'Real-time dashboard data'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {stats ? (
          <div className="space-y-6">
            {/* Overview Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-primary">{stats.overview.total_websites}</div>
                  <div className="text-sm text-muted-foreground">Websites</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-green-500">{stats.overview.total_pages}</div>
                  <div className="text-sm text-muted-foreground">Total Pages</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-blue-500">{stats.overview.analyzed_pages}</div>
                  <div className="text-sm text-muted-foreground">Analyzed</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <ScoreMeter score={stats.overview.average_score} label="Avg Score" size="sm" />
                </CardContent>
              </Card>
            </div>

            {/* Issues Summary - NEW */}
            <Card className="border-orange-200 bg-orange-50/50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  ⚠️ Website Issues Summary
                  {loadingIssues && <span className="text-xs text-muted-foreground">(Loading...)</span>}
                </CardTitle>
                <CardDescription>Broken links and large images across all websites</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <Card className="bg-red-50 border-red-200">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-red-600">{totalBrokenLinks}</div>
                      <div className="text-sm text-muted-foreground">Broken Links (404/410)</div>
                      {totalBrokenLinks > 0 && (
                        <div className="text-xs text-red-600 mt-1">Requires immediate attention</div>
                      )}
                    </CardContent>
                  </Card>
                  <Card className="bg-orange-50 border-orange-200">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl font-bold text-orange-600">{totalLargeImages}</div>
                      <div className="text-sm text-muted-foreground">Large Images (&gt; 400KB)</div>
                      {totalLargeImages > 0 && (
                        <div className="text-xs text-orange-600 mt-1">Consider optimization</div>
                      )}
                    </CardContent>
                  </Card>
                </div>
                {(totalBrokenLinks > 0 || totalLargeImages > 0) && (
                  <Alert className="mt-4">
                    <AlertDescription>
                      <div className="text-sm">
                        <strong>Action needed:</strong> Go to "View History" and click "⚠️ View Issues" on any website to see detailed reports.
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Score Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Score Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-500">{stats.overview.score_distribution.excellent}</div>
                    <div className="text-sm text-muted-foreground">Excellent (80-100)</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-500">{stats.overview.score_distribution.good}</div>
                    <div className="text-sm text-muted-foreground">Good (60-79)</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-500">{stats.overview.score_distribution.needs_improvement}</div>
                    <div className="text-sm text-muted-foreground">Needs Work (0-59)</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Recent Activity</CardTitle>
                <CardDescription>Your latest website analysis activities</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats.recent_activity && stats.recent_activity.length > 0 ? (
                    stats.recent_activity.slice(0, 8).map((activity) => (
                      <div key={activity.id} className="flex items-start gap-3 text-sm p-2 rounded-lg hover:bg-muted/50">
                        <Badge
                          variant={formatLogLevel(activity.level)}
                          className="text-xs mt-0.5 shrink-0"
                        >
                          {activity.level}
                        </Badge>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium">{activity.action}</div>
                          <div className="text-muted-foreground text-xs truncate">
                            {activity.message}
                          </div>
                        </div>
                        <div className="text-xs text-muted-foreground shrink-0">
                          {new Date(activity.timestamp).toLocaleDateString()} {new Date(activity.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-4 text-muted-foreground">
                      No recent activity found
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
                <CardDescription>Export detailed analysis reports</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Website Selection */}
                  {websiteOptions.length > 0 && (
                    <div className="flex items-center gap-4">
                      <span className="text-sm font-medium">Select Website:</span>
                      <select
                        value={selectedWebsiteId || ''}
                        onChange={(e) => setSelectedWebsiteId(Number(e.target.value))}
                        className="border rounded px-3 py-2 text-sm flex-1 max-w-md"
                        disabled={exportLoading}
                      >
                        <option value="">Choose a website...</option>
                        {websiteOptions.map(website => (
                          <option key={website.id} value={website.id}>
                            {website.base_url} ({website.page_count} pages)
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                 
                  {/* Export Buttons */}
                  <div className="flex gap-4 flex-wrap">
                    <Button
                      onClick={() => handleExportJSON(selectedWebsiteId!)}
                      variant="outline"
                      disabled={!selectedWebsiteId || exportLoading}
                      className="flex items-center gap-2"
                    >
                      {exportLoading ? (
                        <>
                          <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                          Exporting...
                        </>
                      ) : (
                        <>
                          <span>📄</span>
                          Export Detailed JSON
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={() => handleExportReport(selectedWebsiteId!)}
                      variant="outline"
                      disabled={!selectedWebsiteId || exportLoading}
                      className="flex items-center gap-2"
                    >
                      {exportLoading ? (
                        <>
                          <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                          Exporting...
                        </>
                      ) : (
                        <>
                          <span>📊</span>
                          Export Comprehensive Report
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={loadDashboard}
                      variant="outline"
                      disabled={exportLoading}
                      className="flex items-center gap-2"
                    >
                      <span>🔄</span>
                      Refresh Stats
                    </Button>
                  </div>
                 
                  {selectedWebsiteId && (
                    <div className="text-xs text-muted-foreground p-2 bg-muted rounded">
                      <strong>Selected:</strong> {getSelectedWebsiteName()}
                      <br />
                      <strong>Exports include:</strong> Full scraped content, AI analysis results, broken links, large images, content metrics, and technical details
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            No dashboard data available. Analyze some websites to see statistics.
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default Dashboard;