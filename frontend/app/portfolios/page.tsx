"use client";

import { useRouter } from 'next/navigation';
import { PortfolioManager } from '@/app/components/PortfolioManager';
import { WatchlistManager } from '@/app/components/WatchlistManager';
import { useAuth } from '@/app/context/AuthContext';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function PortfoliosPage() {
    const { user, isAuthenticated, isLoading } = useAuth();
    const router = useRouter();

    const handleSelectStock = (ticker: string) => {
        router.push(`/stock/${ticker}`);
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-emerald-500 border-r-transparent" />
                    <p className="mt-4 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Main Content */}
            <main className="container mx-auto px-4 py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">My Investments</h1>
                    <p className="text-gray-600">
                        Manage your portfolios and watchlists. Click on any stock ticker to view its analysis.
                    </p>
                </div>

                {!isAuthenticated ? (
                    <div className="text-center py-16 bg-white rounded-lg border border-gray-200 shadow-sm">
                        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Sign in to access your portfolios</h2>
                        <p className="text-gray-600 mb-8 max-w-md mx-auto">
                            Create an account or sign in to save stocks to your portfolios and watchlists.
                        </p>
                        <div className="flex items-center justify-center gap-4">
                            <Link href="/login">
                                <Button className="bg-emerald-600 hover:bg-emerald-700">
                                    Sign In
                                </Button>
                            </Link>
                            <Link href="/register">
                                <Button variant="outline" className="border-gray-300 text-gray-700 hover:bg-gray-50">
                                    Create Account
                                </Button>
                            </Link>
                        </div>
                    </div>
                ) : user?.is_guest ? (
                    <div className="text-center py-16 bg-white rounded-lg border border-gray-200 shadow-sm">
                        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Guest Mode</h2>
                        <p className="text-gray-600 mb-8 max-w-md mx-auto">
                            You&apos;re browsing as a guest. Create an account to save your portfolios and watchlists.
                        </p>
                        <Link href="/register">
                            <Button className="bg-emerald-600 hover:bg-emerald-700">
                                Create Account
                            </Button>
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <PortfolioManager onSelectStock={handleSelectStock} />
                        <WatchlistManager onSelectStock={handleSelectStock} />
                    </div>
                )}
            </main>
        </div>
    );
}
