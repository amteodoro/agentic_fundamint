'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceBadge } from './ConfidenceBadge';
import { useChatContext, getCurrencySymbol } from '@/app/context/ChatContext';

interface Metric {
  value: number | null;
  confidence: number;
  interpretation?: string;
}

interface PhilTownMetrics {
  roic: Metric;
  eps_growth: Metric;
  sales_growth: Metric;
  bvps_growth: Metric;
  fcf_growth: Metric;
  debt_payoff_years: Metric;
  insider_ownership: Metric;
  margin_of_safety: Metric;
  sticker_price: number | null;
  mos_price: number | null;
  current_price: number | null;
}

interface PhilTownResponse {
  final_metrics: {
    phil_town: PhilTownMetrics;
  };
  analysis_summary: string;
  recommendations: string[];
}

export function PhilTownAnalysis({ ticker }: { ticker: string }) {
  const [data, setData] = useState<PhilTownResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Currency context
  const { currency, convertValue } = useChatContext();
  const currencySymbol = getCurrencySymbol(currency);

  const formatPrice = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';
    const converted = convertValue(value, 'USD');
    if (converted === null) return 'N/A';
    return `${currencySymbol}${converted.toFixed(2)}`;
  };

  useEffect(() => {
    if (ticker) {
      const fetchAnalysis = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8100/api/analysis/${ticker}/phil-town`);
          if (!response.ok) {
            throw new Error('Failed to fetch Phil Town analysis.');
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

  if (loading) return <p>Loading Phil Town analysis...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data || !data.final_metrics.phil_town) return <p>No Phil Town analysis available.</p>;

  const metrics = data.final_metrics.phil_town;

  const renderMetric = (label: string, metric: Metric, isPercent: boolean = true) => (
    <div className="flex items-center justify-between py-1">
      <span className="text-gray-600">{label}:</span>
      <div className="flex items-center">
        <span className="font-medium mr-2">
          {metric.value !== null
            ? (isPercent ? `${(metric.value * 100).toFixed(2)}%` : metric.value.toFixed(2))
            : 'N/A'}
        </span>
        {metric.value !== null && <ConfidenceBadge score={metric.confidence} />}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Phil Town's Rule #1 Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-3">Moat Evaluation</h3>
              {renderMetric("ROIC (avg)", metrics.roic)}
              {renderMetric("EPS Growth", metrics.eps_growth)}
              {renderMetric("BVPS Growth", metrics.bvps_growth)}
              {renderMetric("Sales Growth", metrics.sales_growth)}
              {renderMetric("FCF Growth", metrics.fcf_growth)}
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3">Management Evaluation</h3>
              {renderMetric("Debt Payoff Years", metrics.debt_payoff_years, false)}
              {renderMetric("Insider Ownership", metrics.insider_ownership)}
            </div>
          </div>

          <div className="mt-6 border-t pt-4">
            <h3 className="text-lg font-semibold mb-3">Margin of Safety (MOS)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between">
                <span>Sticker Price:</span>
                <span className="font-bold text-lg">{formatPrice(metrics.sticker_price)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>MOS Price (50%):</span>
                <span className="font-bold text-lg text-green-600">{formatPrice(metrics.mos_price)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Current Price:</span>
                <span className="font-bold text-lg">{formatPrice(metrics.current_price)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Confidence:</span>
                <ConfidenceBadge score={metrics.margin_of_safety.confidence} />
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