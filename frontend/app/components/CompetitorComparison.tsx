'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

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
    is_target?: boolean;
}

interface CompetitorAnalysisResponse {
    ticker: string;
    industry: string;
    competitors_analyzed: string[];
    comparison_data: CompetitorMetrics[];
}

export function CompetitorComparison({ ticker }: { ticker: string }) {
    const [data, setData] = useState<CompetitorAnalysisResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

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
                } catch (err: any) {
                    setError(err.message);
                } finally {
                    setLoading(false);
                }
            };
            fetchAnalysis();
        }
    }, [ticker]);

    if (loading) return <p>Loading Competitor analysis...</p>;
    if (error) return <p className="text-red-500">{error}</p>;
    if (!data || data.comparison_data.length === 0) return <p>No Competitor analysis available.</p>;

    const formatNumber = (num: number | undefined | null, isPercent: boolean = false) => {
        if (num === undefined || num === null) return 'N/A';
        if (isPercent) return `${(num * 100).toFixed(2)}%`;

        // Format large numbers (Market Cap)
        if (num > 1e9) return `$${(num / 1e9).toFixed(2)}B`;
        if (num > 1e6) return `$${(num / 1e6).toFixed(2)}M`;

        return num.toFixed(2);
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>Competitor Comparison ({data.industry})</CardTitle>
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
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {data.comparison_data.map((comp) => (
                                <TableRow key={comp.ticker} className={comp.is_target ? "bg-blue-50 font-medium" : ""}>
                                    <TableCell>{comp.ticker}</TableCell>
                                    <TableCell>{comp.name}</TableCell>
                                    <TableCell>{formatNumber(comp.market_cap)}</TableCell>
                                    <TableCell>{formatNumber(comp.pe_ratio)}</TableCell>
                                    <TableCell>{formatNumber(comp.ps_ratio)}</TableCell>
                                    <TableCell>{formatNumber(comp.gross_margins, true)}</TableCell>
                                    <TableCell>{formatNumber(comp.operating_margins, true)}</TableCell>
                                    <TableCell>{formatNumber(comp.return_on_equity, true)}</TableCell>
                                    <TableCell>{formatNumber(comp.revenue_growth, true)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    );
}
