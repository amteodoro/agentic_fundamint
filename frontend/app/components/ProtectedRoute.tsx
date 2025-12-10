"use client";

import { useAuth } from '@/app/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps {
    children: React.ReactNode;
    requireAuth?: boolean;
    redirectTo?: string;
}

/**
 * ProtectedRoute component that redirects unauthenticated users.
 */
export function ProtectedRoute({
    children,
    requireAuth = true,
    redirectTo = '/login'
}: ProtectedRouteProps) {
    const { isLoading, isAuthenticated } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && requireAuth && !isAuthenticated) {
            router.push(redirectTo);
        }
    }, [isLoading, isAuthenticated, requireAuth, redirectTo, router]);

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-emerald-500 border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" />
                    <p className="mt-4 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    if (requireAuth && !isAuthenticated) {
        return null;
    }

    return <>{children}</>;
}

/**
 * GuestOnlyRoute - Only allows unauthenticated users (e.g., login/register pages)
 */
interface GuestOnlyRouteProps {
    children: React.ReactNode;
    redirectTo?: string;
}

export function GuestOnlyRoute({
    children,
    redirectTo = '/'
}: GuestOnlyRouteProps) {
    const { isLoading, isAuthenticated } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && isAuthenticated) {
            router.push(redirectTo);
        }
    }, [isLoading, isAuthenticated, redirectTo, router]);

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-emerald-500 border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" />
                    <p className="mt-4 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    if (isAuthenticated) {
        return null;
    }

    return <>{children}</>;
}
