'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label } from 'recharts';
import { formatNumber, CustomTooltip, COLORS } from '@/lib/chart-utils';

interface DividendData {
  Date: string;
  Dividends: number;
}

export function DividendsChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<DividendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8100/api/stock/${ticker}/dividends`);
          if (!response.ok) {
            throw new Error('Failed to fetch dividend history.');
          }
          const result = await response.json();
          
          // Aggregate dividends by year
          const annualDividends: { [year: string]: number } = {};
          result.history.forEach((d: any) => {
            const year = d.Date.split('-')[0];
            if (!annualDividends[year]) {
              annualDividends[year] = 0;
            }
            annualDividends[year] += d.Dividends;
          });

          const chartData = Object.keys(annualDividends).map(year => ({
            Date: year,
            Dividends: annualDividends[year],
          }));

          const sortedData = chartData.sort((a, b) => Number(a.Date) - Number(b.Date));
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
        <CardTitle>Annual Dividends</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>Loading dividends chart...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return (
    <Card>
      <CardHeader>
        <CardTitle>Annual Dividends</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>No dividend data available.</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Annual Dividends</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
            <XAxis dataKey="Date" />
            <YAxis tickFormatter={(tick) => formatNumber(tick, 2)}>
              <Label value="Dividends (USD)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="Dividends" fill={COLORS[0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}