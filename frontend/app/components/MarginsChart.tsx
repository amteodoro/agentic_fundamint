'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface MarginsData {
  Date: string;
  "Gross Margin"?: number;
  "Net Margin"?: number;
  "Op. Margin"?: number;
  "EBITDA Margin"?: number;
}

export function MarginsChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<MarginsData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const financialsRes = await fetch(`http://localhost:8000/api/stock/${ticker}/financials`);
          if (!financialsRes.ok) throw new Error('Failed to fetch financials for margins.');
          const financialsData = await financialsRes.json();
          
          const margins = financialsData.financials.map((d: any) => {
            const revenue = d["Total Revenue"];
            return {
              Date: d.Date.split('-')[0],
              "Gross Margin": revenue ? (d["Gross Profit"] / revenue) * 100 : 0,
              "Net Margin": revenue ? (d["Net Income"] / revenue) * 100 : 0,
              "Op. Margin": revenue ? (d["Operating Income"] / revenue) * 100 : 0,
              "EBITDA Margin": revenue ? (d["EBITDA"] / revenue) * 100 : 0,
            }
          });
          setData(margins);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [ticker]);

  if (loading) return <p>Loading margins chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No margins data available.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profit Margins</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="Date" />
            <YAxis unit="%" />
            <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
            <Legend />
            <Line type="monotone" dataKey="Gross Margin" stroke="#8884d8" />
            <Line type="monotone" dataKey="Net Margin" stroke="#82ca9d" />
            <Line type="monotone" dataKey="Op. Margin" stroke="#ffc658" />
            <Line type="monotone" dataKey="EBITDA Margin" stroke="#ff7300" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}