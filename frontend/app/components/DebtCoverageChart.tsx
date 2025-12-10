'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Label } from 'recharts';
import { formatNumber, CustomTooltip, COLORS } from '@/lib/chart-utils';

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
            fetch(`http://localhost:8100/api/stock/${ticker}/balance-sheet`),
            fetch(`http://localhost:8100/api/stock/${ticker}/financials`)
          ]);

          if (!balanceSheetRes.ok || !financialsRes.ok) {
            throw new Error('Failed to fetch data for Debt Coverage chart.');
          }

          const balanceSheetData = await balanceSheetRes.json();
          const financialsData = await financialsRes.json();

          const sortedFinancials = financialsData.financials.sort((a: any, b: any) => new Date(a.Date).getTime() - new Date(b.Date).getTime());

          const chartData = sortedFinancials.map((d: any) => {
            const year = d.Date.split('-')[0];
            const balanceSheetEntry = balanceSheetData.balance_sheet.find((bs: any) => bs.Date.startsWith(year));
            if (!balanceSheetEntry) return null;

            const netDebt = balanceSheetEntry["Total Debt"] - balanceSheetEntry["Cash And Cash Equivalents"];
            const ebitda = d["EBITDA"];

            return {
              Date: year,
              "Net Debt": netDebt,
              "Net Debt / EBITDA": ebitda ? netDebt / ebitda : undefined,
            }
          }).filter(Boolean);

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

  if (loading) return (
    <Card>
      <CardHeader>
        <CardTitle>Debt & Coverage</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>Loading Debt & Coverage chart...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return (
    <Card>
      <CardHeader>
        <CardTitle>Debt & Coverage</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>No data available for Debt & Coverage chart.</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Debt & Coverage</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
            <XAxis dataKey="Date" />
            <YAxis yAxisId="left" tickFormatter={(tick) => formatNumber(tick, 0)}>
              <Label value="Net Debt" angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <YAxis yAxisId="right" orientation="right" tickFormatter={(tick) => formatNumber(tick, 1)}>
              <Label value="Net Debt / EBITDA" angle={-90} position="insideRight" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar yAxisId="left" dataKey="Net Debt" fill={COLORS[0]} />
            <Line yAxisId="right" type="monotone" dataKey="Net Debt / EBITDA" stroke={COLORS[1]} />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}