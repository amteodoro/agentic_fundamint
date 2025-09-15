'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartData {
  Date: string;
  "Market Cap"?: number;
  "Shares Outstanding"?: number;
}

export function MarketCapSharesChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const [historyRes, financialsRes, profileRes] = await Promise.all([
            fetch(`http://localhost:8000/api/stock/${ticker}/price-history?period=10y`),
            fetch(`http://localhost:8000/api/stock/${ticker}/financials`),
            fetch(`http://localhost:8000/api/stock/${ticker}/profile`)
          ]);

          if (!historyRes.ok || !financialsRes.ok || !profileRes.ok) {
            throw new Error('Failed to fetch data for Market Cap & Shares chart.');
          }

          const historyData = await historyRes.json();
          const financialsData = await financialsRes.json();
          const profileData = await profileRes.json();

          const sharesOutstanding = profileData.sharesOutstanding;

          const chartData = financialsData.financials.map((d: any) => {
            const year = d.Date.split('-')[0];
            const yearEndPrice = historyData.history.find((h: any) => h.Date.startsWith(year))?.Close;
            return {
              Date: year,
              "Market Cap": yearEndPrice && sharesOutstanding ? (yearEndPrice * sharesOutstanding) / 1e6 : undefined,
              "Shares Outstanding": d["Diluted Average Shares"] / 1e6 || d["Basic Average Shares"] / 1e6 || undefined,
            }
          });

          setData(chartData.reverse());
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [ticker]);

  if (loading) return <p>Loading Market Cap & Shares chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No data available for Market Cap & Shares chart.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Cap & Shares Outstanding</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="Date" />
            <YAxis yAxisId="left" unit="M" />
            <YAxis yAxisId="right" orientation="right" unit="M" />
            <Tooltip formatter={(value: number, name: string) => `${value.toFixed(2)}M`} />
            <Legend />
            <Bar yAxisId="left" dataKey="Market Cap" fill="#8884d8" />
            <Line yAxisId="right" type="monotone" dataKey="Shares Outstanding" stroke="#82ca9d" />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}