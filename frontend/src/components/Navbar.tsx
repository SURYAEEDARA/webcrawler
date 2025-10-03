import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import Profile from './Profile';

const Navbar: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  return (
    <nav style={{
      backgroundColor: 'white',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      padding: '1rem 2rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      position: 'relative'
    }}>
      {/* Logo */}
      <Link 
        to="/" 
        style={{ 
          fontSize: '1.5rem', 
          fontWeight: 'bold', 
          color: '#4f46e5', 
          textDecoration: 'none' 
        }}
      >
        WebAnalyzer
      </Link>

      {/* Navigation Links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {!isAuthenticated ? (
          <>
            <Link 
              to="/login" 
              style={{ 
                color: '#374151', 
                textDecoration: 'none',
                padding: '0.5rem 1rem'
              }}
            >
              Login
            </Link>
            <span style={{ color: '#d1d5db' }}>|</span>
            <Link 
              to="/signup" 
              style={{ 
                color: '#374151', 
                textDecoration: 'none',
                padding: '0.5rem 1rem'
              }}
            >
              Register
            </Link>
          </>
        ) : (
          <>
            <button
              onClick={() => setShowProfile(!showProfile)}
              style={{
                backgroundColor: '#4f46e5',
                color: 'white',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Profile
            </button>
            {showProfile && (
              <div style={{
                position: 'absolute',
                top: '100%',
                right: '2rem',
                backgroundColor: 'white',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                borderRadius: '8px',
                padding: '1rem',
                minWidth: '200px',
                zIndex: 1000
              }}>
                <Profile onClose={() => setShowProfile(false)} />
              </div>
            )}
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;