'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PhilTownData {
  moat: any;
  management: any;
  mos: any;
  growth_rates: any;
}

export function PhilTownAnalysis({ ticker }: { ticker: string }) {
  const [analysis, setAnalysis] = useState<PhilTownData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchAnalysis = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://localhost:8000/api/analysis/${ticker}/phil-town`);
          if (!response.ok) {
            throw new Error('Failed to fetch Phil Town analysis.');
          }
          const data = await response.json();
          setAnalysis(data);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchAnalysis();
    }
  }, [ticker]);

  if (loading) return <p>Loading Phil Town analysis...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!analysis) return <p>No Phil Town analysis available.</p>;

  const { moat, management, mos, growth_rates } = analysis;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Phil Town's Rule #1 Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold">Moat Evaluation</h3>
            <p>ROIC (avg): {moat.avg_roic ? `${(moat.avg_roic * 100).toFixed(2)}%` : 'N/A'}</p>
            <p>EPS Growth: {growth_rates.eps_cagr ? `${(growth_rates.eps_cagr * 100).toFixed(2)}%` : 'N/A'}</p>
            <p>BVPS Growth: {growth_rates.bvps_cagr ? `${(growth_rates.bvps_cagr * 100).toFixed(2)}%` : 'N/A'}</p>
            <p>Sales Growth: {growth_rates.sales_cagr ? `${(growth_rates.sales_cagr * 100).toFixed(2)}%` : 'N/A'}</p>
            <p>FCF Growth: {growth_rates.fcf_cagr ? `${(growth_rates.fcf_cagr * 100).toFixed(2)}%` : 'N/A'}</p>
          </div>
          <div>
            <h3 className="text-lg font-semibold">Management Evaluation</h3>
            <p>Debt Payoff Years: {management.debt_payoff_years ? management.debt_payoff_years.toFixed(2) : 'N/A'}</p>
            <p>Insider Ownership: {management.insider_ownership ? `${(management.insider_ownership * 100).toFixed(2)}%` : 'N/A'}</p>
          </div>
          <div>
            <h3 className="text-lg font-semibold">Margin of Safety (MOS)</h3>
            <p>Current EPS: {mos.current_eps ? `${mos.current_eps.toFixed(2)}` : 'N/A'}</p>
            <p>Future EPS: {mos.future_eps ? `${mos.future_eps.toFixed(2)}` : 'N/A'}</p>
            <p>Sticker Price: {mos.sticker_price ? `${mos.sticker_price.toFixed(2)}` : 'N/A'}</p>
            <p>MOS Price: {mos.mos_price ? `${mos.mos_price.toFixed(2)}` : 'N/A'}</p>
            <p>Current Market Price: {mos.current_market_price ? `${mos.current_market_price.toFixed(2)}` : 'N/A'}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}