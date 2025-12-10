import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface ConfidenceBadgeProps {
    score: number;
    source?: string;
}

export function ConfidenceBadge({ score, source }: ConfidenceBadgeProps) {
    let colorClass = "bg-gray-500";
    let text = "Low Confidence";

    if (score >= 0.8) {
        colorClass = "bg-green-500";
        text = "High Confidence";
    } else if (score >= 0.5) {
        colorClass = "bg-yellow-500";
        text = "Medium Confidence";
    }

    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger>
                    <Badge className={`${colorClass} hover:${colorClass} text-white text-xs ml-2`}>
                        {Math.round(score * 100)}%
                    </Badge>
                </TooltipTrigger>
                <TooltipContent>
                    <p>{text}</p>
                    {source && <p className="text-xs text-gray-400">Source: {source}</p>}
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}
