export type UserRole = "admin" | "requester";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface PRLineItem {
  id: number;
  pr_id: number;
  item_name: string;
  quantity: number;
  unit_of_measure: string;
  estimated_unit_price: number;
  subtotal: number;
}

/** Line item shape for creating a PR (no id/pr_id/subtotal) */
export interface PRLineItemInput {
  item_name: string;
  quantity: number;
  unit_of_measure: string;
  estimated_unit_price: number;
}

export type PRStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "PO_ISSUED"
  | "DOC_SUBMITTED"
  | "VERIFIED"
  | "CLOSED";

export interface PurchaseRequisition {
  id: number;
  pr_number: string;
  title: string;
  justification: string | null;
  status: PRStatus;
  total_amount: number;
  created_at: string;
  updated_at: string;
  approval_note: string | null;
  requester_id: number;
  line_items?: PRLineItem[];
}

export interface PurchaseOrder {
  id: number;
  po_number: string;
  pr_id: number;
  issued_by: number;
  issued_at: string;
  allocated_budget: number;
}

export interface GRNDocument {
  id: number;
  po_id: number;
  requester_id: number;
  receipt_url: string | null;
  commercial_invoice_url: string | null;
  goods_photo_url: string | null;
  submitted_at: string;
  verification_note: string | null;
}

/** Matches backend PaginationMeta (field: pagination, total_items) */
export interface PaginationMeta {
  page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
}

export interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

/** Backend returns { pagination: ... } not { meta: ... } */
export interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  pagination: PaginationMeta;
}

/** Payload for creating a PR */
export interface PRCreatePayload {
  title: string;
  justification: string;
  items: PRLineItemInput[];
}

/** Payload for admin review (approve/reject) */
export interface PRReviewPayload {
  status: "APPROVED" | "REJECTED";
  approval_note: string;
}

/** Payload for GRN verification */
export interface GRNVerifyPayload {
  status: "VERIFIED" | "CLOSED";
  verification_note: string;
}
