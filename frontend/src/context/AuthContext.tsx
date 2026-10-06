import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../api/types';
import { authApi } from '../api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginAsDemo: (role: 'student' | 'admin' | 'teacher') => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        try {
          const profile = await authApi.getMe();
          setUser(profile);
        } catch (err) {
          localStorage.removeItem('access_token');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await authApi.login(email, password);
    localStorage.setItem('access_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  };

  const loginAsDemo = async (role: 'student' | 'admin' | 'teacher') => {
    const creds = {
      student: { email: 'student@learnai.dev', pass: 'student123' },
      admin: { email: 'admin@learnai.dev', pass: 'admin123' },
      teacher: { email: 'teacher@learnai.dev', pass: 'teacher123' },
    }[role];
    await login(creds.email, creds.pass);
  };

  const register = async (email: string, password: string, fullName: string) => {
    const data = await authApi.register(email, password, fullName);
    localStorage.setItem('access_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, loginAsDemo, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
