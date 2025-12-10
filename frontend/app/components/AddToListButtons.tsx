"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/app/context/AuthContext';
import {
    getPortfolios,
    createPortfolio,
    addStockToPortfolio,
    Portfolio,
} from '@/lib/api/portfolio';
import {
    getWatchlists,
    createWatchlist,
    addStockToWatchlist,
    Watchlist,
} from '@/lib/api/watchlist';

interface AddToListButtonsProps {
    ticker: string;
    className?: string;
}

export function AddToListButtons({ ticker, className = '' }: AddToListButtonsProps) {
    const { user, isAuthenticated } = useAuth();
    const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
    const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
    const [showPortfolioDropdown, setShowPortfolioDropdown] = useState(false);
    const [showWatchlistDropdown, setShowWatchlistDropdown] = useState(false);
    const [showCreatePortfolio, setShowCreatePortfolio] = useState(false);
    const [showCreateWatchlist, setShowCreateWatchlist] = useState(false);
    const [showAddToPortfolioForm, setShowAddToPortfolioForm] = useState(false);
    const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(null);
    const [newPortfolioName, setNewPortfolioName] = useState('');
    const [newWatchlistName, setNewWatchlistName] = useState('');
    const [shares, setShares] = useState('');
    const [averageCost, setAverageCost] = useState('');
    const [loading, setLoading] = useState(false);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const portfolioRef = useRef<HTMLDivElement>(null);
    const watchlistRef = useRef<HTMLDivElement>(null);

    // Close dropdowns when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (portfolioRef.current && !portfolioRef.current.contains(event.target as Node)) {
                setShowPortfolioDropdown(false);
                setShowCreatePortfolio(false);
                setShowAddToPortfolioForm(false);
            }
            if (watchlistRef.current && !watchlistRef.current.contains(event.target as Node)) {
                setShowWatchlistDropdown(false);
                setShowCreateWatchlist(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    useEffect(() => {
        const fetchLists = async () => {
            if (!isAuthenticated || user?.is_guest) return;

            try {
                const [portfolioRes, watchlistRes] = await Promise.all([
                    getPortfolios(),
                    getWatchlists(),
                ]);
                setPortfolios(portfolioRes.portfolios);
                setWatchlists(watchlistRes.watchlists);
            } catch (err) {
                console.error('Failed to fetch lists:', err);
            }
        };

        fetchLists();
    }, [isAuthenticated, user?.is_guest]);

    const resetPortfolioForm = () => {
        setShares('');
        setAverageCost('');
        setSelectedPortfolioId(null);
        setShowAddToPortfolioForm(false);
        setNewPortfolioName('');
    };

    const handlePortfolioClick = () => {
        if (portfolios.length === 0) {
            setShowCreatePortfolio(true);
            setShowPortfolioDropdown(false);
        } else {
            setShowPortfolioDropdown(!showPortfolioDropdown);
            setShowCreatePortfolio(false);
        }
        setShowWatchlistDropdown(false);
        setShowCreateWatchlist(false);
        setShowAddToPortfolioForm(false);
    };

    const handleWatchlistClick = () => {
        if (watchlists.length === 0) {
            setShowCreateWatchlist(true);
            setShowWatchlistDropdown(false);
        } else {
            setShowWatchlistDropdown(!showWatchlistDropdown);
            setShowCreateWatchlist(false);
        }
        setShowPortfolioDropdown(false);
        setShowCreatePortfolio(false);
        setShowAddToPortfolioForm(false);
    };

    const handleSelectPortfolio = (portfolioId: string) => {
        setSelectedPortfolioId(portfolioId);
        setShowPortfolioDropdown(false);
        setShowAddToPortfolioForm(true);
    };

    const handleCreatePortfolio = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newPortfolioName.trim()) return;

        try {
            setLoading(true);
            const newPortfolio = await createPortfolio({ name: newPortfolioName.trim() });
            setPortfolios([...portfolios, newPortfolio]);
            setSelectedPortfolioId(newPortfolio.id);
            setNewPortfolioName('');
            setShowCreatePortfolio(false);
            setShowAddToPortfolioForm(true);
        } catch (err) {
            setErrorMessage(err instanceof Error ? err.message : 'Failed to create portfolio');
            setTimeout(() => setErrorMessage(null), 3000);
        } finally {
            setLoading(false);
        }
    };

    const handleAddToPortfolio = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedPortfolioId) return;

        try {
            setLoading(true);
            setErrorMessage(null);

            await addStockToPortfolio(selectedPortfolioId, {
                ticker,
                shares: shares ? parseFloat(shares) : undefined,
                average_cost: averageCost ? parseFloat(averageCost) : undefined,
            });

            const portfolio = portfolios.find((p: Portfolio) => p.id === selectedPortfolioId);
            setSuccessMessage(`Added ${ticker} to ${portfolio?.name || 'portfolio'}`);
            resetPortfolioForm();
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setErrorMessage(err instanceof Error ? err.message : 'Failed to add to portfolio');
            setTimeout(() => setErrorMessage(null), 3000);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateWatchlist = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newWatchlistName.trim()) return;

        try {
            setLoading(true);
            const newWatchlist = await createWatchlist({ name: newWatchlistName.trim() });
            // Add stock to the newly created watchlist
            await addStockToWatchlist(newWatchlist.id, { ticker });
            setWatchlists([...watchlists, newWatchlist]);
            setSuccessMessage(`Created "${newWatchlistName}" and added ${ticker}`);
            setNewWatchlistName('');
            setShowCreateWatchlist(false);
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setErrorMessage(err instanceof Error ? err.message : 'Failed to create watchlist');
            setTimeout(() => setErrorMessage(null), 3000);
        } finally {
            setLoading(false);
        }
    };

    const handleAddToWatchlist = async (watchlistId: string) => {
        try {
            setLoading(true);
            setErrorMessage(null);
            await addStockToWatchlist(watchlistId, { ticker });
            const watchlist = watchlists.find((w: Watchlist) => w.id === watchlistId);
            setSuccessMessage(`Added ${ticker} to ${watchlist?.name || 'watchlist'}`);
            setShowWatchlistDropdown(false);
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setErrorMessage(err instanceof Error ? err.message : 'Failed to add to watchlist');
            setTimeout(() => setErrorMessage(null), 3000);
        } finally {
            setLoading(false);
        }
    };

    // Don't show for guests or unauthenticated users
    if (!isAuthenticated || user?.is_guest) {
        return null;
    }

    const selectedPortfolio = portfolios.find((p: Portfolio) => p.id === selectedPortfolioId);

    return (
        <div className={`flex items-center gap-2 ${className}`}>
            {/* Success/Error Messages */}
            {successMessage && (
                <span className="text-xs text-emerald-700 bg-emerald-100 px-2 py-1 rounded border border-emerald-200">
                    {successMessage}
                </span>
            )}
            {errorMessage && (
                <span className="text-xs text-red-700 bg-red-100 px-2 py-1 rounded border border-red-200">
                    {errorMessage}
                </span>
            )}

            {/* Add to Portfolio */}
            <div className="relative" ref={portfolioRef}>
                <Button
                    size="sm"
                    variant="outline"
                    disabled={loading}
                    onClick={handlePortfolioClick}
                    className="border-emerald-500 text-emerald-600 hover:bg-emerald-50 text-xs"
                >
                    + Portfolio
                </Button>

                {/* Create Portfolio Modal */}
                {showCreatePortfolio && (
                    <div className="absolute z-50 mt-2 right-0 w-72 bg-white border border-gray-200 rounded-lg shadow-xl p-4">
                        <h3 className="font-semibold text-gray-900 mb-3">Create New Portfolio</h3>
                        <form onSubmit={handleCreatePortfolio}>
                            <div className="space-y-3">
                                <div>
                                    <Label htmlFor="portfolioName" className="text-gray-700 text-sm">Portfolio Name</Label>
                                    <Input
                                        id="portfolioName"
                                        value={newPortfolioName}
                                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPortfolioName(e.target.value)}
                                        placeholder="e.g., Tech Growth"
                                        required
                                        autoFocus
                                        className="mt-1 bg-white border-gray-300 text-gray-900"
                                    />
                                </div>
                                <div className="flex gap-2">
                                    <Button
                                        type="submit"
                                        disabled={loading || !newPortfolioName.trim()}
                                        size="sm"
                                        className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                                    >
                                        {loading ? 'Creating...' : 'Next'}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setShowCreatePortfolio(false)}
                                        className="border-gray-300 text-gray-700"
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </div>
                        </form>
                    </div>
                )}

                {/* Add to Portfolio Form (with shares & cost) */}
                {showAddToPortfolioForm && (
                    <div className="absolute z-50 mt-2 right-0 w-80 bg-white border border-gray-200 rounded-lg shadow-xl p-4">
                        <h3 className="font-semibold text-gray-900 mb-1">Add {ticker} to Portfolio</h3>
                        <p className="text-xs text-gray-500 mb-3">
                            Adding to: <span className="font-medium">{selectedPortfolio?.name}</span>
                        </p>
                        <form onSubmit={handleAddToPortfolio}>
                            <div className="space-y-3">
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <Label htmlFor="shares" className="text-gray-700 text-sm">Shares (optional)</Label>
                                        <Input
                                            id="shares"
                                            type="number"
                                            step="any"
                                            min="0"
                                            value={shares}
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setShares(e.target.value)}
                                            placeholder="e.g., 100"
                                            className="mt-1 bg-white border-gray-300 text-gray-900"
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="avgCost" className="text-gray-700 text-sm">Avg Cost (optional)</Label>
                                        <Input
                                            id="avgCost"
                                            type="number"
                                            step="any"
                                            min="0"
                                            value={averageCost}
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAverageCost(e.target.value)}
                                            placeholder="e.g., 150.00"
                                            className="mt-1 bg-white border-gray-300 text-gray-900"
                                        />
                                    </div>
                                </div>
                                <p className="text-xs text-gray-500">
                                    Enter your position details to track P&L, or leave blank to just add the ticker.
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        type="submit"
                                        disabled={loading}
                                        size="sm"
                                        className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                                    >
                                        {loading ? 'Adding...' : 'Add to Portfolio'}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={resetPortfolioForm}
                                        className="border-gray-300 text-gray-700"
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </div>
                        </form>
                    </div>
                )}

                {/* Portfolio Dropdown */}
                {showPortfolioDropdown && (
                    <div className="absolute z-50 mt-2 right-0 w-56 bg-white border border-gray-200 rounded-lg shadow-xl overflow-hidden">
                        <div className="max-h-48 overflow-y-auto">
                            {portfolios.map((portfolio: Portfolio) => (
                                <button
                                    key={portfolio.id}
                                    onClick={() => handleSelectPortfolio(portfolio.id)}
                                    className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
                                >
                                    {portfolio.name}
                                    <span className="text-xs text-gray-400 ml-2">
                                        ({portfolio.holdings.length} stocks)
                                    </span>
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={() => {
                                setShowPortfolioDropdown(false);
                                setShowCreatePortfolio(true);
                            }}
                            className="w-full px-4 py-2.5 text-left text-sm text-emerald-600 hover:bg-emerald-50 border-t border-gray-200 font-medium"
                        >
                            + Create New Portfolio
                        </button>
                    </div>
                )}
            </div>

            {/* Add to Watchlist */}
            <div className="relative" ref={watchlistRef}>
                <Button
                    size="sm"
                    variant="outline"
                    disabled={loading}
                    onClick={handleWatchlistClick}
                    className="border-blue-500 text-blue-600 hover:bg-blue-50 text-xs"
                >
                    + Watchlist
                </Button>

                {/* Create Watchlist Modal */}
                {showCreateWatchlist && (
                    <div className="absolute z-50 mt-2 right-0 w-72 bg-white border border-gray-200 rounded-lg shadow-xl p-4">
                        <h3 className="font-semibold text-gray-900 mb-3">Create New Watchlist</h3>
                        <form onSubmit={handleCreateWatchlist}>
                            <div className="space-y-3">
                                <div>
                                    <Label htmlFor="watchlistName" className="text-gray-700 text-sm">Watchlist Name</Label>
                                    <Input
                                        id="watchlistName"
                                        value={newWatchlistName}
                                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewWatchlistName(e.target.value)}
                                        placeholder="e.g., Tech to Watch"
                                        required
                                        autoFocus
                                        className="mt-1 bg-white border-gray-300 text-gray-900"
                                    />
                                </div>
                                <p className="text-xs text-gray-500">
                                    {ticker} will be added automatically
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        type="submit"
                                        disabled={loading || !newWatchlistName.trim()}
                                        size="sm"
                                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                                    >
                                        {loading ? 'Creating...' : 'Create & Add'}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setShowCreateWatchlist(false)}
                                        className="border-gray-300 text-gray-700"
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </div>
                        </form>
                    </div>
                )}

                {/* Watchlist Dropdown */}
                {showWatchlistDropdown && (
                    <div className="absolute z-50 mt-2 right-0 w-56 bg-white border border-gray-200 rounded-lg shadow-xl overflow-hidden">
                        <div className="max-h-48 overflow-y-auto">
                            {watchlists.map((watchlist: Watchlist) => (
                                <button
                                    key={watchlist.id}
                                    onClick={() => handleAddToWatchlist(watchlist.id)}
                                    className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
                                >
                                    {watchlist.name}
                                    <span className="text-xs text-gray-400 ml-2">
                                        ({watchlist.items.length} stocks)
                                    </span>
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={() => {
                                setShowWatchlistDropdown(false);
                                setShowCreateWatchlist(true);
                            }}
                            className="w-full px-4 py-2.5 text-left text-sm text-blue-600 hover:bg-blue-50 border-t border-gray-200 font-medium"
                        >
                            + Create New Watchlist
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AddToListButtons;
