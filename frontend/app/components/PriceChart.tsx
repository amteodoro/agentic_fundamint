'use client';

import { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label } from 'recharts';
import { createCurrencyFormatter, createCurrencyTooltip, COLORS } from '@/lib/chart-utils';
import { useChatContext, getCurrencySymbol } from '@/app/context/ChatContext';

interface PriceData {
  Date: string;
  Close: number;
}

export function PriceChart({ ticker }: { ticker: string }) {
  const [data, setData] = useState<PriceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { currency, exchangeRate } = useChatContext();
  const currencySymbol = getCurrencySymbol(currency);

  // Create currency-aware formatters
  const tickFormatter = useMemo(() =>
    createCurrencyFormatter(currencySymbol, currency === 'EUR' ? exchangeRate : 1, 2, true),
    [currencySymbol, currency, exchangeRate]
  );

  const CurrencyTooltip = useMemo(() =>
    createCurrencyTooltip(currencySymbol, currency === 'EUR' ? exchangeRate : 1),
    [currencySymbol, currency, exchangeRate]
  );

  // Convert data to selected currency
  const convertedData = useMemo(() => {
    if (currency === 'EUR' && exchangeRate) {
      return data.map(d => ({
        ...d,
        Close: d.Close * exchangeRate
      }));
    }
    return data;
  }, [data, currency, exchangeRate]);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8100/api/stock/${ticker}/price-history`);
          if (!response.ok) {
            throw new Error('Failed to fetch price history.');
          }
          const result = await response.json();
          const sortedData = result.history.sort((a: PriceData, b: PriceData) => new Date(a.Date).getTime() - new Date(b.Date).getTime());
          setData(sortedData);
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
        <CardTitle>Price Chart ({currency})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>Loading price chart...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return (
    <Card>
      <CardHeader>
        <CardTitle>Price Chart ({currency})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full flex items-center justify-center">
          <p>No price data available.</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price Chart ({currency})</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={convertedData}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
            <XAxis dataKey="Date" />
            <YAxis tickFormatter={tickFormatter}>
              <Label value={`Price (${currency})`} angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
            </YAxis>
            <Tooltip content={<CurrencyTooltip />} />
            <Line type="monotone" dataKey="Close" stroke={COLORS[0]} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}