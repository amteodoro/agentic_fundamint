"use client";

interface DataSourceBadgeProps {
    source: string | null | undefined;
    className?: string;
}

/**
 * Displays a small badge indicating the data source (yfinance, Financial Modeling Prep, etc.)
 */
export function DataSourceBadge({ source, className = "" }: DataSourceBadgeProps) {
    if (!source || source === "unknown") {
        return null;
    }

    // Format the source name for display
    const formatSourceName = (src: string): string => {
        const sourceMap: Record<string, string> = {
            "yfinance": "Yahoo Finance",
            "financial_modeling_prep": "Financial Modeling Prep",
        };

        // Handle mixed sources
        if (src.startsWith("mixed")) {
            const sources = src.replace("mixed (", "").replace(")", "").split(", ");
            const formattedSources = sources.map(s => sourceMap[s] || s);
            return `Mixed: ${formattedSources.join(" + ")}`;
        }

        return sourceMap[src] || src;
    };

    // Get badge color based on source
    const getBadgeStyle = (src: string): string => {
        if (src.includes("financial_modeling_prep")) {
            return "bg-purple-100 text-purple-800 border-purple-200";
        }
        if (src === "yfinance") {
            return "bg-blue-100 text-blue-800 border-blue-200";
        }
        if (src.startsWith("mixed")) {
            return "bg-amber-100 text-amber-800 border-amber-200";
        }
        return "bg-gray-100 text-gray-800 border-gray-200";
    };

    return (
        <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getBadgeStyle(source)} ${className}`}
            title={`Data provided by: ${formatSourceName(source)}`}
        >
            <svg
                className="w-3 h-3 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
            >
                <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
                />
            </svg>
            {formatSourceName(source)}
        </span>
    );
}
