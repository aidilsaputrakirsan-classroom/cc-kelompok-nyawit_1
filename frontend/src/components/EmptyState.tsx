import { Link } from "react-router-dom";

interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  actionLabel?: string;
  actionLink?: string;
  onAction?: () => void;
}

export default function EmptyState({
  icon = "📋",
  title,
  description,
  actionLabel,
  actionLink,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      {actionLabel && (
        <>
          {actionLink ? (
            <Link to={actionLink} className="btn btn-primary">
              {actionLabel}
            </Link>
          ) : onAction ? (
            <button className="btn btn-outline" onClick={onAction}>
              {actionLabel}
            </button>
          ) : null}
        </>
      )}
    </div>
  );
}
