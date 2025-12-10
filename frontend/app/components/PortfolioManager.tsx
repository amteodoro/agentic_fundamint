"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/app/context/AuthContext';
import {
    getPortfolios,
    createPortfolio,
    deletePortfolio,
    removeStockFromPortfolio,
    Portfolio,
    Holding,
} from '@/lib/api/portfolio';

interface StockQuote {
    ticker: string;
    price: number;
    change: number;
    changePercent: number;
}

interface PortfolioManagerProps {
    onSelectStock?: (ticker: string) => void;
}

export function PortfolioManager({ onSelectStock }: PortfolioManagerProps) {
    const { user, isAuthenticated } = useAuth();
    const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
    const [stockQuotes, setStockQuotes] = useState<Record<string, StockQuote>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newPortfolioName, setNewPortfolioName] = useState('');
    const [newPortfolioDescription, setNewPortfolioDescription] = useState('');
    const [creating, setCreating] = useState(false);
    const [expandedPortfolioId, setExpandedPortfolioId] = useState<string | null>(null);

    const fetchPortfolios = useCallback(async () => {
        if (!isAuthenticated || user?.is_guest) {
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            const response = await getPortfolios();
            setPortfolios(response.portfolios);
            setError(null);

            // Fetch stock quotes for all holdings
            const allTickers = new Set<string>();
            response.portfolios.forEach(p => {
                p.holdings.forEach(h => allTickers.add(h.ticker));
            });

            if (allTickers.size > 0) {
                fetchStockQuotes(Array.from(allTickers));
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load portfolios');
        } finally {
            setLoading(false);
        }
    }, [isAuthenticated, user?.is_guest]);

    const fetchStockQuotes = async (tickers: string[]) => {
        const quotes: Record<string, StockQuote> = {};

        // Fetch quotes for each ticker using the new /quote endpoint
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

    useEffect(() => {
        fetchPortfolios();
    }, [fetchPortfolios]);

    const handleCreatePortfolio = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newPortfolioName.trim()) return;

        try {
            setCreating(true);
            await createPortfolio({
                name: newPortfolioName.trim(),
                description: newPortfolioDescription.trim() || undefined,
            });
            setNewPortfolioName('');
            setNewPortfolioDescription('');
            setShowCreateForm(false);
            await fetchPortfolios();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create portfolio');
        } finally {
            setCreating(false);
        }
    };

    const handleDeletePortfolio = async (portfolioId: string) => {
        if (!confirm('Are you sure you want to delete this portfolio?')) return;

        try {
            await deletePortfolio(portfolioId);
            await fetchPortfolios();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete portfolio');
        }
    };

    const handleRemoveStock = async (portfolioId: string, ticker: string) => {
        try {
            await removeStockFromPortfolio(portfolioId, ticker);
            await fetchPortfolios();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to remove stock');
        }
    };

    const toggleExpanded = (portfolioId: string) => {
        setExpandedPortfolioId(expandedPortfolioId === portfolioId ? null : portfolioId);
    };

    const calculatePnL = (holding: Holding): { value: number; percent: number } | null => {
        const quote = stockQuotes[holding.ticker];
        if (!quote || !holding.average_cost || !holding.shares) return null;

        const currentValue = quote.price * holding.shares;
        const costBasis = holding.average_cost * holding.shares;
        const pnl = currentValue - costBasis;
        const pnlPercent = ((currentValue - costBasis) / costBasis) * 100;

        return { value: pnl, percent: pnlPercent };
    };

    const calculatePortfolioValue = (portfolio: Portfolio): { total: number; pnl: number; pnlPercent: number } => {
        let total = 0;
        let costBasis = 0;

        portfolio.holdings.forEach(holding => {
            const quote = stockQuotes[holding.ticker];
            if (quote && holding.shares) {
                total += quote.price * holding.shares;
                if (holding.average_cost) {
                    costBasis += holding.average_cost * holding.shares;
                }
            }
        });

        const pnl = costBasis > 0 ? total - costBasis : 0;
        const pnlPercent = costBasis > 0 ? (pnl / costBasis) * 100 : 0;

        return { total, pnl, pnlPercent };
    };

    const formatCurrency = (value: number): string => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
        }).format(value);
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
                    <CardTitle className="text-gray-900">Portfolios</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8">
                        <p className="text-gray-600 mb-4">
                            Create an account to save and manage your investment portfolios.
                        </p>
                        <Button
                            variant="outline"
                            className="border-emerald-500 text-emerald-600 hover:bg-emerald-50"
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
                    <CardTitle className="text-gray-900">Portfolios</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8">
                        <p className="text-gray-600 mb-4">
                            Sign in to access your portfolios.
                        </p>
                        <Button
                            variant="outline"
                            className="border-emerald-500 text-emerald-600 hover:bg-emerald-50"
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
                <CardTitle className="text-gray-900">My Portfolios</CardTitle>
                <Button
                    size="sm"
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                    {showCreateForm ? 'Cancel' : '+ New Portfolio'}
                </Button>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
                {error && (
                    <div className="p-3 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200">
                        {error}
                    </div>
                )}

                {/* Create Portfolio Form */}
                {showCreateForm && (
                    <form onSubmit={handleCreatePortfolio} className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="space-y-2">
                            <Label htmlFor="portfolioName" className="text-gray-700">Portfolio Name</Label>
                            <Input
                                id="portfolioName"
                                value={newPortfolioName}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPortfolioName(e.target.value)}
                                placeholder="e.g., Tech Growth"
                                required
                                className="bg-white border-gray-300 text-gray-900"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="portfolioDescription" className="text-gray-700">Description (optional)</Label>
                            <Input
                                id="portfolioDescription"
                                value={newPortfolioDescription}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPortfolioDescription(e.target.value)}
                                placeholder="e.g., High-growth technology stocks"
                                className="bg-white border-gray-300 text-gray-900"
                            />
                        </div>
                        <Button
                            type="submit"
                            disabled={creating}
                            className="w-full bg-emerald-600 hover:bg-emerald-700"
                        >
                            {creating ? 'Creating...' : 'Create Portfolio'}
                        </Button>
                    </form>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="text-center py-8">
                        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-emerald-500 border-r-transparent" />
                        <p className="mt-2 text-gray-500">Loading portfolios...</p>
                    </div>
                )}

                {/* Empty State */}
                {!loading && portfolios.length === 0 && (
                    <div className="text-center py-8">
                        <p className="text-gray-500">No portfolios yet. Create one to get started!</p>
                    </div>
                )}

                {/* Portfolio List */}
                {!loading && portfolios.length > 0 && (
                    <div className="space-y-3">
                        {portfolios.map((portfolio) => {
                            const portfolioValue = calculatePortfolioValue(portfolio);

                            return (
                                <div
                                    key={portfolio.id}
                                    className="border border-gray-200 rounded-lg overflow-hidden"
                                >
                                    {/* Portfolio Header */}
                                    <div
                                        className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                                        onClick={() => toggleExpanded(portfolio.id)}
                                    >
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3">
                                                <h3 className="font-semibold text-gray-900">{portfolio.name}</h3>
                                                {portfolioValue.total > 0 && (
                                                    <span className="text-sm font-medium text-gray-700">
                                                        {formatCurrency(portfolioValue.total)}
                                                    </span>
                                                )}
                                                {portfolioValue.pnl !== 0 && (
                                                    <span className={`text-sm font-medium ${portfolioValue.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                        {formatPercent(portfolioValue.pnlPercent)}
                                                    </span>
                                                )}
                                            </div>
                                            {portfolio.description && (
                                                <p className="text-sm text-gray-500">{portfolio.description}</p>
                                            )}
                                            <p className="text-xs text-gray-400 mt-1">
                                                {portfolio.holdings.length} {portfolio.holdings.length === 1 ? 'stock' : 'stocks'}
                                            </p>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-gray-400 text-sm">
                                                {expandedPortfolioId === portfolio.id ? '[-]' : '[+]'}
                                            </span>
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeletePortfolio(portfolio.id);
                                                }}
                                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                            >
                                                Delete
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Portfolio Holdings */}
                                    {expandedPortfolioId === portfolio.id && (
                                        <div className="p-4 bg-white border-t border-gray-100">
                                            {portfolio.holdings.length === 0 ? (
                                                <p className="text-sm text-gray-500 text-center py-4">
                                                    No stocks in this portfolio. Search for stocks to add them.
                                                </p>
                                            ) : (
                                                <div className="overflow-x-auto">
                                                    <table className="w-full text-sm">
                                                        <thead>
                                                            <tr className="border-b border-gray-100">
                                                                <th className="text-left py-2 px-2 text-gray-500 font-medium">Ticker</th>
                                                                <th className="text-right py-2 px-2 text-gray-500 font-medium">Shares</th>
                                                                <th className="text-right py-2 px-2 text-gray-500 font-medium">Avg Cost</th>
                                                                <th className="text-right py-2 px-2 text-gray-500 font-medium">Price</th>
                                                                <th className="text-right py-2 px-2 text-gray-500 font-medium">P&L</th>
                                                                <th className="text-right py-2 px-2"></th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {portfolio.holdings.map((holding) => {
                                                                const quote = stockQuotes[holding.ticker];
                                                                const pnl = calculatePnL(holding);

                                                                return (
                                                                    <tr key={holding.id} className="border-b border-gray-50 hover:bg-gray-50">
                                                                        <td className="py-3 px-2">
                                                                            <button
                                                                                onClick={() => onSelectStock?.(holding.ticker)}
                                                                                className="font-mono font-bold text-emerald-600 hover:text-emerald-700 transition-colors"
                                                                            >
                                                                                {holding.ticker}
                                                                            </button>
                                                                        </td>
                                                                        <td className="py-3 px-2 text-right text-gray-700">
                                                                            {holding.shares?.toLocaleString() || '-'}
                                                                        </td>
                                                                        <td className="py-3 px-2 text-right text-gray-700">
                                                                            {holding.average_cost ? formatCurrency(holding.average_cost) : '-'}
                                                                        </td>
                                                                        <td className="py-3 px-2 text-right">
                                                                            {quote ? (
                                                                                <div>
                                                                                    <span className="text-gray-900 font-medium">{formatCurrency(quote.price)}</span>
                                                                                    <span className={`text-xs ml-1 ${quote.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                                                        {formatPercent(quote.changePercent)}
                                                                                    </span>
                                                                                </div>
                                                                            ) : (
                                                                                <span className="text-gray-400">Loading...</span>
                                                                            )}
                                                                        </td>
                                                                        <td className="py-3 px-2 text-right">
                                                                            {pnl ? (
                                                                                <div className={pnl.value >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                                                    <div className="font-medium">{formatCurrency(pnl.value)}</div>
                                                                                    <div className="text-xs">{formatPercent(pnl.percent)}</div>
                                                                                </div>
                                                                            ) : (
                                                                                <span className="text-gray-400">-</span>
                                                                            )}
                                                                        </td>
                                                                        <td className="py-3 px-2 text-right">
                                                                            <Button
                                                                                size="sm"
                                                                                variant="ghost"
                                                                                onClick={() => handleRemoveStock(portfolio.id, holding.ticker)}
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
                            );
                        })}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export default PortfolioManager;
