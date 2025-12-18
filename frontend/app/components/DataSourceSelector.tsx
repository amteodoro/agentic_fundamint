"use client";

import { useChatContext, DataSourceType } from '@/app/context/ChatContext';

/**
 * Dropdown selector for choosing the data source (Yahoo Finance or Financial Modeling Prep)
 */
export function DataSourceSelector() {
    const { dataSource, setDataSource } = useChatContext();

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setDataSource(e.target.value as DataSourceType);
        // Trigger a page refresh to reload data with new source
        window.location.reload();
    };

    return (
        <div className="flex items-center gap-2">
            <label htmlFor="data-source" className="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                Data Source:
            </label>
            <select
                id="data-source"
                value={dataSource}
                onChange={handleChange}
                className="block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 py-1.5 px-3 text-sm text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
                <option value="yfinance">Yahoo Finance (with fallbacks)</option>
                <option value="fmp">Financial Modeling Prep</option>
            </select>
        </div>
    );
}
