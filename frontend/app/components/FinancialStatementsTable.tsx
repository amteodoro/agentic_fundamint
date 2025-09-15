'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface FinancialStatementRow {
  Date: string;
  [key: string]: any;
}

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

  if (loading) return <p>Loading financial statements...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!financials.length) return <p>No financial statements available.</p>;

  const headers = Object.keys(financials[0]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Statements</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              {headers.map(header => <TableHead key={header}>{header}</TableHead>)}
            </TableRow>
          </TableHeader>
          <TableBody>
            {financials.map((row, index) => (
              <TableRow key={index}>
                {headers.map(header => (
                  <TableCell key={header}>
                    {typeof row[header] === 'number' ? row[header].toLocaleString() : row[header]}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}