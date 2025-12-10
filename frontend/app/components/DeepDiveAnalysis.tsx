'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

interface DeepDiveResponse {
    ticker: string;
    questions: string[];
    answers: { [key: string]: string };
}

export function DeepDiveAnalysis({ ticker }: { ticker: string }) {
    const [data, setData] = useState<DeepDiveResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (ticker) {
            const fetchAnalysis = async () => {
                try {
                    setLoading(true);
                    const response = await fetch(`http://localhost:8100/api/analysis/${ticker}/deep-dive`);
                    if (!response.ok) {
                        throw new Error('Failed to fetch Deep Dive analysis.');
                    }
                    const result = await response.json();
                    setData(result);
                } catch (err: any) {
                    setError(err.message);
                } finally {
                    setLoading(false);
                }
            };
            fetchAnalysis();
        }
    }, [ticker]);

    if (loading) return (
        <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-500">Generating Deep Dive Analysis... This may take a minute.</p>
        </div>
    );

    if (error) return <p className="text-red-500">{error}</p>;
    if (!data) return <p>No Deep Dive analysis available.</p>;

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>Deep Dive Investment Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                    <Accordion type="single" collapsible className="w-full">
                        {data.questions.map((question, index) => (
                            <AccordionItem key={index} value={`item-${index}`}>
                                <AccordionTrigger className="text-left font-medium text-lg">
                                    {index + 1}. {question}
                                </AccordionTrigger>
                                <AccordionContent className="text-gray-700 whitespace-pre-line leading-relaxed">
                                    {data.answers[String(index + 1)] || data.answers[question] || "No answer available."}
                                </AccordionContent>
                            </AccordionItem>
                        ))}
                    </Accordion>
                </CardContent>
            </Card>
        </div>
    );
}
