import React from 'react';
import { useAuth } from '../contexts/AuthContext';

interface ProfileProps {
  onClose: () => void;
}

const Profile: React.FC<ProfileProps> = ({ onClose }) => {
  const { user, logout } = useAuth();

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0, color: '#1f2937' }}>Profile</h3>
        <button 
          onClick={onClose}
          style={{ 
            background: 'none', 
            border: 'none', 
            fontSize: '1.2rem', 
            cursor: 'pointer',
            color: '#6b7280'
          }}
        >
          ×
        </button>
      </div>
      
      {user && (
        <div style={{ marginBottom: '1rem' }}>
          <p style={{ margin: '0.5rem 0' }}><strong>Username:</strong> {user.username}</p>
          <p style={{ margin: '0.5rem 0' }}><strong>Email:</strong> {user.email}</p>
          <p style={{ margin: '0.5rem 0' }}><strong>Member since:</strong> {new Date(user.created_at).toLocaleDateString()}</p>
        </div>
      )}
      
      <button
        onClick={() => {
          logout();
          onClose();
        }}
        style={{
          width: '100%',
          padding: '0.5rem',
          backgroundColor: '#dc2626',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Logout
      </button>
    </div>
  );
};

export default Profile;