'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { User, UserRole } from '@/types';
import { authService } from '@/services/authService';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  quickLogin: (role: UserRole) => Promise<void>;
  logout: () => void;
  switchRole: (role: UserRole) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_STORAGE_KEY = 'resqai_auth_token';
const USER_STORAGE_KEY = 'resqai_auth_user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize session from localStorage or seed default DISPATCHER session
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
      const storedUser = localStorage.getItem(USER_STORAGE_KEY);

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        setIsLoading(false);
      } else {
        // Default to DISPATCHER session for instant hackathon accessibility
        authService
          .quickLogin('DISPATCHER')
          .then((res) => {
            setToken(res.access_token);
            setUser(res.user);
            localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token);
            localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(res.user));
          })
          .catch((e) => {
            console.warn('Initial auth sync fallback:', e);
          })
          .finally(() => {
            setIsLoading(false);
          });
      }
    } catch (e) {
      console.warn('Error reading localStorage auth state:', e);
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await authService.login(email, password);
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(res.user));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const quickLogin = useCallback(async (role: UserRole) => {
    setIsLoading(true);
    try {
      const res = await authService.quickLogin(role);
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(res.user));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      localStorage.removeItem(USER_STORAGE_KEY);
    } catch (e) {
      console.warn('Error clearing localStorage:', e);
    }
  }, []);

  const switchRole = useCallback(
    async (role: UserRole) => {
      await quickLogin(role);
    },
    [quickLogin]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        quickLogin,
        logout,
        switchRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
