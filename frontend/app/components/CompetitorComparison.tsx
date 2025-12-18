'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useChatContext, getCurrencySymbol } from '@/app/context/ChatContext';

interface CompetitorMetrics {
    ticker: string;
    name: string;
    market_cap: number;
    pe_ratio: number;
    ps_ratio: number;
    pb_ratio: number;
    gross_margins: number;
    operating_margins: number;
    return_on_equity: number;
    revenue_growth: number;
    current_price: number | null;
    earnings_growth: number | null;
    target_price: number | null;
    is_target?: boolean;
}

interface CompetitorAnalysisResponse {
    ticker: string;
    industry: string;
    competitors_analyzed: string[];
    comparison_data: CompetitorMetrics[];
}

interface ProjectionDefaults {
    revenue_growth_pct: number;
    net_margin_pct: number;
    target_pe: number;
    target_ps: number;
    share_change_pct: number;
    projection_years: number;
}

interface NegativeAnalysis {
    use_price_to_sales: boolean;
}

interface ProjectionData {
    current_price: number;
    current_revenue: number | null;
    current_shares: number | null;
    market_cap: number | null;
    defaults: ProjectionDefaults;
    negative_analysis?: NegativeAnalysis;
}

interface CompetitorProjection {
    futurePrice: number;
    cagr: number;
}

export function CompetitorComparison({ ticker }: { ticker: string }) {
    const [data, setData] = useState<CompetitorAnalysisResponse | null>(null);
    const [projections, setProjections] = useState<Record<string, CompetitorProjection>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const { currency, convertValue } = useChatContext();
    const currencySymbol = getCurrencySymbol(currency);

    const PROJECTION_YEARS = 5;

    useEffect(() => {
        if (ticker) {
            const fetchAnalysis = async () => {
                try {
                    setLoading(true);
                    const response = await fetch(`http://localhost:8100/api/analysis/${ticker}/competitors`);
                    if (!response.ok) {
                        throw new Error('Failed to fetch Competitor analysis.');
                    }
                    const result = await response.json();
                    setData(result);

                    // Fetch price projection data for each competitor
                    const allTickers = result.comparison_data.map((c: CompetitorMetrics) => c.ticker);
                    const projectionPromises = allTickers.map(async (t: string) => {
                        try {
                            const projRes = await fetch(`http://localhost:8100/api/analysis/${t}/price-projection`);
                            if (projRes.ok) {
                                const projData: ProjectionData = await projRes.json();
                                const projection = calculateProjection(projData, PROJECTION_YEARS);
                                return { ticker: t, projection };
                            }
                        } catch {
                            // Silently fail for individual projections
                        }
                        return { ticker: t, projection: null };
                    });

                    const projectionResults = await Promise.all(projectionPromises);
                    const projMap: Record<string, CompetitorProjection> = {};
                    projectionResults.forEach(({ ticker: t, projection }) => {
                        if (projection) {
                            projMap[t] = projection;
                        }
                    });
                    setProjections(projMap);

                } catch (err: any) {
                    setError(err.message);
                } finally {
                    setLoading(false);
                }
            };
            fetchAnalysis();
        }
    }, [ticker]);

    // Calculate projection using the same Recipe Framework as PriceProjectionAnalysis
    const calculateProjection = (projData: ProjectionData, years: number): CompetitorProjection | null => {
        if (!projData.current_price || !projData.current_revenue) {
            return null;
        }

        const currentRevenue = projData.current_revenue;
        const currentPrice = projData.current_price;
        const currentShares = projData.current_shares ||
            (projData.market_cap ? projData.market_cap / currentPrice : null);

        if (!currentShares) return null;

        const { revenue_growth_pct, net_margin_pct, target_pe, target_ps, share_change_pct } = projData.defaults;
        const usePriceToSales = projData.negative_analysis?.use_price_to_sales || false;

        // Step 1: Future Revenue
        const futureRevenue = currentRevenue * Math.pow(1 + revenue_growth_pct / 100, years);

        let futureMarketCap: number;

        if (usePriceToSales) {
            // P/S Mode: Market Cap = Revenue * P/S ratio
            futureMarketCap = futureRevenue * target_ps;
        } else {
            // P/E Mode: Market Cap = Net Income * P/E ratio
            const futureNetIncome = futureRevenue * (net_margin_pct / 100);
            futureMarketCap = futureNetIncome * target_pe;
        }

        // Step 4: Future Shares
        const futureShares = currentShares * Math.pow(1 + share_change_pct / 100, years);

        // Step 5: Future Stock Price
        const futurePrice = futureMarketCap / futureShares;

        // Expected CAGR (Annual Return)
        const cagr = (Math.pow(futurePrice / currentPrice, 1 / years) - 1) * 100;

        return { futurePrice, cagr };
    };

    if (loading) return <p>Loading Competitor analysis...</p>;
    if (error) return <p className="text-red-500">{error}</p>;
    if (!data || data.comparison_data.length === 0) return <p>No Competitor analysis available.</p>;

    const formatNumber = (num: number | undefined | null, isPercent: boolean = false) => {
        if (num === undefined || num === null) return 'N/A';
        if (isPercent) return `${(num * 100).toFixed(2)}%`;

        return num.toFixed(2);
    };

    const formatCurrencyValue = (num: number | undefined | null, isLarge: boolean = false) => {
        if (num === undefined || num === null) return 'N/A';

        // Convert to selected currency
        const converted = convertValue(num, 'USD');
        if (converted === null) return 'N/A';

        // Format large numbers (Market Cap)
        if (isLarge) {
            if (Math.abs(converted) >= 1e12) return `${currencySymbol}${(converted / 1e12).toFixed(2)}T`;
            if (Math.abs(converted) >= 1e9) return `${currencySymbol}${(converted / 1e9).toFixed(2)}B`;
            if (Math.abs(converted) >= 1e6) return `${currencySymbol}${(converted / 1e6).toFixed(2)}M`;
        }

        return `${currencySymbol}${converted.toFixed(2)}`;
    };

    const formatPrice = (num: number | undefined | null) => {
        if (num === undefined || num === null) return 'N/A';
        const converted = convertValue(num, 'USD');
        if (converted === null) return 'N/A';
        return `${currencySymbol}${converted.toFixed(2)}`;
    };

    const formatPercent = (num: number | undefined | null) => {
        if (num === undefined || num === null) return 'N/A';
        return `${num.toFixed(1)}%`;
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Competitor Comparison - {data.industry} ({currency})</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Ticker</TableHead>
                                <TableHead>Name</TableHead>
                                <TableHead>Market Cap</TableHead>
                                <TableHead>P/E</TableHead>
                                <TableHead>P/S</TableHead>
                                <TableHead>Gross Margin</TableHead>
                                <TableHead>Op Margin</TableHead>
                                <TableHead>ROE</TableHead>
                                <TableHead>Rev Growth</TableHead>
                                <TableHead>5Y Price Proj.</TableHead>
                                <TableHead>Expected Yearly Return</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {data.comparison_data.map((comp) => {
                                const proj = projections[comp.ticker];

                                return (
                                    <TableRow key={comp.ticker} className={comp.is_target ? "bg-blue-50 font-medium" : ""}>
                                        <TableCell>
                                            <Link
                                                href={`/stock/${comp.ticker}`}
                                                className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                                            >
                                                {comp.ticker}
                                            </Link>
                                        </TableCell>
                                        <TableCell>{comp.name}</TableCell>
                                        <TableCell>{formatCurrencyValue(comp.market_cap, true)}</TableCell>
                                        <TableCell>{formatNumber(comp.pe_ratio)}</TableCell>
                                        <TableCell>{formatNumber(comp.ps_ratio)}</TableCell>
                                        <TableCell>{formatNumber(comp.gross_margins, true)}</TableCell>
                                        <TableCell>{formatNumber(comp.operating_margins, true)}</TableCell>
                                        <TableCell>{formatNumber(comp.return_on_equity, true)}</TableCell>
                                        <TableCell>{formatNumber(comp.revenue_growth, true)}</TableCell>
                                        <TableCell>{formatPrice(proj?.futurePrice)}</TableCell>
                                        <TableCell className={proj?.cagr !== undefined ? (proj.cagr >= 0 ? "text-green-600" : "text-red-600") : ""}>
                                            {formatPercent(proj?.cagr)}
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </div>
                <p className="text-xs text-gray-500 mt-3">
                    Note: 5Y Price Projection uses the Recipe Framework (Revenue Growth → Net Margin → P/E Multiple → Share Count) to calculate target prices. Click on a ticker to see the full analysis.
                </p>
            </CardContent>
        </Card>
    );
}

