'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PriceData {
  Date: string;
  Close: number;
}

export function PriceChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<PriceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8000/api/stock/${ticker}/price-history`);
          if (!response.ok) {
            throw new Error('Failed to fetch price history.');
          }
          const result = await response.json();
          setData(result.history);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [ticker]);

  if (loading) return <p>Loading price chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No price data available.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price Chart</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="Date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="Close" stroke="#8884d8" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}