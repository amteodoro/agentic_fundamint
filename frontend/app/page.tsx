"use client";

import { StockSearchInput } from "@/app/components/StockSearchInput";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50">
      <div className="text-center w-full max-w-2xl">
        <h1 className="text-5xl md:text-6xl font-bold text-gray-800 mb-4">
          Welcome to Fundamint
        </h1>
        <p className="text-lg md:text-xl text-gray-600 mb-8">
          Your AI-powered assistant for deep fundamental stock analysis.
          Search for a stock to begin.
        </p>
        <div className="flex justify-center">
          <StockSearchInput />
        </div>
        <p className="text-sm text-gray-500 mt-4">
          Tip: Use the dropdown in the navigation bar to switch between Yahoo Finance and Financial Modeling Prep data.
        </p>
      </div>
    </main>
  );
}
