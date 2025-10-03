import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Login: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      setLoading(true);
      await login(formData);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb', padding: '20px' }}>
      <div style={{ maxWidth: '400px', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
            Sign in to your account
          </h2>
        </div>
        
        <form onSubmit={handleSubmit}>
          {error && (
            <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '12px', borderRadius: '6px', marginBottom: '20px' }}>
              {error}
            </div>
          )}
          
          <div style={{ marginBottom: '15px' }}>
            <input
              name="email"
              type="text"
              required
              style={{ width: '100%', padding: '10px', border: '1px solid #d1d5db', borderRadius: '4px' }}
              placeholder="email"
              value={formData.email}
              onChange={handleChange}
            />
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <input
              name="password"
              type="password"
              required
              style={{ width: '100%', padding: '10px', border: '1px solid #d1d5db', borderRadius: '4px' }}
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              style={{ 
                width: '100%', 
                padding: '12px', 
                backgroundColor: '#4f46e5', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px',
                opacity: loading ? 0.5 : 1
              }}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <Link
              to="/signup"
              style={{ color: '#4f46e5', textDecoration: 'none' }}
            >
              Don't have an account? Sign up
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;