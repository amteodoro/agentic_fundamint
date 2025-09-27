'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from '@/lib/utils';

interface FinancialStatementRow {
  Date: string;
  [key: string]: any;
}

const formatNumber = (num: number) => {
  if (num === 0) return '0';
  if (Math.abs(num) >= 1e9) {
    return `${(num / 1e9).toFixed(2)}B`;
  }
  if (Math.abs(num) >= 1e6) {
    return `${(num / 1e6).toFixed(2)}M`;
  }
  if (Math.abs(num) >= 1e3) {
    return `${(num / 1e3).toFixed(2)}K`;
  }
  return num.toLocaleString();
};

export function FinancialStatementsTable({ ticker }: { ticker: string }) {
  const [financials, setFinancials] = useState<FinancialStatementRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchFinancials = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8000/api/stock/${ticker}/financials`);
          if (!response.ok) {
            throw new Error('Failed to fetch financial statements.');
          }
          const data = await response.json();
          setFinancials(data.financials);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchFinancials();
    }
  }, [ticker]);

  if (loading) return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Statements</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[400px] w-full flex items-center justify-center">
          <p>Loading financial statements...</p>
        </div>
      </CardContent>
    </Card>
  );
  if (error) return <p className="text-red-500">{error}</p>;
  if (!financials.length) return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Statements</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[400px] w-full flex items-center justify-center">
          <p>No financial statements available.</p>
        </div>
      </CardContent>
    </Card>
  );

  const headers = Object.keys(financials[0]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Statements</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                {headers.map(header => <TableHead key={header}>{header}</TableHead>)}
              </TableRow>
            </TableHeader>
            <TableBody>
              {financials.map((row, index) => (
                <TableRow key={index} className={cn(index % 2 === 0 ? 'bg-muted/50' : '')}>
                  {headers.map(header => (
                    <TableCell key={header} className={cn(
                      typeof row[header] === 'number' && row[header] < 0 ? 'text-red-500' : '',
                      typeof row[header] === 'number' && row[header] > 0 ? 'text-green-500' : ''
                    )}>
                      {typeof row[header] === 'number' ? formatNumber(row[header]) : row[header]}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}