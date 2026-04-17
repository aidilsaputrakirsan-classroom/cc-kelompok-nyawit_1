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

export default function StatusBadge({ status }: { status: PRStatus }) {
  return (
    <span className="status-badge" data-status={status}>
      {STATUS_LABELS[status]}
    </span>
  );
}
