"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
    getEarningsCalendar,
    EarningsCalendarResponse,
    DailyEarnings,
    EarningEvent,
    CalendarView,
    formatEarningsTimeShort,
    getDaysUntilEarnings,
} from '@/lib/api/earnings';

interface EarningsCalendarProps {
    onSelectStock?: (ticker: string) => void;
    defaultView?: CalendarView;
}

export function EarningsCalendar({ onSelectStock, defaultView = 'weekly' }: EarningsCalendarProps) {
    const [view, setView] = useState<CalendarView>(defaultView);
    const [calendarData, setCalendarData] = useState<EarningsCalendarResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedDate, setSelectedDate] = useState<string | null>(null);
    const [selectedEarning, setSelectedEarning] = useState<EarningEvent | null>(null);

    const fetchCalendar = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getEarningsCalendar(view);
            setCalendarData(data);

            // Auto-select today if it has earnings
            const today = new Date().toISOString().split('T')[0];
            const todayData = data.days.find(d => d.date === today);
            if (todayData && todayData.count > 0) {
                setSelectedDate(today);
            } else {
                // Select first day with earnings
                const firstWithEarnings = data.days.find(d => d.count > 0);
                if (firstWithEarnings) {
                    setSelectedDate(firstWithEarnings.date);
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load earnings calendar');
        } finally {
            setLoading(false);
        }
    }, [view]);

    useEffect(() => {
        fetchCalendar();
    }, [fetchCalendar]);

    const formatDate = (dateStr: string): string => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
        });
    };

    const formatFullDate = (dateStr: string): string => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
            year: 'numeric',
        });
    };

    const isToday = (dateStr: string): boolean => {
        const today = new Date().toISOString().split('T')[0];
        return dateStr === today;
    };

    const isWeekend = (dayOfWeek: string): boolean => {
        return dayOfWeek === 'Saturday' || dayOfWeek === 'Sunday';
    };

    const getTimeColor = (time?: string | null): string => {
        if (!time) return 'bg-gray-100 text-gray-600';
        switch (time.toLowerCase()) {
            case 'bmo':
                return 'bg-amber-100 text-amber-700';
            case 'amc':
                return 'bg-indigo-100 text-indigo-700';
            case 'dmh':
                return 'bg-emerald-100 text-emerald-700';
            default:
                return 'bg-gray-100 text-gray-600';
        }
    };

    const formatCurrency = (value?: number | null): string => {
        if (value === null || value === undefined) return '-';
        if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
        if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
        return `$${value.toLocaleString()}`;
    };

    const formatEps = (value?: number | null): string => {
        if (value === null || value === undefined) return '-';
        return `$${value.toFixed(2)}`;
    };

    const selectedDayData = calendarData?.days.find(d => d.date === selectedDate);

    // Filter out weekends for week view
    const displayDays = calendarData?.days.filter(d =>
        view === 'monthly' || !isWeekend(d.dayOfWeek)
    ) || [];

    return (
        <Card className="bg-white border-gray-200 shadow-lg overflow-hidden">
            <CardHeader className="border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <CardTitle className="text-xl text-gray-900">Earnings Calendar</CardTitle>
                        <p className="text-sm text-gray-500 mt-1">
                            {calendarData ? `${calendarData.totalEarnings} companies reporting` : 'Loading...'}
                        </p>
                    </div>
                    <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
                        {(['daily', 'weekly', 'monthly'] as CalendarView[]).map((v) => (
                            <Button
                                key={v}
                                size="sm"
                                variant={view === v ? 'default' : 'ghost'}
                                onClick={() => setView(v)}
                                className={`text-xs capitalize ${view === v
                                        ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                                        : 'text-gray-600 hover:text-gray-900'
                                    }`}
                            >
                                {v}
                            </Button>
                        ))}
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
                        <Button onClick={fetchCalendar} variant="outline" size="sm">
                            Try Again
                        </Button>
                    </div>
                )}

                {/* Calendar Content */}
                {!loading && !error && calendarData && (
                    <div className="flex flex-col lg:flex-row">
                        {/* Date Selector */}
                        <div className="lg:w-1/3 border-b lg:border-b-0 lg:border-r border-gray-100 overflow-x-auto lg:overflow-x-visible">
                            <div className="flex lg:flex-col gap-1 p-3 lg:max-h-[400px] lg:overflow-y-auto">
                                {displayDays.map((day) => {
                                    const dayDiff = getDaysUntilEarnings(day.date);
                                    const isPast = dayDiff !== null && dayDiff < 0;

                                    return (
                                        <button
                                            key={day.date}
                                            onClick={() => setSelectedDate(day.date)}
                                            className={`flex-shrink-0 flex items-center justify-between gap-3 px-4 py-3 rounded-lg transition-all text-left ${selectedDate === day.date
                                                    ? 'bg-emerald-50 border-2 border-emerald-500'
                                                    : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                                                } ${isPast ? 'opacity-50' : ''}`}
                                        >
                                            <div className="min-w-0">
                                                <div className={`text-xs font-medium ${isToday(day.date)
                                                        ? 'text-emerald-600'
                                                        : 'text-gray-500'
                                                    }`}>
                                                    {isToday(day.date) ? 'TODAY' : day.dayOfWeek.slice(0, 3).toUpperCase()}
                                                </div>
                                                <div className="text-sm font-semibold text-gray-900">
                                                    {formatDate(day.date)}
                                                </div>
                                            </div>
                                            <div className={`flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-bold ${day.count > 0
                                                    ? 'bg-emerald-100 text-emerald-700'
                                                    : 'bg-gray-100 text-gray-400'
                                                }`}>
                                                {day.count}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Earnings List for Selected Date */}
                        <div className="lg:w-2/3 p-4">
                            {selectedDayData ? (
                                <>
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                        {formatFullDate(selectedDayData.date)}
                                        <span className="text-sm font-normal text-gray-500 ml-2">
                                            ({selectedDayData.count} {selectedDayData.count === 1 ? 'company' : 'companies'})
                                        </span>
                                    </h3>

                                    {selectedDayData.count === 0 ? (
                                        <div className="text-center py-12 text-gray-500">
                                            <p className="text-lg mb-1">No earnings scheduled</p>
                                            <p className="text-sm">Check other dates in the calendar</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-2 max-h-[350px] overflow-y-auto pr-2">
                                            {selectedDayData.earnings.map((earning, idx) => (
                                                <div
                                                    key={`${earning.symbol}-${idx}`}
                                                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer group"
                                                    onClick={() => {
                                                        if (onSelectStock) {
                                                            onSelectStock(earning.symbol);
                                                        } else {
                                                            setSelectedEarning(selectedEarning?.symbol === earning.symbol ? null : earning);
                                                        }
                                                    }}
                                                >
                                                    <div className="flex items-center gap-4">
                                                        <div>
                                                            <span className="font-mono font-bold text-emerald-600 group-hover:text-emerald-700 transition-colors">
                                                                {earning.symbol}
                                                            </span>
                                                        </div>
                                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getTimeColor(earning.time)}`}>
                                                            {formatEarningsTimeShort(earning.time) || 'TBD'}
                                                        </span>
                                                    </div>
                                                    <div className="text-right">
                                                        <div className="text-sm text-gray-900">
                                                            EPS Est: <span className="font-semibold">{formatEps(earning.epsEstimate)}</span>
                                                        </div>
                                                        <div className="text-xs text-gray-500">
                                                            Rev Est: {formatCurrency(earning.revenueEstimate)}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="text-center py-12 text-gray-500">
                                    <p>Select a date to view earnings</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!loading && !error && (!calendarData || calendarData.totalEarnings === 0) && (
                    <div className="p-6 text-center">
                        <p className="text-gray-500">No earnings data available</p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export default EarningsCalendar;
