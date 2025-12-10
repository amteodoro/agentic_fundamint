"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  name: string;
  email: string;
  isGuest: boolean;
}

interface AuthContextType {
  user: User | null;
  loginAsGuest: () => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Check local storage for existing session
    const storedUser = localStorage.getItem('fundamint_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const loginAsGuest = () => {
    const guestUser: User = {
      id: 'guest-' + Math.random().toString(36).substr(2, 9),
      name: 'Guest Investor',
      email: 'guest@example.com',
      isGuest: true,
    };
    setUser(guestUser);
    localStorage.setItem('fundamint_user', JSON.stringify(guestUser));
    router.push('/');
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('fundamint_user');
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loginAsGuest, logout, isAuthenticated: !!user }}>
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
