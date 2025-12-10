"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  User,
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  getCurrentUser,
  LoginData,
  RegisterData,
} from '@/lib/api/auth';
import { getAccessToken, clearTokens } from '@/lib/api/client';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  loginAsGuest: () => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Check for existing session on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        // First check for guest user in localStorage (backward compatibility)
        const storedUser = localStorage.getItem('fundamint_user');
        if (storedUser) {
          const parsedUser = JSON.parse(storedUser);
          if (parsedUser.isGuest) {
            // Convert old guest format to new format
            setUser({
              id: parsedUser.id,
              email: parsedUser.email,
              name: parsedUser.name,
              is_active: true,
              is_guest: true,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            });
            setIsLoading(false);
            return;
          }
        }

        // Check for JWT token
        const token = getAccessToken();
        if (token) {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        clearTokens();
        localStorage.removeItem('fundamint_user');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (data: LoginData) => {
    setIsLoading(true);
    try {
      const response = await apiLogin(data);
      setUser(response.user);
      // Clear any old guest user data
      localStorage.removeItem('fundamint_user');
      router.push('/');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true);
    try {
      const response = await apiRegister(data);
      setUser(response.user);
      // Clear any old guest user data
      localStorage.removeItem('fundamint_user');
      router.push('/');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  const loginAsGuest = useCallback(() => {
    const guestUser: User = {
      id: 'guest-' + Math.random().toString(36).substr(2, 9),
      email: 'guest@example.com',
      name: 'Guest Investor',
      is_active: true,
      is_guest: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setUser(guestUser);
    // Store in localStorage for backward compatibility
    localStorage.setItem('fundamint_user', JSON.stringify({
      id: guestUser.id,
      name: guestUser.name,
      email: guestUser.email,
      isGuest: true,
    }));
    router.push('/');
  }, [router]);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      if (user && !user.is_guest) {
        await apiLogout();
      }
    } catch {
      // Ignore logout errors
    } finally {
      setUser(null);
      clearTokens();
      localStorage.removeItem('fundamint_user');
      setIsLoading(false);
      router.push('/login');
    }
  }, [user, router]);

  const refreshUser = useCallback(async () => {
    if (user?.is_guest) return;

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      // If refresh fails, logout
      await logout();
    }
  }, [user, logout]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        loginAsGuest,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
