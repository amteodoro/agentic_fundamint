"use client";

import { createContext, useState, useContext, ReactNode, useEffect, useCallback } from 'react';

export type DataSourceType = 'yfinance' | 'fmp';
export type CurrencyType = 'USD' | 'EUR';

interface ChatContextType {
  ticker: string | null;
  setTicker: (ticker: string | null) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  dataSource: DataSourceType;
  setDataSource: (source: DataSourceType) => void;
  currency: CurrencyType;
  setCurrency: (currency: CurrencyType) => void;
  exchangeRate: number; // USD to EUR rate
  convertValue: (value: number | null | undefined, fromCurrency?: string) => number | null;
  formatCurrency: (value: number | null | undefined, fromCurrency?: string) => string;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Currency symbols
const CURRENCY_SYMBOLS: Record<CurrencyType, string> = {
  USD: '$',
  EUR: '€'
};

export const ChatContextProvider = ({ children }: { children: ReactNode }) => {
  const [ticker, setTicker] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');
  const [dataSource, setDataSource] = useState<DataSourceType>('yfinance');
  const [currency, setCurrency] = useState<CurrencyType>('USD');
  const [exchangeRate, setExchangeRate] = useState<number>(0.92); // Default USD to EUR rate

  // Fetch exchange rate when currency changes
  useEffect(() => {
    const fetchExchangeRate = async () => {
      try {
        // Fetch USD to EUR exchange rate from the backend
        const response = await fetch('http://localhost:8100/api/exchange-rate?from=USD&to=EUR');
        if (response.ok) {
          const data = await response.json();
          if (data.rate) {
            setExchangeRate(data.rate);
          }
        }
      } catch (error) {
        console.error('Failed to fetch exchange rate:', error);
        // Keep default rate on error
      }
    };

    fetchExchangeRate();
    // Refresh exchange rate every 5 minutes
    const interval = setInterval(fetchExchangeRate, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Convert a USD value to the selected currency
  const convertValue = useCallback((value: number | null | undefined, fromCurrency: string = 'USD'): number | null => {
    if (value === null || value === undefined || isNaN(value)) {
      return null;
    }

    // If the source currency matches the selected currency, no conversion needed
    if (fromCurrency === currency) {
      return value;
    }

    // Convert USD to EUR
    if (fromCurrency === 'USD' && currency === 'EUR') {
      return value * exchangeRate;
    }

    // Convert EUR to USD
    if (fromCurrency === 'EUR' && currency === 'USD') {
      return value / exchangeRate;
    }

    return value;
  }, [currency, exchangeRate]);

  // Format a value as currency
  const formatCurrency = useCallback((value: number | null | undefined, fromCurrency: string = 'USD'): string => {
    const convertedValue = convertValue(value, fromCurrency);

    if (convertedValue === null) {
      return 'N/A';
    }

    const symbol = CURRENCY_SYMBOLS[currency];

    // Format based on magnitude
    const absValue = Math.abs(convertedValue);

    if (absValue >= 1e12) {
      return `${symbol}${(convertedValue / 1e12).toFixed(2)}T`;
    } else if (absValue >= 1e9) {
      return `${symbol}${(convertedValue / 1e9).toFixed(2)}B`;
    } else if (absValue >= 1e6) {
      return `${symbol}${(convertedValue / 1e6).toFixed(2)}M`;
    } else if (absValue >= 1e3) {
      return `${symbol}${(convertedValue / 1e3).toFixed(2)}K`;
    } else if (absValue >= 1) {
      return `${symbol}${convertedValue.toFixed(2)}`;
    } else {
      return `${symbol}${convertedValue.toFixed(4)}`;
    }
  }, [convertValue, currency]);

  return (
    <ChatContext.Provider value={{
      ticker, setTicker,
      activeTab, setActiveTab,
      dataSource, setDataSource,
      currency, setCurrency,
      exchangeRate,
      convertValue,
      formatCurrency
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatContextProvider');
  }
  return context;
};

// Export currency symbol helper
export const getCurrencySymbol = (currency: CurrencyType): string => CURRENCY_SYMBOLS[currency];
