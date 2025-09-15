'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Line } from 'recharts';

interface FinancialsData {
  Date: string;
  "Total Revenue"?: number;
  "Net Income"?: number;
  EBITDA?: number;
  "Diluted EPS"?: number;
}

export function FinancialSummaryChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<FinancialsData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8000/api/stock/${ticker}/financials`);
          if (!response.ok) {
            throw new Error('Failed to fetch financial summary.');
          }
          const result = await response.json();
          setData(result.financials.map((d: any) => ({ ...d, Date: d.Date.split('-')[0] })));
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [ticker]);

  if (loading) return <p>Loading financial summary chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No financial summary data available.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="Date" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="Total Revenue" fill="#8884d8" />
            <Bar yAxisId="left" dataKey="Net Income" fill="#82ca9d" />
            <Bar yAxisId="left" dataKey="EBITDA" fill="#ffc658" />
            <Line yAxisId="right" type="monotone" dataKey="Diluted EPS" stroke="#ff7300" />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}