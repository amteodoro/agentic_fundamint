'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartData {
  Date: string;
  "Annual Net Income"?: number;
  PER?: number;
}

export function NetIncomePERChart({ ticker }: { ticker: string }) {
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
            throw new Error('Failed to fetch data for Net Income & PER chart.');
          }

          const financialsData = await financialsRes.json();
          const historyData = await historyRes.json();
          const profileData = await profileRes.json();

          const sharesOutstanding = profileData.sharesOutstanding;

          const chartData = financialsData.financials.map((d: any) => {
            const year = d.Date.split('-')[0];
            const yearEndPrice = historyData.history.find((h: any) => h.Date.startsWith(year))?.Close;
            const marketCap = yearEndPrice && sharesOutstanding ? yearEndPrice * sharesOutstanding : 0;
            const netIncome = d["Net Income"];

            return {
              Date: year,
              "Annual Net Income": netIncome / 1e6,
              PER: marketCap && netIncome ? marketCap / netIncome : undefined,
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

  if (loading) return <p>Loading Net Income & PER chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No data available for Net Income & PER chart.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Net Income & PER</CardTitle>
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
            <Bar yAxisId="left" dataKey="Annual Net Income" fill="#8884d8" />
            <Line yAxisId="right" type="monotone" dataKey="PER" stroke="#82ca9d" />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}