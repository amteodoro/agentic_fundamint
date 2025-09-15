'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartData {
  Date: string;
  "Enterprise Value"?: number;
}

export function EnterpriseValueChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const [historyRes, balanceSheetRes, profileRes] = await Promise.all([
            fetch(`http://localhost:8000/api/stock/${ticker}/price-history?period=10y`),
            fetch(`http://localhost:8000/api/stock/${ticker}/balance-sheet`),
            fetch(`http://localhost:8000/api/stock/${ticker}/profile`)
          ]);

          if (!historyRes.ok || !balanceSheetRes.ok || !profileRes.ok) {
            throw new Error('Failed to fetch data for Enterprise Value chart.');
          }

          const historyData = await historyRes.json();
          const balanceSheetData = await balanceSheetRes.json();
          const profileData = await profileRes.json();

          const sharesOutstanding = profileData.sharesOutstanding;

          const chartData = balanceSheetData.balance_sheet.map((d: any) => {
            const year = d.Date.split('-')[0];
            const yearEndPrice = historyData.history.find((h: any) => h.Date.startsWith(year))?.Close;
            const marketCap = yearEndPrice && sharesOutstanding ? yearEndPrice * sharesOutstanding : 0;
            const netDebt = d["Total Debt"] - d["Cash And Cash Equivalents"];
            return {
              Date: year,
              "Enterprise Value": marketCap && netDebt ? (marketCap + netDebt) / 1e6 : undefined,
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

  if (loading) return <p>Loading Enterprise Value chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No data available for Enterprise Value chart.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Enterprise Value</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="Date" />
            <YAxis unit="M" />
            <Tooltip formatter={(value: number) => `${value.toFixed(2)}M`} />
            <Legend />
            <Bar dataKey="Enterprise Value" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}