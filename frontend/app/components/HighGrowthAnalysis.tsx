'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface HighGrowthData {
  sales_cagr_hg?: number;
  net_margin_trend?: string;
  current_net_margin?: number;
  current_psr?: number;
  current_per?: number;
  ev_to_ebitda?: number;
  net_debt_to_ebitda?: number;
  latest_roe?: number;
  avg_roic?: number;
  insider_ownership_hg?: number;
  pays_dividends?: boolean;
}

export function HighGrowthAnalysis({ ticker }: { ticker: string }) {
  const [analysis, setAnalysis] = useState<HighGrowthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchAnalysis = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8000/api/analysis/${ticker}/high-growth`);
          if (!response.ok) {
            throw new Error('Failed to fetch High-Growth analysis.');
          }
          const data = await response.json();
          setAnalysis(data);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchAnalysis();
    }
  }, [ticker]);

  if (loading) return <p>Loading High-Growth analysis...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!analysis) return <p>No High-Growth analysis available.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>High-Growth, Quality Stock Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p>Sales CAGR: {analysis.sales_cagr_hg ? `${(analysis.sales_cagr_hg * 100).toFixed(2)}%` : 'N/A'}</p>
          <p>Net Margin Trend: {analysis.net_margin_trend || 'N/A'}</p>
          <p>Current Net Margin: {analysis.current_net_margin ? `${(analysis.current_net_margin * 100).toFixed(2)}%` : 'N/A'}</p>
          <p>Current PSR: {analysis.current_psr ? analysis.current_psr.toFixed(2) : 'N/A'}</p>
          <p>Current PER: {analysis.current_per ? analysis.current_per.toFixed(2) : 'N/A'}</p>
          <p>EV/EBITDA: {analysis.ev_to_ebitda ? analysis.ev_to_ebitda.toFixed(2) : 'N/A'}</p>
          <p>Net Debt/EBITDA: {analysis.net_debt_to_ebitda ? analysis.net_debt_to_ebitda.toFixed(2) : 'N/A'}</p>
          <p>Latest ROE: {analysis.latest_roe ? `${(analysis.latest_roe * 100).toFixed(2)}%` : 'N/A'}</p>
          <p>Average ROIC: {analysis.avg_roic ? `${(analysis.avg_roic * 100).toFixed(2)}%` : 'N/A'}</p>
          <p>Insider Ownership: {analysis.insider_ownership_hg ? `${(analysis.insider_ownership_hg * 100).toFixed(2)}%` : 'N/A'}</p>
          <p>Pays Dividends: {analysis.pays_dividends ? 'Yes' : 'No'}</p>
        </div>
      </CardContent>
    </Card>
  );
}