'use client';

import { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { useRouter } from 'next/navigation';
import { useDebounce } from 'use-debounce';

interface SearchResult {
  symbol: string;
  longName: string;
}

export function StockSearchInput() {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [debouncedSearchTerm] = useDebounce(searchTerm, 500); // Debounce for 500ms
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchSearchResults = async () => {
      if (debouncedSearchTerm.trim() === '') {
        setSearchResults([]);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8100/api/search?q=${debouncedSearchTerm}`);
        if (!response.ok) {
          throw new Error('Failed to fetch search results.');
        }
        const data = await response.json();
        setSearchResults(data.results);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSearchResults();
  }, [debouncedSearchTerm]);

  const handleSelectStock = (symbol: string) => {
    setSearchTerm(''); // Clear search term
    setSearchResults([]); // Clear search results
    router.push(`/stock/${symbol}`);
  };

  // Close search results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setSearchResults([]);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="relative w-full max-w-md" ref={searchRef}>
      <Input
        type="text"
        placeholder="Search for a stock (e.g., AAPL)"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-full"
      />
      {loading && <div className="absolute z-10 w-full bg-white shadow-md rounded-md mt-1 p-2">Loading...</div>}
      {error && <div className="absolute z-10 w-full bg-white shadow-md rounded-md mt-1 p-2 text-red-500">Error: {error}</div>}
      {searchResults.length > 0 && searchTerm.trim() !== '' && !loading && (
        <div className="absolute z-10 w-full bg-white shadow-md rounded-md mt-1 max-h-60 overflow-y-auto">
          {searchResults.map((result) => (
            <div
              key={result.symbol}
              className="p-2 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSelectStock(result.symbol)}
            >
              {result.symbol} - {result.longName}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
