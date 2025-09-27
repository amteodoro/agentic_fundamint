'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Label } from 'recharts';
import { formatNumber, CustomTooltip, COLORS } from '@/lib/chart-utils';

interface ChartData {
  Date: string;
  "Annual EBITDA"?: number;
  "EV/EBITDA"?: number;
}

export function EBITDA_EV_EBITDA_Chart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const [financialsRes, historyRes, balanceSheetRes, profileRes] = await Promise.all([
            fetch(`http://localhost:8000/api/stock/${ticker}/financials`),
            fetch(`http://localhost:8000/api/stock/${ticker}/price-history?period=10y`),
            fetch(`http://localhost:8000/api/stock/${ticker}/balance-sheet`),
            fetch(`http://localhost:8000/api/stock/${ticker}/profile`)
          ]);

          if (!financialsRes.ok || !historyRes.ok || !balanceSheetRes.ok || !profileRes.ok) {
            throw new Error('Failed to fetch data for EBITDA & EV/EBITDA chart.');
          }

          const financialsData = await financialsRes.json();
          const historyData = await historyRes.json();
          const balanceSheetData = await balanceSheetRes.json();
          const profileData = await profileRes.json();

          const sharesOutstanding = profileData.sharesOutstanding;

          const sortedFinancials = financialsData.financials.sort((a: any, b: any) => new Date(a.Date).getTime() - new Date(b.Date).getTime());

          const chartData = sortedFinancials.map((d: any) => {
            const year = d.Date.split('-')[0];
            const yearEndPrice = historyData.history.find((h: any) => h.Date.startsWith(year))?.Close;
            const marketCap = yearEndPrice && sharesOutstanding ? yearEndPrice * sharesOutstanding : 0;
            const balanceSheetEntry = balanceSheetData.balance_sheet.find((bs: any) => bs.Date.startsWith(year));
            if (!balanceSheetEntry) return null;

            const netDebt = balanceSheetEntry["Total Debt"] - balanceSheetEntry["Cash And Cash Equivalents"];
            const enterpriseValue = marketCap + netDebt;
            const ebitda = d["EBITDA"];

            return {
              Date: year,
              "Annual EBITDA": ebitda,
              "EV/EBITDA": enterpriseValue && ebitda ? enterpriseValue / ebitda : undefined,
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
        <CardTitle>EBITDA & EV/EBITDA</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>Loading EBITDA & EV/EBITDA chart...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return (
    <Card>
      <CardHeader>
        <CardTitle>EBITDA & EV/EBITDA</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>No data available for EBITDA & EV/EBITDA chart.</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>EBITDA & EV/EBITDA</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
            <XAxis dataKey="Date" />
            <YAxis yAxisId="left" tickFormatter={(tick) => formatNumber(tick, 0)}>
              <Label value="Annual EBITDA" angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <YAxis yAxisId="right" orientation="right" tickFormatter={(tick) => formatNumber(tick, 1)}>
              <Label value="EV/EBITDA" angle={-90} position="insideRight" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar yAxisId="left" dataKey="Annual EBITDA" fill={COLORS[0]} />
            <Line yAxisId="right" type="monotone" dataKey="EV/EBITDA" stroke={COLORS[1]} />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}