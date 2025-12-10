'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label } from 'recharts';
import { formatNumber, CustomTooltip, COLORS } from '@/lib/chart-utils';

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
          const response = await fetch(`http://localhost:8100/api/stock/${ticker}/price-history`);
          if (!response.ok) {
            throw new Error('Failed to fetch price history.');
          }
          const result = await response.json();
          const sortedData = result.history.sort((a: PriceData, b: PriceData) => new Date(a.Date).getTime() - new Date(b.Date).getTime());
          setData(sortedData);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [ticker]);

  if (loading) return (
    <Card>
      <CardHeader>
        <CardTitle>Price Chart</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>Loading price chart...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return (
    <Card>
      <CardHeader>
        <CardTitle>Price Chart</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>No price data available.</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price Chart</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
            <XAxis dataKey="Date" />
            <YAxis tickFormatter={(tick) => formatNumber(tick, 2)}>
              <Label value="Price (USD)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="Close" stroke={COLORS[0]} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}