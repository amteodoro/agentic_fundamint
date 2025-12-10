'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

// Types based on the Python script's CRITERIA_DATA and analysis output
interface SummaryMetric {
  criteria_name: string;
  interpretation: string;
  value: string | number | null;
  assessment: string;
  color: string;
}

const transformDataForSummaryTable = (hgAnalysisData: any, criteria: any[]): SummaryMetric[] => {
  if (!hgAnalysisData || !criteria) return [];

  const getMetricAssessment = (metricName: string, value: any, hgData: any) => {
    const good_color = "#D4EDDA";
    const neutral_color = "#FFF3CD";
    const warning_color = "#F8D7DA";
    const default_color = "#FFFFFF";

    if (value === null || value === undefined || (typeof value === 'number' && isNaN(value))) {
      return { assessment: "N/A", color: default_color };
    }

    switch (metricName) {
      case "Sales Growth":
        if (value > 0.15) return { assessment: "Good", color: good_color };
        if (value >= 0.05) return { assessment: "Neutral", color: neutral_color };
        return { assessment: "Warning", color: warning_color };
      case "Net Margin":
        if (value > 0.10) return { assessment: "Good", color: good_color };
        if (value >= 0.05) return { assessment: "Neutral", color: neutral_color };
        return { assessment: "Warning", color: warning_color };
      case "EV/EBITDA":
        if (value < 5) return { assessment: "Good", color: good_color };
        if (value <= 20) return { assessment: "Neutral", color: neutral_color };
        return { assessment: "Warning", color: warning_color };
      case "Net Debt / EBITDA":
        if (hgData.net_debt < 0) return { assessment: "Good (Net Cash)", color: good_color };
        if (value < 3) return { assessment: "Good", color: good_color };
        return { assessment: "Warning", color: warning_color };
      case "ROE":
        if (value > 0.20) return { assessment: "Good", color: good_color };
        if (value >= 0.15) return { assessment: "Neutral", color: neutral_color };
        return { assessment: "Warning", color: warning_color };
      case "PER":
        if (value > 0 && value < 10) return { assessment: "Good", color: good_color };
        if (value <= 20) return { assessment: "Neutral", color: neutral_color };
        return { assessment: "Warning", color: warning_color };
      case "PSR":
        if (value < 1) return { assessment: "Good", color: good_color };
        if (value <= 10) return { assessment: "Neutral", color: neutral_color };
        return { assessment: "Warning", color: warning_color };
      case "Insider Ownership":
        if (value > 0.10) return { assessment: "Good (Significant)", color: good_color };
        return { assessment: "Warning (Fragmented/Low)", color: warning_color };
      case "Dividends":
        return value ? { assessment: "Good", color: good_color } : { assessment: "Warning", color: warning_color };
      default:
        return { assessment: "N/A", color: default_color };
    }
  };

  const rawMetrics: { [key: string]: any } = {
    "Sales Growth": hgAnalysisData.final_metrics?.high_growth?.sales_growth?.value ?? hgAnalysisData.sales_cagr_hg,
    "Net Margin": hgAnalysisData.final_metrics?.high_growth?.net_margin?.value ?? hgAnalysisData.current_net_margin,
    "EV/EBITDA": hgAnalysisData.final_metrics?.high_growth?.ev_ebitda?.value ?? hgAnalysisData.ev_to_ebitda,
    "Net Debt / EBITDA": hgAnalysisData.final_metrics?.high_growth?.debt_to_ebitda?.value ?? hgAnalysisData.net_debt_to_ebitda,
    "ROE": hgAnalysisData.final_metrics?.high_growth?.roe?.value ?? hgAnalysisData.latest_roe,
    "PER": hgAnalysisData.final_metrics?.high_growth?.per_ratio?.value ?? hgAnalysisData.current_per,
    "PSR": hgAnalysisData.final_metrics?.high_growth?.psr_ratio?.value ?? hgAnalysisData.current_psr,
    "Insider Ownership": hgAnalysisData.final_metrics?.high_growth?.insider_ownership?.value ?? hgAnalysisData.insider_ownership_hg,
    "Dividends": hgAnalysisData.final_metrics?.high_growth?.pays_dividends ?? hgAnalysisData.pays_dividends,
  };

  const metricMap: { [key: string]: string } = {
    "Sales Growth": "Sales Growth (Crescimento das Vendas)",
    "Net Margin": "Net Margin (Margem Líquida)",
    "EV/EBITDA": "EV/EBITDA",
    "Net Debt / EBITDA": "Net Debt / EBITDA",
    "ROE": "Operational Return on Equity (ROE)",
    "PER": "Price to Earnings Ratio (PER)",
    "PSR": "Price to Sales Ratio (PSR)",
    "Insider Ownership": "Shareholder Structure (Estrutura Acionista)",
    "Dividends": "Dividend Payments (Pagamento de Dividendos)"
  };

  const summaryMetrics: SummaryMetric[] = Object.keys(metricMap).map(simpleName => {
    const value = rawMetrics[simpleName];
    const { assessment, color } = getMetricAssessment(simpleName, value, hgAnalysisData);
    // Match using the simple name (e.g., "Sales Growth") instead of the Portuguese version
    const interpretation = criteria.find(c => c.criteria_name === simpleName)?.interpretation || "N/A";

    let formattedValue: string | number | null;
    if (value === null || value === undefined || (typeof value === 'number' && isNaN(value))) {
      formattedValue = "N/A";
    } else if (["Sales Growth", "Net Margin", "ROE", "Insider Ownership"].includes(simpleName)) {
      formattedValue = `${(value * 100).toFixed(2)}%`;
    } else if (simpleName === "Dividends") {
      formattedValue = value ? "Yes" : "No";
    } else {
      formattedValue = typeof value === 'number' ? value.toFixed(2) : value;
    }

    return {
      criteria_name: simpleName,
      interpretation,
      value: formattedValue,
      assessment,
      color,
    };
  });

  // Manually add qualitative metrics
  const buybackInterpretation = criteria.find(c => c.criteria_name === "Share Buybacks")?.interpretation || "N/A";
  summaryMetrics.push({
    criteria_name: "Share Buybacks",
    interpretation: buybackInterpretation,
    value: "Manual Check",
    assessment: "N/A",
    color: "#FFFFFF",
  });

  return summaryMetrics;
};

export function SummaryTable({ ticker }: { ticker: string }) {
  const [summaryData, setSummaryData] = useState<SummaryMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchSummaryData = async () => {
        try {
          setLoading(true);
          // This component needs the high-growth analysis data
          const response = await fetch(`http://localhost:8100/api/analysis/${ticker}/high-growth`);
          if (!response.ok) {
            throw new Error('Failed to fetch summary data.');
          }
          const hgAnalysisData = await response.json();

          // The criteria data is static, so we can define it here or fetch it if it becomes dynamic
          const criteriaResponse = await fetch('http://localhost:8100/api/criteria');
          const criteriaData = await criteriaResponse.json();

          const transformedData = transformDataForSummaryTable(hgAnalysisData, criteriaData);
          setSummaryData(transformedData);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchSummaryData();
    }
  }, [ticker]);

  if (loading) return <p>Loading summary table...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!summaryData.length) return <p>No summary data available.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Summary Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Metric</TableHead>
              <TableHead>Value</TableHead>
              <TableHead>Assessment</TableHead>
              <TableHead>Interpretation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {summaryData.map((metric) => (
              <TableRow key={metric.criteria_name}>
                <TableCell>{metric.criteria_name}</TableCell>
                <TableCell>{metric.value}</TableCell>
                <TableCell style={{ backgroundColor: metric.color }}>{metric.assessment}</TableCell>
                <TableCell>{metric.interpretation}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}