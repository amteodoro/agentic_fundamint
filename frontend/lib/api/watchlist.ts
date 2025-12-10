/**
 * Watchlist API services.
 */

import { api } from './client';

export interface WatchlistItem {
    id: string;
    ticker: string;
    added_at: string;
    target_price: number | null;
    notes: string | null;
}

export interface Watchlist {
    id: string;
    name: string;
    created_at: string;
    items: WatchlistItem[];
}

export interface WatchlistListResponse {
    watchlists: Watchlist[];
    total: number;
}

export interface CreateWatchlistData {
    name: string;
}

export interface UpdateWatchlistData {
    name?: string;
}

export interface AddWatchlistItemData {
    ticker: string;
    target_price?: number;
    notes?: string;
}

export interface UpdateWatchlistItemData {
    target_price?: number;
    notes?: string;
}

/**
 * Get all watchlists for the current user.
 */
export async function getWatchlists(): Promise<WatchlistListResponse> {
    return api.get<WatchlistListResponse>('/api/watchlists');
}

/**
 * Get a specific watchlist by ID.
 */
export async function getWatchlist(id: string): Promise<Watchlist> {
    return api.get<Watchlist>(`/api/watchlists/${id}`);
}

/**
 * Create a new watchlist.
 */
export async function createWatchlist(data: CreateWatchlistData): Promise<Watchlist> {
    return api.post<Watchlist>('/api/watchlists', data);
}

/**
 * Update a watchlist.
 */
export async function updateWatchlist(id: string, data: UpdateWatchlistData): Promise<Watchlist> {
    return api.put<Watchlist>(`/api/watchlists/${id}`, data);
}

/**
 * Delete a watchlist.
 */
export async function deleteWatchlist(id: string): Promise<void> {
    return api.delete(`/api/watchlists/${id}`);
}

/**
 * Add a stock to a watchlist.
 */
export async function addStockToWatchlist(
    watchlistId: string,
    data: AddWatchlistItemData
): Promise<WatchlistItem> {
    return api.post<WatchlistItem>(`/api/watchlists/${watchlistId}/stocks`, data);
}

/**
 * Update a stock in a watchlist.
 */
export async function updateStockInWatchlist(
    watchlistId: string,
    ticker: string,
    data: UpdateWatchlistItemData
): Promise<WatchlistItem> {
    return api.put<WatchlistItem>(`/api/watchlists/${watchlistId}/stocks/${ticker}`, data);
}

/**
 * Remove a stock from a watchlist.
 */
export async function removeStockFromWatchlist(
    watchlistId: string,
    ticker: string
): Promise<void> {
    return api.delete(`/api/watchlists/${watchlistId}/stocks/${ticker}`);
}
