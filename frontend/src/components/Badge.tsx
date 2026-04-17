interface BadgeProps {
  label: string;
  variant?: "default" | "primary" | "success" | "warning" | "danger" | "info";
  size?: "sm" | "md" | "lg";
  className?: string;
}

export default function Badge({
  label,
  variant = "default",
  size = "md",
  className = "",
}: BadgeProps) {
  return (
    <span className={`badge badge-${variant} badge-${size} ${className}`}>
      {label}
    </span>
  );
}
