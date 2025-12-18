'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DataSourceBadge } from './DataSourceBadge';
import { useChatContext, getCurrencySymbol } from '@/app/context/ChatContext';

interface KeyMetric {
  label: string;
  value: string;
  rawValue?: number;
  isCurrency?: boolean;
}

interface MetricsResponse {
  metrics: KeyMetric[];
  dataSource?: string;
}

export function KeyMetrics({ ticker }: { ticker: string }) {
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { currency, convertValue } = useChatContext();
  const currencySymbol = getCurrencySymbol(currency);

  useEffect(() => {
    if (ticker) {
      const fetchMetrics = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8100/api/stock/${ticker}/metrics`);
          if (!response.ok) {
            throw new Error('Failed to fetch key metrics.');
          }
          const responseData = await response.json();
          setData(responseData);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchMetrics();
    }
  }, [ticker]);

  // Format value with currency conversion
  const formatMetricValue = (metric: KeyMetric): string => {
    if (!metric.isCurrency || metric.rawValue === undefined || metric.rawValue === null) {
      return metric.value;
    }

    // Convert to selected currency
    const converted = convertValue(metric.rawValue, 'USD');
    if (converted === null) return metric.value;

    // Format based on size
    const absValue = Math.abs(converted);
    if (absValue >= 1e12) {
      return `${currencySymbol}${(converted / 1e12).toFixed(2)}T`;
    }
    if (absValue >= 1e9) {
      return `${currencySymbol}${(converted / 1e9).toFixed(2)}B`;
    }
    if (absValue >= 1e6) {
      return `${currencySymbol}${(converted / 1e6).toFixed(2)}M`;
    }
    if (absValue >= 1e3) {
      return `${currencySymbol}${(converted / 1e3).toFixed(2)}K`;
    }
    return `${currencySymbol}${converted.toFixed(2)}`;
  };

  if (loading) return <p>Loading key metrics...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data || !data.metrics.length) return <p>No key metrics available.</p>;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Key Metrics ({currency})</CardTitle>
          <DataSourceBadge source={data.dataSource} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {data.metrics.map((metric) => (
            <div key={metric.label}>
              <p className="font-semibold">{metric.label}</p>
              <p>{formatMetricValue(metric)}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}