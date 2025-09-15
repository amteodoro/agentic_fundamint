'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface KeyMetric {
  label: string;
  value: string;
}

export function KeyMetrics({ ticker }: { ticker: string }) {
  const [metrics, setMetrics] = useState<KeyMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchMetrics = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8000/api/stock/${ticker}/metrics`);
          if (!response.ok) {
            throw new Error('Failed to fetch key metrics.');
          }
          const data = await response.json();
          setMetrics(data.metrics);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchMetrics();
    }
  }, [ticker]);

  if (loading) return <p>Loading key metrics...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!metrics.length) return <p>No key metrics available.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Key Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {metrics.map((metric) => (
            <div key={metric.label}>
              <p className="font-semibold">{metric.label}</p>
              <p>{metric.value}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}