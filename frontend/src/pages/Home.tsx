import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import AnalyzeSection from '../components/AnalyzeSection';
import HistorySection from '../components/HistorySection';
import Dashboard from '../components/Dashboard';
import { Button } from '../components/ui/button';

const Home: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  const [activeView, setActiveView] = useState<'analyze' | 'history' | 'dashboard'>('analyze');
  const [recentWebsite, setRecentWebsite] = useState<any>(null);

  const handleWebsiteAdded = () => {
    setActiveView('history');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div>Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      {!isAuthenticated ? (
        <div className="min-h-[calc(100vh-80px)] flex items-center justify-center p-8">
          <div className="text-center max-w-2xl">
            <h1 className="text-4xl font-bold mb-4 text-gray-900">
              WebAnalyzer
            </h1>
            <p className="text-xl mb-8 text-gray-600">
              Analyze website content with AI-powered grammar and content quality
            </p>
            <div className="flex gap-4 justify-center">
              <Link to="/signup">
                <Button size="lg">
                  Get Started
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="outline" size="lg">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      ) : (
        <div className="container mx-auto p-6 max-w-6xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2 text-gray-900">
              WebAnalyzer
            </h1>
            <p className="text-gray-600">
              Professional website content analysis and auditing
            </p>
          </div>

          <div className="flex gap-4 mb-8 justify-center">
            <Button
              onClick={() => setActiveView('analyze')}
              variant={activeView === 'analyze' ? "default" : "outline"}
              size="lg"
            >
              Analyze Website
            </Button>
            <Button
              onClick={() => setActiveView('history')}
              variant={activeView === 'history' ? "default" : "outline"}
              size="lg"
            >
              View History
            </Button>
            <Button
              onClick={() => setActiveView('dashboard')}
              variant={activeView === 'dashboard' ? "default" : "outline"}
              size="lg"
            >
              Dashboard
            </Button>
          </div>

          {activeView === 'analyze' ? (
            <AnalyzeSection onWebsiteAdded={handleWebsiteAdded} />
          ) : activeView === 'history' ? (
            <HistorySection />
          ) : (
            <Dashboard />
          )}
        </div>
      )}
    </div>
  );
};

export default Home;