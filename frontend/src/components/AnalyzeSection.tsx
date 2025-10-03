import React, { useState } from 'react';
import { apiService } from '../services/api';
import type { Website } from '../services/api';

interface AnalyzeSectionProps {
  onWebsiteAdded: (website: Website) => void;
}

const AnalyzeSection: React.FC<AnalyzeSectionProps> = ({ onWebsiteAdded }) => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const scrapedWebsite = await apiService.scrapeWebsite(url);
      
      const analyzedWebsite = await apiService.analyzeWebsite(scrapedWebsite.id);
      
      onWebsiteAdded(analyzedWebsite);
      setUrl('');
    } catch (err: any) {
      setError(err.message || 'Failed to analyze website');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      backgroundColor: 'white', 
      padding: '2rem', 
      borderRadius: '8px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      marginBottom: '2rem'
    }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
        Analyze a Website
      </h2>
      
      <form onSubmit={handleAnalyze}>
        {error && (
          <div style={{ 
            backgroundColor: '#fef2f2', 
            border: '1px solid #fecaca', 
            color: '#dc2626', 
            padding: '12px', 
            borderRadius: '4px', 
            marginBottom: '1rem' 
          }}>
            {error}
          </div>
        )}
        
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter website URL (e.g., https://example.com)"
            required
            style={{ 
              flex: 1, 
              padding: '0.75rem', 
              border: '1px solid #d1d5db', 
              borderRadius: '4px',
              fontSize: '1rem'
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{ 
              padding: '0.75rem 2rem', 
              backgroundColor: '#4f46e5', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer',
              opacity: loading ? 0.5 : 1
            }}
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        
        <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>
          Enter a website URL to analyze its content for grammar and improvement suggestions.
        </p>
      </form>
    </div>
  );
};

export default AnalyzeSection;