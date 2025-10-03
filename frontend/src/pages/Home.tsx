import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import AnalyzeSection from '../components/AnalyzeSection';
import HistorySection from '../components/HistorySection';
import type { Website } from '../services/api';

const Home: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  const [websites, setWebsites] = useState<Website[]>([]);

  const handleWebsiteAdded = (website: Website) => {
    setWebsites(prev => [website, ...prev]);
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: '1.5rem' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      <Navbar />
      
      {!isAuthenticated ? (
        <div style={{ 
          minHeight: 'calc(100vh - 80px)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          padding: '2rem'
        }}>
          <div style={{ maxWidth: '600px', width: '100%', textAlign: 'center' }}>
            <h1 style={{ fontSize: '3rem', fontWeight: 'bold', marginBottom: '1.5rem', color: '#1f2937' }}>
              WebAnalyzer
            </h1>
            <p style={{ fontSize: '1.3rem', marginBottom: '2rem', color: '#6b7280', lineHeight: '1.6' }}>
              Analyze any website's content and get AI-powered grammar suggestions, 
              style improvements, and comprehensive writing analysis to enhance your 
              online content quality.
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <Link
                to="/signup"
                style={{ 
                  padding: '12px 24px', 
                  backgroundColor: '#4f46e5', 
                  color: 'white', 
                  textDecoration: 'none',
                  borderRadius: '4px',
                  fontWeight: 'bold'
                }}
              >
                Get Started Free
              </Link>
              <Link
                to="/login"
                style={{ 
                  padding: '12px 24px', 
                  backgroundColor: '#e5e7eb', 
                  color: '#374151', 
                  textDecoration: 'none',
                  borderRadius: '4px',
                  fontWeight: 'bold'
                }}
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
          {/* Welcome Section */}
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#1f2937', marginBottom: '1rem' }}>
              Welcome to WebAnalyzer!
            </h1>
            <p style={{ fontSize: '1.2rem', color: '#6b7280', maxWidth: '600px', margin: '0 auto' }}>
              Analyze website content, get grammar scores, and receive AI-powered improvement suggestions.
            </p>
          </div>

          {/* Analyze Section */}
          <AnalyzeSection onWebsiteAdded={handleWebsiteAdded} />

          {/* History Section */}
          <HistorySection />
        </div>
      )}
    </div>
  );
};

export default Home;