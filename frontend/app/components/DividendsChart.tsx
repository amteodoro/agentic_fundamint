'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

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
          const response = await fetch(`http://localhost:8000/api/stock/${ticker}/dividends`);
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

          setData(chartData);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [ticker]);

  if (loading) return <p>Loading dividends chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No dividend data available.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Annual Dividends</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="Date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="Dividends" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}