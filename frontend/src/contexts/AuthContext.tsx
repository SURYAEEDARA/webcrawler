import React, { createContext, useContext, useState, useEffect} from 'react';
import type { ReactNode } from 'react';
import { apiService } from '../services/api';
import type { User, LoginData, SignupData } from '../services/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginData) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token && apiService.isAuthenticated()) {
        try {
          const userData = await apiService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to get current user:', error);
          apiService.logout();
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (data: LoginData) => {
    try {
      const authResponse = await apiService.login(data);
      apiService.storeAuthData(authResponse);
      setUser(authResponse.user);
    } catch (error) {
      throw error;
    }
  };

  const signup = async (data: SignupData) => {
    try {
      const user = await apiService.signup(data);
      // After signup, automatically login
      const loginData = { email: data.email, password: data.password };
      const authResponse = await apiService.login(loginData);
      apiService.storeAuthData(authResponse);
      setUser(authResponse.user);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};