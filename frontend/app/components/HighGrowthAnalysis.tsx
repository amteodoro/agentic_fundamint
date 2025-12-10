'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceBadge } from './ConfidenceBadge';

interface Metric {
  value: number | null;
  confidence: number;
  interpretation?: string;
}

interface HighGrowthMetrics {
  sales_growth: Metric;
  net_margin_trend: string;
  net_margin: Metric;
  psr_ratio: Metric;
  per_ratio: Metric;
  ev_ebitda: Metric;
  debt_to_ebitda: Metric;
  roe: Metric;
  roic: Metric;
  insider_ownership: Metric;
  pays_dividends: boolean;
}

interface HighGrowthResponse {
  final_metrics: {
    high_growth: HighGrowthMetrics;
  };
  analysis_summary: string;
  recommendations: string[];
}

export function HighGrowthAnalysis({ ticker }: { ticker: string }) {
  const [data, setData] = useState<HighGrowthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchAnalysis = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8100/api/analysis/${ticker}/high-growth`);
          if (!response.ok) {
            throw new Error('Failed to fetch High-Growth analysis.');
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

  if (loading) return <p>Loading High-Growth analysis...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data || !data.final_metrics.high_growth) return <p>No High-Growth analysis available.</p>;

  const metrics = data.final_metrics.high_growth;

  const renderMetric = (label: string, metric: Metric | undefined, isPercent: boolean = true) => {
    if (!metric || metric.value === null || metric.value === undefined) {
      return (
        <div className="flex items-center justify-between py-1">
          <span className="text-gray-600">{label}:</span>
          <span className="font-medium">N/A</span>
        </div>
      );
    }

    return (
      <div className="flex items-center justify-between py-1">
        <span className="text-gray-600">{label}:</span>
        <div className="flex items-center">
          <span className="font-medium mr-2">
            {isPercent ? `${(metric.value * 100).toFixed(2)}%` : metric.value.toFixed(2)}
          </span>
          <ConfidenceBadge score={metric.confidence} />
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>High-Growth, Quality Stock Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-3">Growth & Margins</h3>
              {renderMetric("Sales Growth (CAGR)", metrics.sales_growth)}
              <div className="flex items-center justify-between py-1">
                <span className="text-gray-600">Net Margin Trend:</span>
                <span className="font-medium">{metrics.net_margin_trend || 'N/A'}</span>
              </div>
              {renderMetric("Current Net Margin", metrics.net_margin)}
              {renderMetric("Latest ROE", metrics.roe)}
              {renderMetric("Average ROIC", metrics.roic)}
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Valuation & Health</h3>
              {renderMetric("PSR", metrics.psr_ratio, false)}
              {renderMetric("PER", metrics.per_ratio, false)}
              {renderMetric("EV/EBITDA", metrics.ev_ebitda, false)}
              {renderMetric("Debt/EBITDA", metrics.debt_to_ebitda, false)}
              {renderMetric("Insider Ownership", metrics.insider_ownership)}
              <div className="flex items-center justify-between py-1">
                <span className="text-gray-600">Pays Dividends:</span>
                <span className="font-medium">{metrics.pays_dividends ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {data.analysis_summary && (
        <Card>
          <CardHeader>
            <CardTitle>AI Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700">{data.analysis_summary}</p>
          </CardContent>
        </Card>
      )}

      {data.recommendations && data.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1">
              {data.recommendations.map((rec, index) => (
                <li key={index} className="text-gray-700">{rec}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}