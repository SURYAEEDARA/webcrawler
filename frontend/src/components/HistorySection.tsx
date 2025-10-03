import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { Website } from '../services/api';

const HistorySection: React.FC = () => {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadWebsites();
  }, []);

  const loadWebsites = async () => {
    try {
      const userWebsites = await apiService.getUserWebsites();
      setWebsites(userWebsites);
    } catch (err: any) {
      setError(err.message || 'Failed to load websites');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        backgroundColor: 'white', 
        padding: '2rem', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '1.2rem' }}>Loading your analysis history...</div>
      </div>
    );
  }

  return (
    <div style={{ 
      backgroundColor: 'white', 
      padding: '2rem', 
      borderRadius: '8px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
        Analysis History
      </h2>
      
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
      
      {websites.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
          <p>No websites analyzed yet. Start by analyzing a website above!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {websites.map((website) => (
            <div 
              key={website.id}
              style={{ 
                border: '1px solid #e5e7eb', 
                borderRadius: '6px', 
                padding: '1rem',
                backgroundColor: '#f9fafb'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 'bold' }}>
                  {website.title}
                </h3>
                {website.grammar_score && (
                  <span style={{ 
                    backgroundColor: website.grammar_score >= 80 ? '#10b981' : 
                                   website.grammar_score >= 60 ? '#f59e0b' : '#ef4444',
                    color: 'white',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.8rem',
                    fontWeight: 'bold'
                  }}>
                    Score: {website.grammar_score}/100
                  </span>
                )}
              </div>
              
              <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                <strong>URL:</strong> {website.url}
              </p>
              <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                <strong>Words:</strong> {website.word_count} • 
                <strong> Analyzed:</strong> {new Date(website.created_at).toLocaleDateString()}
              </p>
              
              {website.improvement_suggestions && (
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ cursor: 'pointer', color: '#4f46e5' }}>
                    View Suggestions
                  </summary>
                  <div style={{ 
                    marginTop: '0.5rem', 
                    padding: '0.5rem', 
                    backgroundColor: 'white', 
                    borderRadius: '4px',
                    fontSize: '0.9rem'
                  }}>
                    {website.improvement_suggestions}
                  </div>
                </details>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistorySection;