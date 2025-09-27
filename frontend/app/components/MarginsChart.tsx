'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Label } from 'recharts';
import { CustomTooltip, COLORS, formatNumber } from '@/lib/chart-utils';

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
          
          const sortedFinancials = financialsData.financials.sort((a: any, b: any) => new Date(a.Date).getTime() - new Date(b.Date).getTime());
          const margins = sortedFinancials.map((d: any) => {
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

  if (loading) return (
    <Card>
      <CardHeader>
        <CardTitle>Profit Margins</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>Loading margins chart...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return (
    <Card>
      <CardHeader>
        <CardTitle>Profit Margins</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>No margins data available.</p>
        </div>
      </CardContent>
    </Card>
  );

  const formatYAxis = (tick: number) => `${formatNumber(tick, 0)}%`;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profit Margins</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
            <XAxis dataKey="Date" />
            <YAxis tickFormatter={formatYAxis}>
              <Label value="Margin (%)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line type="monotone" dataKey="Gross Margin" stroke={COLORS[0]} />
            <Line type="monotone" dataKey="Net Margin" stroke={COLORS[1]} />
            <Line type="monotone" dataKey="Op. Margin" stroke={COLORS[2]} />
            <Line type="monotone" dataKey="EBITDA Margin" stroke={COLORS[3]} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}