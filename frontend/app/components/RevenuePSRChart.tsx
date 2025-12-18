'use client';

import { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Label } from 'recharts';
import { formatNumber, createCurrencyFormatter, createCurrencyTooltip, COLORS } from '@/lib/chart-utils';
import { useChatContext, getCurrencySymbol } from '@/app/context/ChatContext';

interface ChartData {
  Date: string;
  "Annual Revenue"?: number;
  PSR?: number;
}

export function RevenuePSRChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { currency, exchangeRate } = useChatContext();
  const currencySymbol = getCurrencySymbol(currency);
  const rate = currency === 'EUR' ? exchangeRate : 1;

  const revenueFormatter = useMemo(() =>
    createCurrencyFormatter(currencySymbol, rate, 0, true),
    [currencySymbol, rate]
  );

  const CurrencyTooltip = useMemo(() =>
    createCurrencyTooltip(currencySymbol, rate),
    [currencySymbol, rate]
  );

  const convertedData = useMemo(() => {
    if (currency === 'EUR' && exchangeRate) {
      return data.map(d => ({
        ...d,
        "Annual Revenue": d["Annual Revenue"] ? d["Annual Revenue"] * exchangeRate : undefined
      }));
    }
    return data;
  }, [data, currency, exchangeRate]);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const [financialsRes, historyRes, profileRes] = await Promise.all([
            fetch(`http://localhost:8100/api/stock/${ticker}/financials`),
            fetch(`http://localhost:8100/api/stock/${ticker}/price-history?period=10y`),
            fetch(`http://localhost:8100/api/stock/${ticker}/profile`)
          ]);

          if (!financialsRes.ok || !historyRes.ok || !profileRes.ok) {
            throw new Error('Failed to fetch data for Revenue & PSR chart.');
          }

          const financialsData = await financialsRes.json();
          const historyData = await historyRes.json();
          const profileData = await profileRes.json();

          const sharesOutstanding = profileData.sharesOutstanding;

          const sortedFinancials = financialsData.financials.sort((a: any, b: any) => new Date(a.Date).getTime() - new Date(b.Date).getTime());

          const chartData = sortedFinancials.map((d: any) => {
            const year = d.Date.split('-')[0];
            const yearEndPrice = historyData.history.find((h: any) => h.Date.startsWith(year))?.Close;
            const marketCap = yearEndPrice && sharesOutstanding ? yearEndPrice * sharesOutstanding : 0;
            const revenue = d["Total Revenue"];

            return {
              Date: year,
              "Annual Revenue": revenue,
              PSR: marketCap && revenue ? marketCap / revenue : undefined,
            }
          });

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
        <CardTitle>Revenue & PSR ({currency})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>Loading Revenue & PSR chart...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue & PSR ({currency})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>No data available for Revenue & PSR chart.</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue & PSR ({currency})</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={convertedData}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
            <XAxis dataKey="Date" />
            <YAxis yAxisId="left" tickFormatter={revenueFormatter}>
              <Label value={`Annual Revenue (${currency})`} angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <YAxis yAxisId="right" orientation="right" tickFormatter={(tick) => formatNumber(tick, 1)}>
              <Label value="PSR" angle={-90} position="insideRight" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <Tooltip content={<CurrencyTooltip />} />
            <Legend />
            <Bar yAxisId="left" dataKey="Annual Revenue" fill={COLORS[0]} />
            <Line yAxisId="right" type="monotone" dataKey="PSR" stroke={COLORS[1]} />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}