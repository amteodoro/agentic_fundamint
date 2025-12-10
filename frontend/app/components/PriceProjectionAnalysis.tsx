'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

interface ProjectionDefaults {
    revenue_growth_pct: number;
    net_margin_pct: number;
    target_pe: number;
    target_ps: number;
    share_change_pct: number;
    projection_years: number;
}

interface HistoricalContext {
    revenue_history: { year: string; value: number }[];
    margin_history: { year: string; value: number }[];
    pe_range: { min: number | null; avg: number | null; max: number | null };
    shares_history: { year: string; value: number }[];
}

interface DataQuality {
    [key: string]: { source: string; confidence: number };
}

interface HistoricalAverages {
    revenue_growth_pct: number | null;
    net_margin_pct: number | null;
    target_pe: number | null;
    target_ps: number | null;
    share_change_pct: number | null;
    projection_years: number | null;
}

interface NegativeAnalysis {
    revenue_status: 'positive' | 'negative';
    revenue_trend: 'growing' | 'stagnant' | 'shrinking';
    margin_status: 'positive' | 'negative';
    margin_category: 'cyclical' | 'turnaround' | 'structural' | null;
    is_cyclical: boolean;
    has_operating_leverage: boolean;
    red_flags: string[];
    opportunities: string[];
    recommendation: 'PROCEED' | 'REJECT' | 'CYCLICAL_BUY' | 'TURNAROUND_BUY' | null;
    use_price_to_sales: boolean;
}

interface ProjectionData {
    ticker: string;
    company_name: string;
    current_price: number;
    current_revenue: number | null;
    current_net_income: number | null;
    current_shares: number | null;
    market_cap: number | null;
    current_pe: number | null;
    current_margin: number | null;
    defaults: ProjectionDefaults;
    historical_averages: HistoricalAverages;
    historical_context: HistoricalContext;
    data_quality: DataQuality;
    negative_analysis?: NegativeAnalysis;
    hurdle_rate: number;
    error?: string;
}

interface SliderConfig {
    key: keyof ProjectionDefaults;
    label: string;
    min: number;
    max: number;
    step: number;
    unit: string;
    description: string;
}

const SLIDER_CONFIGS: SliderConfig[] = [
    {
        key: 'revenue_growth_pct',
        label: 'Revenue Growth',
        min: -10,
        max: 50,
        step: 0.5,
        unit: '%',
        description: 'Annual revenue growth rate'
    },
    {
        key: 'net_margin_pct',
        label: 'Net Margin',
        min: -20,
        max: 50,
        step: 0.5,
        unit: '%',
        description: 'Target net profit margin'
    },
    {
        key: 'target_pe',
        label: 'Target P/E',
        min: 5,
        max: 100,
        step: 0.5,
        unit: 'x',
        description: 'Expected valuation multiple'
    },
    {
        key: 'share_change_pct',
        label: 'Share Change/yr',
        min: -10,
        max: 10,
        step: 0.1,
        unit: '%',
        description: 'Negative = buybacks, Positive = dilution'
    }
];

const YEAR_OPTIONS = [5, 10, 15, 20];

export function PriceProjectionAnalysis({ ticker }: { ticker: string }) {
    const [data, setData] = useState<ProjectionData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Parameter state - initialized from defaults
    const [revenueGrowth, setRevenueGrowth] = useState<number>(5);
    const [netMargin, setNetMargin] = useState<number>(10);
    const [targetPE, setTargetPE] = useState<number>(15);
    const [targetPS, setTargetPS] = useState<number>(2);
    const [shareChange, setShareChange] = useState<number>(0);
    const [years, setYears] = useState<number>(10);

    useEffect(() => {
        if (ticker) {
            const fetchData = async () => {
                try {
                    setLoading(true);
                    const response = await fetch(`http://localhost:8100/api/analysis/${ticker}/price-projection`);
                    if (!response.ok) {
                        throw new Error('Failed to fetch price projection data.');
                    }
                    const result: ProjectionData = await response.json();

                    if (result.error) {
                        throw new Error(result.error);
                    }

                    setData(result);

                    // Initialize sliders with defaults
                    setRevenueGrowth(result.defaults.revenue_growth_pct);
                    setNetMargin(result.defaults.net_margin_pct);
                    setTargetPE(result.defaults.target_pe);
                    setTargetPS(result.defaults.target_ps || 2);
                    setShareChange(result.defaults.share_change_pct);
                    setYears(result.defaults.projection_years);

                } catch (err: any) {
                    setError(err.message);
                } finally {
                    setLoading(false);
                }
            };
            fetchData();
        }
    }, [ticker]);

    // Calculate projected values
    const projection = useMemo(() => {
        if (!data?.current_price || !data?.current_revenue) {
            return null;
        }

        const currentRevenue = data.current_revenue;
        const currentPrice = data.current_price;
        const currentShares = data.current_shares || (data.market_cap ? data.market_cap / currentPrice : null);
        const usePriceToSales = data.negative_analysis?.use_price_to_sales || false;

        if (!currentShares) return null;

        // Step 1: Future Revenue
        const futureRevenue = currentRevenue * Math.pow(1 + revenueGrowth / 100, years);

        let futureMarketCap: number;
        let futureNetIncome: number | null = null;

        if (usePriceToSales) {
            // P/S Mode: Market Cap = Revenue * P/S ratio
            futureMarketCap = futureRevenue * targetPS;
        } else {
            // P/E Mode: Market Cap = Net Income * P/E ratio
            futureNetIncome = futureRevenue * (netMargin / 100);
            futureMarketCap = futureNetIncome * targetPE;
        }

        // Step 4: Future Shares
        const futureShares = currentShares * Math.pow(1 + shareChange / 100, years);

        // Step 5: Future Stock Price
        const futurePrice = futureMarketCap / futureShares;

        // Expected CAGR (Annual Return)
        const cagr = (Math.pow(futurePrice / currentPrice, 1 / years) - 1) * 100;

        // Decision based on hurdle rate (15%)
        const hurdleRate = data.hurdle_rate;
        let decision: 'BUY' | 'HOLD' | 'REJECT';
        let decisionColor: string;

        if (cagr >= hurdleRate) {
            decision = 'BUY';
            decisionColor = 'bg-green-500';
        } else if (cagr >= 10) {
            decision = 'HOLD';
            decisionColor = 'bg-yellow-500';
        } else {
            decision = 'REJECT';
            decisionColor = 'bg-red-500';
        }

        return {
            futureRevenue,
            futureNetIncome,
            futureMarketCap,
            futureShares,
            futurePrice,
            cagr,
            decision,
            decisionColor,
            currentPrice,
            currentShares,
            currentRevenue,
            usePriceToSales
        };
    }, [data, revenueGrowth, netMargin, targetPE, targetPS, shareChange, years]);

    const resetToDefaults = () => {
        if (data) {
            setRevenueGrowth(data.defaults.revenue_growth_pct);
            setNetMargin(data.defaults.net_margin_pct);
            setTargetPE(data.defaults.target_pe);
            setTargetPS(data.defaults.target_ps || 2);
            setShareChange(data.defaults.share_change_pct);
            setYears(data.defaults.projection_years);
        }
    };

    const formatCurrency = (value: number | null): string => {
        if (value === null || value === undefined) return 'N/A';
        if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
        if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
        if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
        return `$${value.toFixed(2)}`;
    };

    const formatLargeNumber = (value: number | null): string => {
        if (value === null || value === undefined) return 'N/A';
        if (value >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
        if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
        if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
        return value.toFixed(0);
    };

    const getConfidenceBadge = (quality?: { source: string; confidence: number }) => {
        if (!quality) return null;
        const color = quality.confidence >= 0.8 ? 'bg-green-100 text-green-800' :
            quality.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800';
        return (
            <span className={`text-xs px-2 py-0.5 rounded-full ${color}`}>
                {quality.source === 'calculated' ? 'Calculated' : quality.source === 'yfinance' ? 'Verified' : 'Estimate'}
            </span>
        );
    };

    if (loading) return <p className="p-4">Loading price projection analysis...</p>;
    if (error) return <p className="text-red-500 p-4">{error}</p>;
    if (!data) return <p className="p-4">No price projection data available.</p>;

    const parameterValues: Record<string, number> = {
        revenue_growth_pct: revenueGrowth,
        net_margin_pct: netMargin,
        target_pe: targetPE,
        target_ps: targetPS,
        share_change_pct: shareChange,
        projection_years: years
    };

    const setters: Record<string, (v: number) => void> = {
        revenue_growth_pct: setRevenueGrowth,
        net_margin_pct: setNetMargin,
        target_pe: setTargetPE,
        target_ps: setTargetPS,
        share_change_pct: setShareChange,
        projection_years: setYears
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="flex items-center justify-between">
                        <span>Price Target Projection</span>
                        <span className="text-sm font-normal text-gray-500">
                            Based on "Recipe" Framework
                        </span>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-gray-600">
                        Project the future stock price using 4 key variables: Revenue Growth, Net Margin, P/E Multiple, and Share Count.
                        Adjust the sliders to see how different scenarios affect the target price and expected return.
                    </p>
                </CardContent>
            </Card>

            {/* Red Flags & Opportunities Alert */}
            {data.negative_analysis && (data.negative_analysis.red_flags.length > 0 || data.negative_analysis.opportunities.length > 0) && (
                <div className="space-y-3">
                    {/* Red Flags */}
                    {data.negative_analysis.red_flags.length > 0 && (
                        <Card className="border-2 border-red-300 bg-red-50">
                            <CardContent className="pt-4">
                                <div className="space-y-2">
                                    <h3 className="font-bold text-red-800">Warning: Red Flags Detected</h3>
                                    {data.negative_analysis.red_flags.map((flag: string, idx: number) => (
                                        <p key={idx} className="text-sm text-red-700">{flag}</p>
                                    ))}
                                    {data.negative_analysis.recommendation === 'REJECT' && (
                                        <p className="text-sm font-bold text-red-800 mt-2">
                                            STOP - Recommendation: REJECT this investment based on Recipe methodology.
                                        </p>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Opportunities */}
                    {data.negative_analysis.opportunities.length > 0 && (
                        <Card className="border-2 border-green-300 bg-green-50">
                            <CardContent className="pt-4">
                                <div className="space-y-2">
                                    <h3 className="font-bold text-green-800">Potential Opportunities</h3>
                                    {data.negative_analysis.opportunities.map((opp: string, idx: number) => (
                                        <p key={idx} className="text-sm text-green-700">{opp}</p>
                                    ))}
                                    {data.negative_analysis.recommendation === 'CYCLICAL_BUY' && (
                                        <p className="text-sm font-bold text-green-800 mt-2">
                                            Cyclical Pattern: Consider buying during this downturn.
                                        </p>
                                    )}
                                    {data.negative_analysis.recommendation === 'TURNAROUND_BUY' && (
                                        <p className="text-sm font-bold text-green-800 mt-2">
                                            Turnaround Potential: High operating leverage could drive margin expansion.
                                        </p>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* P/S Slider - shown when P/E is not applicable */}
                    {data.negative_analysis.use_price_to_sales && (
                        <Card className="border-2 border-blue-300 bg-blue-50">
                            <CardContent className="pt-4">
                                <div className="space-y-4">
                                    <div>
                                        <h3 className="font-bold text-blue-800">Using Price-to-Sales (P/S) Ratio</h3>
                                        <p className="text-sm text-blue-700">
                                            With negative margins, P/E is meaningless. Projections now use P/S ratio to calculate future market cap directly from revenue.
                                        </p>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <Label className="text-sm font-medium text-blue-800">Target P/S Ratio</Label>
                                            <span className="font-bold text-lg text-blue-800">
                                                {targetPS.toFixed(1)}x
                                            </span>
                                        </div>
                                        <input
                                            type="range"
                                            min={0.5}
                                            max={15}
                                            step={0.1}
                                            value={targetPS}
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTargetPS(parseFloat(e.target.value))}
                                            className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                        />
                                        <div className="flex justify-between text-xs text-blue-600">
                                            <span>0.5x</span>
                                            <span>Future Market Cap = Revenue × P/S</span>
                                            <span>15x</span>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Left Column: Parameters */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Projection Parameters</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Sliders */}
                        {SLIDER_CONFIGS.map((config) => {
                            const historicalAvg = data.historical_averages?.[config.key];
                            return (
                                <div key={config.key} className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <Label className="text-sm font-medium">{config.label}</Label>
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-lg">
                                                {parameterValues[config.key].toFixed(1)}{config.unit}
                                            </span>
                                            {getConfidenceBadge(data.data_quality[config.key.replace('_pct', '')])}
                                        </div>
                                    </div>
                                    <input
                                        type="range"
                                        min={config.min}
                                        max={config.max}
                                        step={config.step}
                                        value={parameterValues[config.key]}
                                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setters[config.key](parseFloat(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                    <div className="flex justify-between text-xs">
                                        <span className="text-gray-500">{config.min}{config.unit}</span>
                                        <div className="flex items-center gap-1">
                                            {historicalAvg !== null && historicalAvg !== undefined && (
                                                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                                                    Hist Avg: {historicalAvg.toFixed(1)}{config.unit}
                                                </span>
                                            )}
                                        </div>
                                        <span className="text-gray-500">{config.max}{config.unit}</span>
                                    </div>
                                </div>
                            );
                        })}

                        {/* Years Dropdown */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label className="text-sm font-medium">Projection Horizon</Label>
                                <select
                                    value={years}
                                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setYears(parseInt(e.target.value))}
                                    className="border rounded px-3 py-1 text-sm"
                                >
                                    {YEAR_OPTIONS.map((y) => (
                                        <option key={y} value={y}>{y} years</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Reset Button */}
                        <button
                            onClick={resetToDefaults}
                            className="w-full py-2 px-4 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
                        >
                            Reset to Defaults
                        </button>
                    </CardContent>
                </Card>

                {/* Right Column: Results */}
                <div className="space-y-4">
                    {/* Target Price Card */}
                    <Card className="border-2 border-blue-200">
                        <CardContent className="pt-6">
                            {projection ? (
                                <div className="text-center space-y-4">
                                    <div>
                                        <p className="text-sm text-gray-500">Target Price ({years} years)</p>
                                        <p className="text-4xl font-bold text-blue-600">
                                            ${projection.futurePrice.toFixed(2)}
                                        </p>
                                    </div>

                                    <div className="flex items-center justify-center gap-2">
                                        <span className="text-gray-500">Expected Return:</span>
                                        <span className={`text-2xl font-bold ${projection.cagr >= 15 ? 'text-green-600' :
                                            projection.cagr >= 10 ? 'text-yellow-600' : 'text-red-600'
                                            }`}>
                                            {projection.cagr.toFixed(1)}% CAGR
                                        </span>
                                    </div>

                                    <div className={`inline-flex items-center justify-center px-6 py-3 rounded-lg text-white font-bold text-xl ${projection.decisionColor}`}>
                                        {projection.decision}
                                    </div>

                                    <p className="text-xs text-gray-500">
                                        {projection.decision === 'BUY' && `Expected return ≥ ${data.hurdle_rate}% hurdle rate`}
                                        {projection.decision === 'HOLD' && 'Expected return between 10-15%'}
                                        {projection.decision === 'REJECT' && 'Expected return below 10%'}
                                    </p>
                                </div>
                            ) : (
                                <p className="text-center text-gray-500">Insufficient data for projection</p>
                            )}
                        </CardContent>
                    </Card>

                    {/* Breakdown Card */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">Price Breakdown</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {projection && (
                                <div className="space-y-3 text-sm">
                                    <div className="flex justify-between py-2 border-b">
                                        <span className="text-gray-600">Current Price</span>
                                        <span className="font-medium">${projection.currentPrice.toFixed(2)}</span>
                                    </div>
                                    <div className="flex justify-between py-2 border-b">
                                        <span className="text-gray-600">Current Revenue</span>
                                        <span className="font-medium">{formatCurrency(projection.currentRevenue)}</span>
                                    </div>
                                    <div className="flex justify-between py-2 border-b">
                                        <span className="text-gray-600">Future Revenue ({years}yr)</span>
                                        <span className="font-medium text-blue-600">{formatCurrency(projection.futureRevenue)}</span>
                                    </div>
                                    <div className="flex justify-between py-2 border-b">
                                        <span className="text-gray-600">Future Net Income</span>
                                        <span className="font-medium text-blue-600">{formatCurrency(projection.futureNetIncome)}</span>
                                    </div>
                                    <div className="flex justify-between py-2 border-b">
                                        <span className="text-gray-600">Future Market Cap</span>
                                        <span className="font-medium text-blue-600">{formatCurrency(projection.futureMarketCap)}</span>
                                    </div>
                                    <div className="flex justify-between py-2 border-b">
                                        <span className="text-gray-600">Share Count Change</span>
                                        <span className={`font-medium ${shareChange < 0 ? 'text-green-600' : shareChange > 0 ? 'text-red-600' : ''}`}>
                                            {shareChange < 0 ? 'Buybacks' : shareChange > 0 ? 'Dilution' : 'Stable'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between py-2 bg-blue-50 rounded px-2 font-bold">
                                        <span>Target Price</span>
                                        <span className="text-blue-600">${projection.futurePrice.toFixed(2)}</span>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Historical Context */}
                    {data.historical_context.pe_range.avg && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg">Historical Context</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div className="p-3 bg-gray-50 rounded">
                                        <p className="text-gray-500">Current P/E</p>
                                        <p className="font-bold">{data.current_pe?.toFixed(1) || 'N/A'}x</p>
                                    </div>
                                    <div className="p-3 bg-gray-50 rounded">
                                        <p className="text-gray-500">P/E Range</p>
                                        <p className="font-bold">
                                            {data.historical_context.pe_range.min?.toFixed(0)} - {data.historical_context.pe_range.max?.toFixed(0)}x
                                        </p>
                                    </div>
                                    <div className="p-3 bg-gray-50 rounded">
                                        <p className="text-gray-500">Current Margin</p>
                                        <p className="font-bold">{data.current_margin?.toFixed(1) || 'N/A'}%</p>
                                    </div>
                                    <div className="p-3 bg-gray-50 rounded">
                                        <p className="text-gray-500">Market Cap</p>
                                        <p className="font-bold">{data.market_cap ? formatCurrency(data.market_cap) : 'N/A'}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}

export default PriceProjectionAnalysis;
