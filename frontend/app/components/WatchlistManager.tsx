"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/app/context/AuthContext';
import { useChatContext, getCurrencySymbol } from '@/app/context/ChatContext';
import {
    getWatchlists,
    createWatchlist,
    deleteWatchlist,
    removeStockFromWatchlist,
    Watchlist,
} from '@/lib/api/watchlist';
import {
    getBulkEarningsDates,
    BulkEarningsItem,
    formatDaysUntilEarnings,
    getEarningsUrgencyClass,
} from '@/lib/api/earnings';

interface StockQuote {
    ticker: string;
    price: number;
    change: number;
    changePercent: number;
}

interface WatchlistManagerProps {
    onSelectStock?: (ticker: string) => void;
}

export function WatchlistManager({ onSelectStock }: WatchlistManagerProps) {
    const { user, isAuthenticated } = useAuth();
    const { currency, convertValue } = useChatContext();
    const currencySymbol = getCurrencySymbol(currency);

    const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
    const [stockQuotes, setStockQuotes] = useState<Record<string, StockQuote>>({});
    const [earningsDates, setEarningsDates] = useState<Record<string, BulkEarningsItem>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newWatchlistName, setNewWatchlistName] = useState('');
    const [creating, setCreating] = useState(false);
    const [expandedWatchlistId, setExpandedWatchlistId] = useState<string | null>(null);

    const fetchWatchlists = useCallback(async () => {
        if (!isAuthenticated || user?.is_guest) {
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            const response = await getWatchlists();
            setWatchlists(response.watchlists);
            setError(null);

            // Fetch stock quotes for all items
            const allTickers = new Set<string>();
            response.watchlists.forEach(w => {
                w.items.forEach(item => allTickers.add(item.ticker));
            });

            if (allTickers.size > 0) {
                fetchStockQuotes(Array.from(allTickers));
                fetchEarningsDates(Array.from(allTickers));
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load watchlists');
        } finally {
            setLoading(false);
        }
    }, [isAuthenticated, user?.is_guest]);

    const fetchStockQuotes = async (tickers: string[]) => {
        const quotes: Record<string, StockQuote> = {};

        await Promise.all(
            tickers.map(async (ticker) => {
                try {
                    const response = await fetch(`http://localhost:8100/api/stock/${ticker}/quote`);
                    if (response.ok) {
                        const data = await response.json();
                        quotes[ticker] = {
                            ticker: data.ticker,
                            price: data.price,
                            change: data.change,
                            changePercent: data.changePercent,
                        };
                    }
                } catch {
                    // Silently fail for individual quotes
                }
            })
        );

        setStockQuotes(prev => ({ ...prev, ...quotes }));
    };

    const fetchEarningsDates = async (tickers: string[]) => {
        try {
            const response = await getBulkEarningsDates(tickers);
            const earningsMap: Record<string, BulkEarningsItem> = {};
            response.earnings.forEach(e => {
                earningsMap[e.symbol] = e;
            });
            setEarningsDates(prev => ({ ...prev, ...earningsMap }));
        } catch {
            // Silently fail - earnings dates are supplementary
        }
    };

    useEffect(() => {
        fetchWatchlists();
    }, [fetchWatchlists]);

    const handleCreateWatchlist = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newWatchlistName.trim()) return;

        try {
            setCreating(true);
            await createWatchlist({ name: newWatchlistName.trim() });
            setNewWatchlistName('');
            setShowCreateForm(false);
            await fetchWatchlists();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create watchlist');
        } finally {
            setCreating(false);
        }
    };

    const handleDeleteWatchlist = async (watchlistId: string) => {
        if (!confirm('Are you sure you want to delete this watchlist?')) return;

        try {
            await deleteWatchlist(watchlistId);
            await fetchWatchlists();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete watchlist');
        }
    };

    const handleRemoveStock = async (watchlistId: string, ticker: string) => {
        try {
            await removeStockFromWatchlist(watchlistId, ticker);
            await fetchWatchlists();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to remove stock');
        }
    };

    const toggleExpanded = (watchlistId: string) => {
        setExpandedWatchlistId(expandedWatchlistId === watchlistId ? null : watchlistId);
    };

    const formatCurrency = (value: number): string => {
        const converted = convertValue(value, 'USD');
        if (converted === null) return 'N/A';
        return `${currencySymbol}${converted.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    };

    const formatPercent = (value: number): string => {
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}%`;
    };

    // Guest user message
    if (user?.is_guest) {
        return (
            <Card className="bg-white border-gray-200 shadow-sm">
                <CardHeader>
                    <CardTitle className="text-gray-900">Watchlists</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8">
                        <p className="text-gray-600 mb-4">
                            Create an account to save stocks to your watchlist.
                        </p>
                        <Button
                            variant="outline"
                            className="border-blue-500 text-blue-600 hover:bg-blue-50"
                            onClick={() => window.location.href = '/register'}
                        >
                            Create Account
                        </Button>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Not authenticated
    if (!isAuthenticated) {
        return (
            <Card className="bg-white border-gray-200 shadow-sm">
                <CardHeader>
                    <CardTitle className="text-gray-900">Watchlists</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8">
                        <p className="text-gray-600 mb-4">
                            Sign in to access your watchlists.
                        </p>
                        <Button
                            variant="outline"
                            className="border-blue-500 text-blue-600 hover:bg-blue-50"
                            onClick={() => window.location.href = '/login'}
                        >
                            Sign In
                        </Button>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="bg-white border-gray-200 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between border-b border-gray-100">
                <CardTitle className="text-gray-900">My Watchlists</CardTitle>
                <Button
                    size="sm"
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                    {showCreateForm ? 'Cancel' : '+ New Watchlist'}
                </Button>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
                {error && (
                    <div className="p-3 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200">
                        {error}
                    </div>
                )}

                {/* Create Watchlist Form */}
                {showCreateForm && (
                    <form onSubmit={handleCreateWatchlist} className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="space-y-2">
                            <Label htmlFor="watchlistName" className="text-gray-700">Watchlist Name</Label>
                            <Input
                                id="watchlistName"
                                value={newWatchlistName}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewWatchlistName(e.target.value)}
                                placeholder="e.g., Tech to Watch"
                                required
                                className="bg-white border-gray-300 text-gray-900"
                            />
                        </div>
                        <Button
                            type="submit"
                            disabled={creating}
                            className="w-full bg-blue-600 hover:bg-blue-700"
                        >
                            {creating ? 'Creating...' : 'Create Watchlist'}
                        </Button>
                    </form>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="text-center py-8">
                        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-blue-500 border-r-transparent" />
                        <p className="mt-2 text-gray-500">Loading watchlists...</p>
                    </div>
                )}

                {/* Empty State */}
                {!loading && watchlists.length === 0 && (
                    <div className="text-center py-8">
                        <p className="text-gray-500">No watchlists yet. Create one to track stocks!</p>
                    </div>
                )}

                {/* Watchlist List */}
                {!loading && watchlists.length > 0 && (
                    <div className="space-y-3">
                        {watchlists.map((watchlist) => (
                            <div
                                key={watchlist.id}
                                className="border border-gray-200 rounded-lg overflow-hidden"
                            >
                                {/* Watchlist Header */}
                                <div
                                    className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                                    onClick={() => toggleExpanded(watchlist.id)}
                                >
                                    <div>
                                        <h3 className="font-semibold text-gray-900">{watchlist.name}</h3>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {watchlist.items.length} {watchlist.items.length === 1 ? 'stock' : 'stocks'}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-gray-400 text-sm">
                                            {expandedWatchlistId === watchlist.id ? '[-]' : '[+]'}
                                        </span>
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteWatchlist(watchlist.id);
                                            }}
                                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                        >
                                            Delete
                                        </Button>
                                    </div>
                                </div>

                                {/* Watchlist Items */}
                                {expandedWatchlistId === watchlist.id && (
                                    <div className="p-4 bg-white border-t border-gray-100">
                                        {watchlist.items.length === 0 ? (
                                            <p className="text-sm text-gray-500 text-center py-4">
                                                No stocks in this watchlist. Search for stocks to add them.
                                            </p>
                                        ) : (
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-sm">
                                                    <thead>
                                                        <tr className="border-b border-gray-100">
                                                            <th className="text-left py-2 px-2 text-gray-500 font-medium">Ticker</th>
                                                            <th className="text-right py-2 px-2 text-gray-500 font-medium">Current Price</th>
                                                            <th className="text-right py-2 px-2 text-gray-500 font-medium">Day Change</th>
                                                            <th className="text-right py-2 px-2 text-gray-500 font-medium">Target</th>
                                                            <th className="text-right py-2 px-2 text-gray-500 font-medium">Earnings</th>
                                                            <th className="text-left py-2 px-2 text-gray-500 font-medium">Notes</th>
                                                            <th className="text-right py-2 px-2"></th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {watchlist.items.map((item) => {
                                                            const quote = stockQuotes[item.ticker];
                                                            const targetUpside = item.target_price && quote
                                                                ? ((item.target_price - quote.price) / quote.price) * 100
                                                                : null;
                                                            const earningsInfo = earningsDates[item.ticker];

                                                            return (
                                                                <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50">
                                                                    <td className="py-3 px-2">
                                                                        <button
                                                                            onClick={() => onSelectStock?.(item.ticker)}
                                                                            className="font-mono font-bold text-blue-600 hover:text-blue-700 transition-colors"
                                                                        >
                                                                            {item.ticker}
                                                                        </button>
                                                                    </td>
                                                                    <td className="py-3 px-2 text-right">
                                                                        {quote ? (
                                                                            <span className="text-gray-900 font-medium">{formatCurrency(quote.price)}</span>
                                                                        ) : (
                                                                            <span className="text-gray-400">Loading...</span>
                                                                        )}
                                                                    </td>
                                                                    <td className="py-3 px-2 text-right">
                                                                        {quote ? (
                                                                            <span className={quote.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                                                {formatPercent(quote.changePercent)}
                                                                            </span>
                                                                        ) : (
                                                                            <span className="text-gray-400">-</span>
                                                                        )}
                                                                    </td>
                                                                    <td className="py-3 px-2 text-right">
                                                                        {item.target_price ? (
                                                                            <div>
                                                                                <span className="text-gray-900">{formatCurrency(item.target_price)}</span>
                                                                                {targetUpside !== null && (
                                                                                    <span className={`text-xs ml-1 ${targetUpside >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                                                        ({formatPercent(targetUpside)})
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                        ) : (
                                                                            <span className="text-gray-400">-</span>
                                                                        )}
                                                                    </td>
                                                                    <td className="py-3 px-2 text-right">
                                                                        {earningsInfo?.nextEarningsDate ? (
                                                                            <div className={`text-xs ${getEarningsUrgencyClass(earningsInfo.daysUntilEarnings)}`}>
                                                                                {formatDaysUntilEarnings(earningsInfo.daysUntilEarnings)}
                                                                            </div>
                                                                        ) : (
                                                                            <span className="text-gray-400 text-xs">-</span>
                                                                        )}
                                                                    </td>
                                                                    <td className="py-3 px-2 text-left text-gray-600 max-w-[200px] truncate">
                                                                        {item.notes || '-'}
                                                                    </td>
                                                                    <td className="py-3 px-2 text-right">
                                                                        <Button
                                                                            size="sm"
                                                                            variant="ghost"
                                                                            onClick={() => handleRemoveStock(watchlist.id, item.ticker)}
                                                                            className="text-red-500 hover:text-red-600 hover:bg-red-50 text-xs h-7"
                                                                        >
                                                                            Remove
                                                                        </Button>
                                                                    </td>
                                                                </tr>
                                                            );
                                                        })}
                                                    </tbody>
                                                </table>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export default WatchlistManager;
