'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Label } from 'recharts';
import { formatNumber, CustomTooltip, COLORS } from '@/lib/chart-utils';

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
          const sortedData = result.financials.sort((a: any, b: any) => new Date(a.Date).getTime() - new Date(b.Date).getTime());
          setData(sortedData.map((d: any) => ({ ...d, Date: d.Date.split('-')[0] })));
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
        <CardTitle>Financial Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>Loading financial summary chart...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>No financial summary data available.</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
            <XAxis dataKey="Date" />
            <YAxis yAxisId="left" tickFormatter={(tick) => formatNumber(tick, 0)}>
              <Label value="Amount (USD)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <YAxis yAxisId="right" orientation="right" tickFormatter={(tick) => formatNumber(tick, 2)}>
              <Label value="Diluted EPS (USD)" angle={-90} position="insideRight" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar yAxisId="left" dataKey="Total Revenue" fill={COLORS[0]} />
            <Bar yAxisId="left" dataKey="Net Income" fill={COLORS[1]} />
            <Bar yAxisId="left" dataKey="EBITDA" fill={COLORS[2]} />
            <Line yAxisId="right" type="monotone" dataKey="Diluted EPS" stroke={COLORS[3]} />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}