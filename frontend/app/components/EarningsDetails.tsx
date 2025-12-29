"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
    getStockEarnings,
    StockEarningsResponse,
    HistoricalEarning,
    formatEarningsTime,
    getDaysUntilEarnings,
    formatDaysUntilEarnings,
    getEarningsUrgencyClass,
    getSurpriseInfo,
} from '@/lib/api/earnings';

interface EarningsDetailsProps {
    ticker: string;
    onClose?: () => void;
    onNavigateToStock?: (ticker: string) => void;
}

export function EarningsDetails({ ticker, onClose, onNavigateToStock }: EarningsDetailsProps) {
    const [data, setData] = useState<StockEarningsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showAllHistory, setShowAllHistory] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);
                const result = await getStockEarnings(ticker);
                setData(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load earnings data');
            } finally {
                setLoading(false);
            }
        };

        if (ticker) {
            fetchData();
        }
    }, [ticker]);

    const formatDate = (dateStr?: string | null): string => {
        if (!dateStr) return 'TBD';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                year: 'numeric',
            });
        } catch {
            return dateStr;
        }
    };

    const formatCurrency = (value?: number | null): string => {
        if (value === null || value === undefined) return '-';
        if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
        if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
        if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
        return `$${value.toLocaleString()}`;
    };

    const formatEps = (value?: number | null): string => {
        if (value === null || value === undefined) return '-';
        return `$${value.toFixed(2)}`;
    };

    const formatPercent = (value?: number | null): string => {
        if (value === null || value === undefined) return '-';
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}%`;
    };

    const daysUntil = getDaysUntilEarnings(data?.nextEarningsDate);
    const urgencyClass = getEarningsUrgencyClass(daysUntil);
    const displayedHistory = showAllHistory ? data?.history : data?.history.slice(0, 4);

    return (
        <Card className="bg-white border-gray-200 shadow-xl overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-2xl font-bold">{ticker}</CardTitle>
                        <p className="text-emerald-100 text-sm mt-1">Earnings Analysis</p>
                    </div>
                    <div className="flex gap-2">
                        {onNavigateToStock && (
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => onNavigateToStock(ticker)}
                                className="border-white/30 text-white hover:bg-white/20"
                            >
                                View Stock
                            </Button>
                        )}
                        {onClose && (
                            <Button
                                size="sm"
                                variant="ghost"
                                onClick={onClose}
                                className="text-white hover:bg-white/20"
                            >
                                Close
                            </Button>
                        )}
                    </div>
                </div>
            </CardHeader>

            <CardContent className="p-0">
                {/* Loading State */}
                {loading && (
                    <div className="flex items-center justify-center py-16">
                        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-emerald-500 border-r-transparent" />
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="p-6 text-center">
                        <p className="text-red-600 mb-4">{error}</p>
                    </div>
                )}

                {/* Content */}
                {!loading && !error && data && (
                    <div className="divide-y divide-gray-100">
                        {/* Next Earnings Section */}
                        <div className="p-6 bg-gray-50">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
                                Upcoming Earnings
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-3">
                                    <div>
                                        <p className="text-xs text-gray-500">Next Earnings Date</p>
                                        <p className="text-xl font-bold text-gray-900">
                                            {formatDate(data.nextEarningsDate)}
                                        </p>
                                        <p className={`text-sm font-medium ${urgencyClass}`}>
                                            {formatDaysUntilEarnings(daysUntil)}
                                        </p>
                                    </div>
                                    {data.nextEarningsTime && (
                                        <div>
                                            <p className="text-xs text-gray-500">Announcement Time</p>
                                            <p className="text-sm font-medium text-gray-900">
                                                {formatEarningsTime(data.nextEarningsTime)}
                                            </p>
                                        </div>
                                    )}
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-white rounded-lg p-4 shadow-sm">
                                        <p className="text-xs text-gray-500 mb-1">EPS Estimate</p>
                                        <p className="text-2xl font-bold text-gray-900">
                                            {formatEps(data.epsEstimate)}
                                        </p>
                                    </div>
                                    <div className="bg-white rounded-lg p-4 shadow-sm">
                                        <p className="text-xs text-gray-500 mb-1">Revenue Estimate</p>
                                        <p className="text-2xl font-bold text-gray-900">
                                            {formatCurrency(data.revenueEstimate)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Performance Stats */}
                        <div className="p-6">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
                                Historical Performance
                            </h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="text-center p-4 bg-gray-50 rounded-lg">
                                    <p className="text-3xl font-bold text-gray-900">
                                        {data.stats.totalReported}
                                    </p>
                                    <p className="text-xs text-gray-500 uppercase">Reports</p>
                                </div>
                                <div className="text-center p-4 bg-green-50 rounded-lg">
                                    <p className="text-3xl font-bold text-green-600">
                                        {data.stats.beats}
                                    </p>
                                    <p className="text-xs text-green-700 uppercase">Beats</p>
                                </div>
                                <div className="text-center p-4 bg-red-50 rounded-lg">
                                    <p className="text-3xl font-bold text-red-600">
                                        {data.stats.misses}
                                    </p>
                                    <p className="text-xs text-red-700 uppercase">Misses</p>
                                </div>
                                <div className="text-center p-4 bg-emerald-50 rounded-lg">
                                    <p className="text-3xl font-bold text-emerald-600">
                                        {data.stats.beatRate !== null
                                            ? `${data.stats.beatRate.toFixed(0)}%`
                                            : '-'
                                        }
                                    </p>
                                    <p className="text-xs text-emerald-700 uppercase">Beat Rate</p>
                                </div>
                            </div>
                        </div>

                        {/* Historical Earnings Table */}
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                    Earnings History
                                </h3>
                                {data.history.length > 4 && (
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => setShowAllHistory(!showAllHistory)}
                                        className="text-emerald-600 hover:text-emerald-700"
                                    >
                                        {showAllHistory ? 'Show Less' : `Show All (${data.history.length})`}
                                    </Button>
                                )}
                            </div>

                            {data.history.length === 0 ? (
                                <p className="text-gray-500 text-center py-4">No historical data available</p>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-gray-200">
                                                <th className="text-left py-3 px-2 text-gray-500 font-medium">Date</th>
                                                <th className="text-right py-3 px-2 text-gray-500 font-medium">EPS Est.</th>
                                                <th className="text-right py-3 px-2 text-gray-500 font-medium">EPS Actual</th>
                                                <th className="text-right py-3 px-2 text-gray-500 font-medium">Surprise</th>
                                                <th className="text-right py-3 px-2 text-gray-500 font-medium">Revenue</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {displayedHistory?.map((earning, idx) => {
                                                const surprise = getSurpriseInfo(earning.epsSurprisePercent);

                                                return (
                                                    <tr
                                                        key={`${earning.date}-${idx}`}
                                                        className="border-b border-gray-100 hover:bg-gray-50"
                                                    >
                                                        <td className="py-3 px-2 text-gray-900">
                                                            {formatDate(earning.date)}
                                                        </td>
                                                        <td className="py-3 px-2 text-right text-gray-600">
                                                            {formatEps(earning.epsEstimate)}
                                                        </td>
                                                        <td className="py-3 px-2 text-right font-semibold text-gray-900">
                                                            {formatEps(earning.epsActual)}
                                                        </td>
                                                        <td className={`py-3 px-2 text-right font-medium ${surprise.colorClass}`}>
                                                            {surprise.text}
                                                        </td>
                                                        <td className="py-3 px-2 text-right text-gray-600">
                                                            {formatCurrency(earning.revenue)}
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                        {/* Earnings Beat Visualization */}
                        {data.history.length > 0 && (
                            <div className="p-6 bg-gray-50">
                                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
                                    EPS Surprise Trend
                                </h3>
                                <div className="flex items-end justify-center gap-1 h-20">
                                    {data.history.slice(0, 8).reverse().map((earning, idx) => {
                                        const surprise = earning.epsSurprisePercent;
                                        const height = surprise !== null && surprise !== undefined
                                            ? Math.min(Math.abs(surprise) * 4, 100)
                                            : 10;
                                        const isPositive = surprise !== null && surprise !== undefined && surprise > 0;

                                        return (
                                            <div
                                                key={`bar-${idx}`}
                                                className="flex flex-col items-center gap-1"
                                            >
                                                <div
                                                    className={`w-8 rounded-t transition-all ${isPositive
                                                            ? 'bg-green-500'
                                                            : surprise !== null && surprise !== undefined
                                                                ? 'bg-red-500'
                                                                : 'bg-gray-300'
                                                        }`}
                                                    style={{ height: `${Math.max(height, 8)}%` }}
                                                    title={`${formatPercent(surprise)}`}
                                                />
                                                <span className="text-[10px] text-gray-400">
                                                    Q{(8 - idx - 1) || 'L'}
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                                <p className="text-xs text-gray-500 text-center mt-2">
                                    Last {Math.min(data.history.length, 8)} quarters (most recent on right)
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export default EarningsDetails;
