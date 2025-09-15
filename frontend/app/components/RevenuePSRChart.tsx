'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartData {
  Date: string;
  "Annual Revenue"?: number;
  PSR?: number;
}

export function RevenuePSRChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const [financialsRes, historyRes, profileRes] = await Promise.all([
            fetch(`http://localhost:8000/api/stock/${ticker}/financials`),
            fetch(`http://localhost:8000/api/stock/${ticker}/price-history?period=10y`),
            fetch(`http://localhost:8000/api/stock/${ticker}/profile`)
          ]);

          if (!financialsRes.ok || !historyRes.ok || !profileRes.ok) {
            throw new Error('Failed to fetch data for Revenue & PSR chart.');
          }

          const financialsData = await financialsRes.json();
          const historyData = await historyRes.json();
          const profileData = await profileRes.json();

          const sharesOutstanding = profileData.sharesOutstanding;

          const chartData = financialsData.financials.map((d: any) => {
            const year = d.Date.split('-')[0];
            const yearEndPrice = historyData.history.find((h: any) => h.Date.startsWith(year))?.Close;
            const marketCap = yearEndPrice && sharesOutstanding ? yearEndPrice * sharesOutstanding : 0;
            const revenue = d["Total Revenue"];

            return {
              Date: year,
              "Annual Revenue": revenue / 1e6,
              PSR: marketCap && revenue ? marketCap / revenue : undefined,
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

  if (loading) return <p>Loading Revenue & PSR chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No data available for Revenue & PSR chart.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue & PSR</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="Date" />
            <YAxis yAxisId="left" unit="M" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="Annual Revenue" fill="#8884d8" />
            <Line yAxisId="right" type="monotone" dataKey="PSR" stroke="#82ca9d" />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}