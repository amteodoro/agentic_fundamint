"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { StockSearchInput } from "@/app/components/StockSearchInput";
import { EarningsCalendar } from "@/app/components/EarningsCalendar";
import { EarningsDetails } from "@/app/components/EarningsDetails";

export default function Home() {
  const router = useRouter();
  const [selectedEarningsTicker, setSelectedEarningsTicker] = useState<string | null>(null);

  const handleSelectStock = (ticker: string) => {
    setSelectedEarningsTicker(ticker);
  };

  const handleNavigateToStock = (ticker: string) => {
    router.push(`/stock/${ticker}`);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Hero Section */}
        <section className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-gray-900 via-gray-700 to-gray-900 bg-clip-text text-transparent mb-4">
            Welcome to Fundamint
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Your AI-powered assistant for deep fundamental stock analysis.
            Search for a stock to begin.
          </p>
          <div className="flex justify-center mb-4">
            <StockSearchInput />
          </div>
          <p className="text-sm text-gray-500">
            Tip: Use the dropdown in the navigation bar to switch between Yahoo Finance and Financial Modeling Prep data.
          </p>
        </section>

        {/* Main Content */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Earnings Calendar */}
          <div className={selectedEarningsTicker ? 'lg:col-span-1' : 'lg:col-span-2'}>
            <EarningsCalendar
              onSelectStock={handleSelectStock}
              defaultView="weekly"
            />
          </div>

          {/* Earnings Details Card - Shows when a stock is selected */}
          {selectedEarningsTicker && (
            <div className="lg:col-span-1">
              <EarningsDetails
                ticker={selectedEarningsTicker}
                onClose={() => setSelectedEarningsTicker(null)}
                onNavigateToStock={handleNavigateToStock}
              />
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
