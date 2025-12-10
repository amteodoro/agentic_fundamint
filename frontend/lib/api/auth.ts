/**
 * Authentication API services.
 */

import { api, setTokens, clearTokens, API_BASE_URL } from './client';

export interface User {
    id: string;
    email: string;
    name: string | null;
    is_active: boolean;
    is_guest: boolean;
    created_at: string;
    updated_at: string;
}

export interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: User;
}

export interface RegisterData {
    email: string;
    password: string;
    name?: string;
}

export interface LoginData {
    email: string;
    password: string;
}

/**
 * Register a new user account.
 */
export async function register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
    }

    const authData: AuthResponse = await response.json();
    setTokens(authData.access_token, authData.refresh_token);
    return authData;
}

/**
 * Login with email and password.
 */
export async function login(data: LoginData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
    }

    const authData: AuthResponse = await response.json();
    setTokens(authData.access_token, authData.refresh_token);
    return authData;
}

/**
 * Logout the current user.
 */
export async function logout(): Promise<void> {
    try {
        await api.post('/api/auth/logout');
    } catch {
        // Ignore errors during logout
    } finally {
        clearTokens();
    }
}

/**
 * Get the current authenticated user.
 */
export async function getCurrentUser(): Promise<User> {
    return api.get<User>('/api/auth/me');
}
