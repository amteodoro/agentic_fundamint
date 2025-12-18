"use client";

import Link from "next/link";
import { useAuth } from "@/app/context/AuthContext";
import { Button } from "@/components/ui/button";
import { useChatContext, DataSourceType, CurrencyType } from "@/app/context/ChatContext";

export function MainNav() {
  const { user, logout, isAuthenticated } = useAuth();
  const { dataSource, setDataSource, currency, setCurrency } = useChatContext();

  return (
    <nav className="border-b border-gray-200 bg-white shadow-sm p-4">
      <div className="container mx-auto flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold text-emerald-600 hover:text-emerald-700 transition-colors">
          Fundamint
        </Link>
        <div className="flex items-center gap-4">
          {/* Currency Selector */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-500">Currency:</span>
            <select
              id="nav-currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value as CurrencyType)}
              className="block rounded-md border border-gray-300 bg-white py-1 px-2 text-xs text-gray-700 shadow-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 cursor-pointer"
              title="Select display currency"
            >
              <option value="USD">$ USD</option>
              <option value="EUR">€ EUR</option>
            </select>
          </div>

          {/* Data Source Selector */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-500">Source:</span>
            <select
              id="nav-data-source"
              value={dataSource}
              onChange={(e) => setDataSource(e.target.value as DataSourceType)}
              className="block rounded-md border border-gray-300 bg-white py-1 px-2 text-xs text-gray-700 shadow-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 cursor-pointer"
              title="Select data source"
            >
              <option value="yfinance">Yahoo Finance</option>
              <option value="fmp">FMP API</option>
            </select>
          </div>

          <Link href="/" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">
            Search
          </Link>
          {isAuthenticated && (
            <Link href="/portfolios" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">
              Portfolios
            </Link>
          )}
          {user ? (
            <>
              <span className="text-sm text-gray-500">
                {user.name || user.email?.split('@')[0]} {user.is_guest && "(Guest)"}
              </span>
              <Button
                variant="ghost"
                onClick={logout}
                className="text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                Logout
              </Button>
            </>
          ) : (
            <Link href="/login">
              <Button variant="outline" className="border-emerald-500 text-emerald-600 hover:bg-emerald-50">
                Login
              </Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
