// src/components/Signup.tsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Signup: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { signup } = useAuth();
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

    if (formData.password !== formData.confirmPassword) {
      return setError('Passwords do not match');
    }

    if (formData.password.length < 6) {
      return setError('Password must be at least 6 characters');
    }

    try {
      setLoading(true);
      await signup({
        email: formData.email,
        username: formData.username,
        password: formData.password,
      });
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb', padding: '20px' }}>
      <div style={{ maxWidth: '400px', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
            Create your account
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {error && (
            <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '12px', borderRadius: '6px', marginBottom: '20px' }}>
              {error}
            </div>
          )}
          
          <div style={{ marginBottom: '15px' }}>
            <input
              name="email"
              type="email"
              required
              style={{ width: '100%', padding: '10px', border: '1px solid #d1d5db', borderRadius: '4px' }}
              placeholder="Email address"
              value={formData.email}
              onChange={handleChange}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <input
              name="username"
              type="text"
              required
              style={{ width: '100%', padding: '10px', border: '1px solid #d1d5db', borderRadius: '4px' }}
              placeholder="Username"
              value={formData.username}
              onChange={handleChange}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
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
          
          <div style={{ marginBottom: '20px' }}>
            <input
              name="confirmPassword"
              type="password"
              required
              style={{ width: '100%', padding: '10px', border: '1px solid #d1d5db', borderRadius: '4px' }}
              placeholder="Confirm Password"
              value={formData.confirmPassword}
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
              {loading ? 'Creating Account...' : 'Sign up'}
            </button>
          </div>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <Link
              to="/login"
              style={{ color: '#4f46e5', textDecoration: 'none' }}
            >
              Already have an account? Sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Signup;