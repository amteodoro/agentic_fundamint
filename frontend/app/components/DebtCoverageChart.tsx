'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartData {
  Date: string;
  "Net Debt"?: number;
  "Net Debt / EBITDA"?: number;
}

export function DebtCoverageChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const [balanceSheetRes, financialsRes] = await Promise.all([
            fetch(`http://localhost:8000/api/stock/${ticker}/balance-sheet`),
            fetch(`http://localhost:8000/api/stock/${ticker}/financials`)
          ]);

          if (!balanceSheetRes.ok || !financialsRes.ok) {
            throw new Error('Failed to fetch data for Debt Coverage chart.');
          }

          const balanceSheetData = await balanceSheetRes.json();
          const financialsData = await financialsRes.json();

          const chartData = financialsData.financials.map((d: any) => {
            const year = d.Date.split('-')[0];
            const balanceSheetEntry = balanceSheetData.balance_sheet.find((bs: any) => bs.Date.startsWith(year));
            if (!balanceSheetEntry) return null;

            const netDebt = balanceSheetEntry["Total Debt"] - balanceSheetEntry["Cash And Cash Equivalents"];
            const ebitda = d["EBITDA"];

            return {
              Date: year,
              "Net Debt": netDebt / 1e6,
              "Net Debt / EBITDA": ebitda ? netDebt / ebitda : undefined,
            }
          }).filter(Boolean);

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

  if (loading) return <p>Loading Debt Coverage chart...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>No data available for Debt Coverage chart.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Debt & Coverage</CardTitle>
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
            <Bar yAxisId="left" dataKey="Net Debt" fill="#8884d8" />
            <Line yAxisId="right" type="monotone" dataKey="Net Debt / EBITDA" stroke="#82ca9d" />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}