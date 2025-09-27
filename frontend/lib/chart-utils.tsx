import { TooltipProps } from 'recharts';

export const COLORS = [
  '#3b82f6', // blue-500
  '#22c55e', // green-500
  '#f97316', // orange-500
  '#ef4444', // red-500
  '#8b5cf6', // violet-500
  '#ec4899', // pink-500
  '#f59e0b', // amber-500
  '#10b981', // emerald-500
];

export const formatNumber = (num: number | undefined | null, precision: number = 2): string => {
  if (num === undefined || num === null) return 'N/A';
  if (num === 0) return '0';

  const absNum = Math.abs(num);
  
  if (absNum >= 1e12) {
    return `${(num / 1e12).toFixed(precision)}T`;
  }
  if (absNum >= 1e9) {
    return `${(num / 1e9).toFixed(precision)}B`;
  }
  if (absNum >= 1e6) {
    return `${(num / 1e6).toFixed(precision)}M`;
  }
  if (absNum >= 1e3) {
    return `${(num / 1e3).toFixed(precision)}K`;
  }
  return num.toFixed(precision);
};

export const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-2 bg-background border rounded-md shadow-md">
        <p className="font-bold">{label}</p>
        {payload.map((pld, index) => {
          const value = pld.value;
          let formattedValue;
          if (pld.name && pld.name.includes('Margin')) {
            formattedValue = `${formatNumber(value, 2)}%`;
          } else {
            formattedValue = formatNumber(value);
          }
          return (
            <p key={pld.dataKey} style={{ color: COLORS[index % COLORS.length] }}>
              {`${pld.name}: ${formattedValue}`}
            </p>
          )
        })}
      </div>
    );
  }

  return null;
};