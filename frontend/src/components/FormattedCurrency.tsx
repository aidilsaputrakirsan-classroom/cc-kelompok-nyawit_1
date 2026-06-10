interface FormattedCurrencyProps {
  amount: number;
  currency?: string;
  locale?: string;
  className?: string;
}

export default function FormattedCurrency({
  amount,
  currency = "IDR",
  locale = "id-ID",
  className = "",
}: FormattedCurrencyProps) {
  const formatted = new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
  }).format(amount);

  return <span className={`font-mono ${className}`}>{formatted}</span>;
}
