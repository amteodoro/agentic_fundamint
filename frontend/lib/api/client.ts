/**
 * API client configuration and utilities for Fundamint.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100';

/**
 * Get the stored access token.
 */
export function getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('fundamint_access_token');
}

/**
 * Get the stored refresh token.
 */
export function getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('fundamint_refresh_token');
}

/**
 * Store tokens in localStorage.
 */
export function setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('fundamint_access_token', accessToken);
    localStorage.setItem('fundamint_refresh_token', refreshToken);
}

/**
 * Clear all stored tokens.
 */
export function clearTokens(): void {
    localStorage.removeItem('fundamint_access_token');
    localStorage.removeItem('fundamint_refresh_token');
}

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
    constructor(
        public status: number,
        public detail: string,
        public data?: unknown
    ) {
        super(detail);
        this.name = 'ApiError';
    }
}

/**
 * Refresh the access token using the refresh token.
 */
async function refreshAccessToken(): Promise<string | null> {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return null;

    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
            clearTokens();
            return null;
        }

        const data = await response.json();
        setTokens(data.access_token, data.refresh_token);
        return data.access_token;
    } catch {
        clearTokens();
        return null;
    }
}

/**
 * Generic fetch wrapper with authentication and error handling.
 */
export async function apiFetch<T>(
    endpoint: string,
    options: RequestInit = {},
    retry = true
): Promise<T> {
    const accessToken = getAccessToken();

    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (accessToken) {
        (headers as Record<string, string>)['Authorization'] = `Bearer ${accessToken}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    // Handle 401 - try to refresh token
    if (response.status === 401 && retry) {
        const newToken = await refreshAccessToken();
        if (newToken) {
            return apiFetch<T>(endpoint, options, false);
        }
        // If refresh fails, clear tokens and throw
        clearTokens();
        throw new ApiError(401, 'Session expired. Please login again.');
    }

    // Handle 204 No Content
    if (response.status === 204) {
        return undefined as T;
    }

    // Parse response
    const data = await response.json();

    if (!response.ok) {
        throw new ApiError(
            response.status,
            data.detail || 'An error occurred',
            data
        );
    }

    return data as T;
}

/**
 * HTTP method shortcuts.
 */
export const api = {
    get: <T>(endpoint: string) => apiFetch<T>(endpoint, { method: 'GET' }),

    post: <T>(endpoint: string, body?: unknown) =>
        apiFetch<T>(endpoint, {
            method: 'POST',
            body: body ? JSON.stringify(body) : undefined,
        }),

    put: <T>(endpoint: string, body?: unknown) =>
        apiFetch<T>(endpoint, {
            method: 'PUT',
            body: body ? JSON.stringify(body) : undefined,
        }),

    delete: <T>(endpoint: string) => apiFetch<T>(endpoint, { method: 'DELETE' }),
};

export { API_BASE_URL };
