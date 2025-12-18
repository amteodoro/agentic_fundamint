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

// Currency-aware formatting function
export const formatNumberWithCurrency = (
  num: number | undefined | null,
  precision: number = 2,
  currencySymbol: string = '$',
  exchangeRate: number = 1,
  isCurrencyValue: boolean = true
): string => {
  if (num === undefined || num === null) return 'N/A';
  if (num === 0) return isCurrencyValue ? `${currencySymbol}0` : '0';

  // Apply exchange rate conversion if it's a currency value
  const convertedNum = isCurrencyValue ? num * exchangeRate : num;
  const absNum = Math.abs(convertedNum);
  const prefix = isCurrencyValue ? currencySymbol : '';

  if (absNum >= 1e12) {
    return `${prefix}${(convertedNum / 1e12).toFixed(precision)}T`;
  }
  if (absNum >= 1e9) {
    return `${prefix}${(convertedNum / 1e9).toFixed(precision)}B`;
  }
  if (absNum >= 1e6) {
    return `${prefix}${(convertedNum / 1e6).toFixed(precision)}M`;
  }
  if (absNum >= 1e3) {
    return `${prefix}${(convertedNum / 1e3).toFixed(precision)}K`;
  }
  return `${prefix}${convertedNum.toFixed(precision)}`;
};

// Create a currency-aware formatter for use in chart tick formatters
export const createCurrencyFormatter = (
  currencySymbol: string,
  exchangeRate: number,
  precision: number = 0,
  isCurrencyValue: boolean = true
) => {
  return (tick: number): string => formatNumberWithCurrency(tick, precision, currencySymbol, exchangeRate, isCurrencyValue);
};

// Currency-aware tooltip component creator
export const createCurrencyTooltip = (currencySymbol: string, exchangeRate: number) => {
  return function CurrencyTooltip({ active, payload, label }: TooltipProps<number, string>) {
    if (active && payload && payload.length) {
      return (
        <div className="p-2 bg-background border rounded-md shadow-md">
          <p className="font-bold">{label}</p>
          {payload.map((pld, index) => {
            const value = pld.value;
            let formattedValue;
            if (pld.name && pld.name.includes('Margin')) {
              formattedValue = `${formatNumber(value, 2)}%`;
            } else if (pld.name && (pld.name.includes('Shares') || pld.name.includes('EPS') || pld.name.includes('P/E') || pld.name.includes('PSR') || pld.name.includes('Ratio'))) {
              // Non-currency values
              formattedValue = formatNumber(value);
            } else {
              // Currency values
              formattedValue = formatNumberWithCurrency(value, 2, currencySymbol, exchangeRate, true);
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