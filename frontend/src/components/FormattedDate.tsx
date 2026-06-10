interface FormattedDateProps {
  date: string | Date;
  format?: "short" | "medium" | "long";
  locale?: string;
  className?: string;
}

export default function FormattedDate({
  date,
  format = "medium",
  locale = "id-ID",
  className = "",
}: FormattedDateProps) {
  const dateObj = typeof date === "string" ? new Date(date) : date;

  const formatOptions: Record<string, Intl.DateTimeFormatOptions> = {
    short: {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
    },
    medium: {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
    long: {
      weekday: "long",
      day: "2-digit",
      month: "long",
      year: "numeric",
    },
  };

  const formatted = dateObj.toLocaleDateString(locale, formatOptions[format]);

  return <span className={className}>{formatted}</span>;
}
