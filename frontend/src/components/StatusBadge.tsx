import type { PRStatus } from "../types";

const STATUS_LABELS: Record<PRStatus, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  UNDER_REVIEW: "Under Review",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  PO_ISSUED: "PO Issued",
  DOC_SUBMITTED: "Doc Pending",
  VERIFIED: "Verified",
  CLOSED: "Closed",
};

const STATUS_COLORS: Record<PRStatus, string> = {
  DRAFT: "#6b7280",
  SUBMITTED: "#2563eb",
  UNDER_REVIEW: "#d97706",
  APPROVED: "#16a34a",
  REJECTED: "#dc2626",
  PO_ISSUED: "#7c3aed",
  DOC_SUBMITTED: "#ea580c",
  VERIFIED: "#059669",
  CLOSED: "#4b5563",
};

export default function StatusBadge({ status }: { status: PRStatus }) {
  return (
    <span
      className="status-badge"
      style={{
        backgroundColor: STATUS_COLORS[status] + "18",
        color: STATUS_COLORS[status],
        border: `1px solid ${STATUS_COLORS[status]}40`,
      }}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
