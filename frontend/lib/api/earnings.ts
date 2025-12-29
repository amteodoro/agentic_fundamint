/**
 * Earnings Calendar API services.
 */

import { api } from './client';

// ====== Types ======

export interface EarningEvent {
    symbol: string;
    date: string;
    time?: string | null;  // "bmo" (before market open), "amc" (after market close), "dmh" (during market hours)
    epsEstimate?: number | null;
    epsActual?: number | null;
    revenueEstimate?: number | null;
    revenueActual?: number | null;
    fiscalDateEnding?: string | null;
}

export interface DailyEarnings {
    date: string;
    dayOfWeek: string;
    earnings: EarningEvent[];
    count: number;
}

export interface EarningsCalendarResponse {
    startDate: string;
    endDate: string;
    view: string;
    days: DailyEarnings[];
    totalEarnings: number;
}

export interface HistoricalEarning {
    date: string;
    symbol: string;
    epsActual?: number | null;
    epsEstimate?: number | null;
    epsSurprise?: number | null;
    epsSurprisePercent?: number | null;
    revenue?: number | null;
    revenueEstimate?: number | null;
    fiscalDateEnding?: string | null;
}

export interface EarningsStats {
    totalReported: number;
    beats: number;
    misses: number;
    meets: number;
    beatRate?: number | null;
}

export interface StockEarningsResponse {
    symbol: string;
    nextEarningsDate?: string | null;
    nextEarningsTime?: string | null;
    epsEstimate?: number | null;
    revenueEstimate?: number | null;
    history: HistoricalEarning[];
    stats: EarningsStats;
}

export interface BulkEarningsItem {
    symbol: string;
    nextEarningsDate?: string | null;
    nextEarningsTime?: string | null;
    daysUntilEarnings?: number | null;
}

export interface BulkEarningsResponse {
    earnings: BulkEarningsItem[];
}

// ====== API Functions ======

export type CalendarView = 'daily' | 'weekly' | 'monthly';

/**
 * Get earnings calendar for a specified period.
 */
export async function getEarningsCalendar(
    view: CalendarView = 'weekly',
    fromDate?: string,
    toDate?: string
): Promise<EarningsCalendarResponse> {
    const params = new URLSearchParams({ view });
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);

    const response = await fetch(`http://localhost:8100/api/earnings/calendar?${params}`);
    if (!response.ok) {
        throw new Error('Failed to fetch earnings calendar');
    }
    return response.json();
}

/**
 * Get complete earnings info for a specific stock.
 */
export async function getStockEarnings(ticker: string): Promise<StockEarningsResponse> {
    const response = await fetch(`http://localhost:8100/api/earnings/${ticker}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch earnings for ${ticker}`);
    }
    return response.json();
}

/**
 * Get historical earnings for a specific stock.
 */
export async function getEarningsHistory(
    ticker: string,
    limit: number = 20
): Promise<{ ticker: string; history: HistoricalEarning[]; count: number }> {
    const response = await fetch(`http://localhost:8100/api/earnings/${ticker}/history?limit=${limit}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch earnings history for ${ticker}`);
    }
    return response.json();
}

/**
 * Get next earnings dates for multiple stocks at once.
 * Useful for portfolio/watchlist views.
 */
export async function getBulkEarningsDates(tickers: string[]): Promise<BulkEarningsResponse> {
    const response = await fetch('http://localhost:8100/api/earnings/bulk', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tickers }),
    });
    if (!response.ok) {
        throw new Error('Failed to fetch bulk earnings dates');
    }
    return response.json();
}

// ====== Helper Functions ======

/**
 * Format earnings time code to human-readable string.
 */
export function formatEarningsTime(time?: string | null): string {
    if (!time) return '';

    switch (time.toLowerCase()) {
        case 'bmo':
            return 'Before Market Open';
        case 'amc':
            return 'After Market Close';
        case 'dmh':
            return 'During Market Hours';
        default:
            return time;
    }
}

/**
 * Format earnings time to short code.
 */
export function formatEarningsTimeShort(time?: string | null): string {
    if (!time) return '';

    switch (time.toLowerCase()) {
        case 'bmo':
            return 'Pre-Market';
        case 'amc':
            return 'After Hours';
        case 'dmh':
            return 'Market Hours';
        default:
            return time.toUpperCase();
    }
}

/**
 * Calculate days until earnings.
 */
export function getDaysUntilEarnings(dateStr?: string | null): number | null {
    if (!dateStr) return null;

    try {
        const earningsDate = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        earningsDate.setHours(0, 0, 0, 0);

        const diffTime = earningsDate.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        return diffDays;
    } catch {
        return null;
    }
}

/**
 * Format days until earnings to human-readable string.
 */
export function formatDaysUntilEarnings(days: number | null): string {
    if (days === null) return 'Unknown';
    if (days === 0) return 'Today';
    if (days === 1) return 'Tomorrow';
    if (days < 0) return `${Math.abs(days)} days ago`;
    if (days <= 7) return `In ${days} days`;
    if (days <= 14) return 'Next week';
    if (days <= 30) return `In ${Math.ceil(days / 7)} weeks`;
    return `In ${Math.ceil(days / 30)} months`;
}

/**
 * Get urgency color class based on days until earnings.
 */
export function getEarningsUrgencyClass(days: number | null): string {
    if (days === null) return 'text-gray-400';
    if (days <= 0) return 'text-red-600 font-bold';
    if (days <= 3) return 'text-orange-600 font-semibold';
    if (days <= 7) return 'text-yellow-600';
    return 'text-gray-600';
}

/**
 * Format surprise percentage with color indication.
 */
export function getSurpriseInfo(percent?: number | null): {
    text: string;
    colorClass: string;
    isBeat: boolean | null;
} {
    if (percent === null || percent === undefined) {
        return { text: '-', colorClass: 'text-gray-400', isBeat: null };
    }

    const absPercent = Math.abs(percent);
    const formattedPercent = absPercent.toFixed(2);

    if (percent > 0.5) {
        return {
            text: `Beat +${formattedPercent}%`,
            colorClass: 'text-green-600',
            isBeat: true,
        };
    } else if (percent < -0.5) {
        return {
            text: `Miss -${formattedPercent}%`,
            colorClass: 'text-red-600',
            isBeat: false,
        };
    } else {
        return {
            text: 'Met',
            colorClass: 'text-gray-600',
            isBeat: null,
        };
    }
}
