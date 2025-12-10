"use client";

import { CompanyProfile } from '@/app/components/CompanyProfile';
import { DebtCoverageChart } from '@/app/components/DebtCoverageChart';
import { DividendsChart } from '@/app/components/DividendsChart';
import { EBITDA_EV_EBITDA_Chart } from '@/app/components/EBITDA_EV_EBITDA_Chart';
import { EnterpriseValueChart } from '@/app/components/EnterpriseValueChart';
import { FinancialStatementsTable } from '@/app/components/FinancialStatementsTable';
import { FinancialSummaryChart } from '@/app/components/FinancialSummaryChart';
import { HighGrowthAnalysis } from '@/app/components/HighGrowthAnalysis';
import { KeyMetrics } from '@/app/components/KeyMetrics';
import { MarginsChart } from '@/app/components/MarginsChart';
import { MarketCapSharesChart } from '@/app/components/MarketCapSharesChart';
import { NetIncomePERChart } from '@/app/components/NetIncomePERChart';
import { PhilTownAnalysis } from '@/app/components/PhilTownAnalysis';
import { PriceChart } from '@/app/components/PriceChart';
import { RevenuePSRChart } from '@/app/components/RevenuePSRChart';
import { CompetitorComparison } from '@/app/components/CompetitorComparison';
import { DeepDiveAnalysis } from '@/app/components/DeepDiveAnalysis';
import { PriceProjectionAnalysis } from '@/app/components/PriceProjectionAnalysis';
import { SummaryTable } from '@/app/components/SummaryTable';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useEffect, useState } from 'react';
import { useChatContext } from '@/app/context/ChatContext';

// Define types for the data we'll fetch
interface ProfileData {
  longName?: string;
  sector?: string;
  industry?: string;
  longBusinessSummary?: string;
  website?: string;
  fullTimeEmployees?: number;
}

export default function StockDetailPage({ params }: { params: { ticker: string } }) {
  const { ticker } = params;
  const { setTicker, activeTab, setActiveTab } = useChatContext();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTicker(ticker);
    return () => setTicker(null);
  }, [ticker, setTicker]);

  useEffect(() => {
    if (ticker) {
      const fetchData = async () => {
        try {
          setLoading(true);
          setError(null);

          const profileRes = await fetch(`http://localhost:8100/api/stock/${ticker}/profile`);
          if (!profileRes.ok) throw new Error(`Failed to fetch profile for ${ticker}`);
          const profileData = await profileRes.json();
          setProfile(profileData);

        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [ticker]);

  if (loading) {
    return <div className="flex justify-center items-center min-h-screen">Loading data for {ticker.toUpperCase()}...</div>;
  }

  if (error) {
    return <div className="flex justify-center items-center min-h-screen text-red-500">Error: {error}</div>;
  }

  if (!profile) {
    return <div className="flex justify-center items-center min-h-screen">No data found for {ticker.toUpperCase()}.</div>;
  }

  return (
    <div className="container mx-auto p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{profile.longName} ({ticker.toUpperCase()})</h1>
        <p className="text-lg text-gray-600">{profile.sector} | {profile.industry}</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-1 sm:grid-cols-4 md:grid-cols-8">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="price-target">Price Target</TabsTrigger>
          <TabsTrigger value="phil-town">Sticker Price</TabsTrigger>
          <TabsTrigger value="high-growth">High-Growth</TabsTrigger>
          <TabsTrigger value="competitors">Competitors</TabsTrigger>
          <TabsTrigger value="deep-dive">Deep Dive</TabsTrigger>
          <TabsTrigger value="charts">Charts</TabsTrigger>
          <TabsTrigger value="financials">Financials</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="md:col-span-2">
              <CompanyProfile ticker={ticker} />
            </div>
            <div>
              <KeyMetrics ticker={ticker} />
            </div>
          </div>
          <div className="mt-8">
            <SummaryTable ticker={ticker} />
          </div>
        </TabsContent>

        <TabsContent value="phil-town" className="mt-4">
          <PhilTownAnalysis ticker={ticker} />
        </TabsContent>

        <TabsContent value="price-target" className="mt-4">
          <PriceProjectionAnalysis ticker={ticker} />
        </TabsContent>

        <TabsContent value="high-growth" className="mt-4">
          <HighGrowthAnalysis ticker={ticker} />
        </TabsContent>

        <TabsContent value="competitors" className="mt-4">
          <CompetitorComparison ticker={ticker} />
        </TabsContent>

        <TabsContent value="deep-dive" className="mt-4">
          <DeepDiveAnalysis ticker={ticker} />
        </TabsContent>

        <TabsContent value="charts" className="mt-4">
          <div className="grid grid-cols-1 gap-8">
            <PriceChart ticker={ticker} />
            <FinancialSummaryChart ticker={ticker} />
            <MarginsChart ticker={ticker} />
            <MarketCapSharesChart ticker={ticker} />
            <EnterpriseValueChart ticker={ticker} />
            <DividendsChart ticker={ticker} />
            <DebtCoverageChart ticker={ticker} />
            <RevenuePSRChart ticker={ticker} />
            <EBITDA_EV_EBITDA_Chart ticker={ticker} />
            <NetIncomePERChart ticker={ticker} />
          </div>
        </TabsContent>
        <TabsContent value="financials" className="mt-4">
          <FinancialStatementsTable ticker={ticker} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
