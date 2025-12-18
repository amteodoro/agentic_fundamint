/**
 * Portfolio API services.
 */

import { api } from './client';

export interface PortfolioHolding {
    id: string;
    ticker: string;
    shares: number | null;
    average_cost: number | null;
    added_at: string;
    notes: string | null;
}

// Type alias for cleaner imports
export type Holding = PortfolioHolding;

export interface Portfolio {
    id: string;
    name: string;
    description: string | null;
    created_at: string;
    updated_at: string;
    holdings: PortfolioHolding[];
}

export interface PortfolioListResponse {
    portfolios: Portfolio[];
    total: number;
}

export interface CreatePortfolioData {
    name: string;
    description?: string;
}

export interface UpdatePortfolioData {
    name?: string;
    description?: string;
}

export interface AddHoldingData {
    ticker: string;
    shares?: number;
    average_cost?: number;
    notes?: string;
}

export interface UpdateHoldingData {
    shares?: number;
    average_cost?: number;
    notes?: string;
}

/**
 * Get all portfolios for the current user.
 */
export async function getPortfolios(): Promise<PortfolioListResponse> {
    return api.get<PortfolioListResponse>('/api/portfolios');
}

/**
 * Get a specific portfolio by ID.
 */
export async function getPortfolio(id: string): Promise<Portfolio> {
    return api.get<Portfolio>(`/api/portfolios/${id}`);
}

/**
 * Create a new portfolio.
 */
export async function createPortfolio(data: CreatePortfolioData): Promise<Portfolio> {
    return api.post<Portfolio>('/api/portfolios', data);
}

/**
 * Update a portfolio.
 */
export async function updatePortfolio(id: string, data: UpdatePortfolioData): Promise<Portfolio> {
    return api.put<Portfolio>(`/api/portfolios/${id}`, data);
}

/**
 * Delete a portfolio.
 */
export async function deletePortfolio(id: string): Promise<void> {
    return api.delete(`/api/portfolios/${id}`);
}

/**
 * Add a stock to a portfolio.
 */
export async function addStockToPortfolio(
    portfolioId: string,
    data: AddHoldingData
): Promise<PortfolioHolding> {
    return api.post<PortfolioHolding>(`/api/portfolios/${portfolioId}/stocks`, data);
}

/**
 * Update a stock in a portfolio.
 */
export async function updateStockInPortfolio(
    portfolioId: string,
    ticker: string,
    data: UpdateHoldingData
): Promise<PortfolioHolding> {
    return api.put<PortfolioHolding>(`/api/portfolios/${portfolioId}/stocks/${ticker}`, data);
}

/**
 * Remove a stock from a portfolio.
 */
export async function removeStockFromPortfolio(
    portfolioId: string,
    ticker: string
): Promise<void> {
    return api.delete(`/api/portfolios/${portfolioId}/stocks/${ticker}`);
}
