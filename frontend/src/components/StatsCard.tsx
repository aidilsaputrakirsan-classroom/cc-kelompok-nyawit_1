import type { ReactNode } from "react";

interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  change?: string;
  variant?: "default" | "success" | "warning" | "danger";
}

export default function StatsCard({
  label,
  value,
  icon,
  change,
  variant = "default",
}: StatsCardProps) {
  return (
    <div className={`stat-card ${variant}`}>
      <div className="stat-card-header">
        <span className="stat-card-label">{label}</span>
        {icon && <div className="stat-card-icon">{icon}</div>}
      </div>
      <div className="stat-card-value">{value}</div>
      {change && <div className="stat-card-change">{change}</div>}
    </div>
  );
}
