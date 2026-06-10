import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import api from "../services/api";
import type {
  PurchaseRequisition,
  PurchaseOrder,
  PaginatedResponse,
  APIResponse,
} from "../types";

interface ProcurementContextType {
  /** Cached PR list (requester's own) */
  prs: PurchaseRequisition[];
  prsLoading: boolean;
  /** Cached admin PR list */
  adminPrs: PurchaseRequisition[];
  adminPrsLoading: boolean;
  /** Cached PO list */
  pos: PurchaseOrder[];
  posLoading: boolean;
  /** Fetch requester's PRs */
  fetchMyPRs: (statusFilter?: string) => Promise<void>;
  /** Fetch all PRs (admin) */
  fetchAdminPRs: (statusFilter?: string) => Promise<void>;
  /** Fetch all POs (admin) */
  fetchPOs: () => Promise<void>;
  /** Get a single PR detail */
  fetchPRDetail: (id: number) => Promise<PurchaseRequisition>;
  /** Get a single PR detail (admin) */
  fetchAdminPRDetail: (id: number) => Promise<PurchaseRequisition>;
  /** Invalidate caches (after mutations) */
  invalidate: () => void;
}

const ProcurementContext = createContext<ProcurementContextType | null>(null);

export function ProcurementProvider({ children }: { children: ReactNode }) {
  const [prs, setPrs] = useState<PurchaseRequisition[]>([]);
  const [prsLoading, setPrsLoading] = useState(false);
  const [adminPrs, setAdminPrs] = useState<PurchaseRequisition[]>([]);
  const [adminPrsLoading, setAdminPrsLoading] = useState(false);
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [posLoading, setPosLoading] = useState(false);

  const fetchMyPRs = useCallback(async (statusFilter?: string) => {
    setPrsLoading(true);
    try {
      const params: Record<string, string | number> = {
        page: 1,
        per_page: 50,
      };
      if (statusFilter) params.status = statusFilter;
      const res = await api.get<PaginatedResponse<PurchaseRequisition>>(
        "/requisitions/",
        { params }
      );
      setPrs(res.data.data);
    } catch {
      // Error handled by caller
      throw new Error("Gagal memuat data requisition.");
    } finally {
      setPrsLoading(false);
    }
  }, []);

  const fetchAdminPRs = useCallback(async (statusFilter?: string) => {
    setAdminPrsLoading(true);
    try {
      const params: Record<string, string | number> = {
        page: 1,
        per_page: 50,
      };
      if (statusFilter) params.status = statusFilter;
      const res = await api.get<PaginatedResponse<PurchaseRequisition>>(
        "/requisitions/admin/",
        { params }
      );
      setAdminPrs(res.data.data);
    } catch {
      throw new Error("Gagal memuat data requisition.");
    } finally {
      setAdminPrsLoading(false);
    }
  }, []);

  const fetchPOs = useCallback(async () => {
    setPosLoading(true);
    try {
      const res = await api.get<PaginatedResponse<PurchaseOrder>>(
        "/purchase-orders/",
        { params: { page: 1, per_page: 50 } }
      );
      setPos(res.data.data);
    } catch {
      throw new Error("Gagal memuat data purchase order.");
    } finally {
      setPosLoading(false);
    }
  }, []);

  const fetchPRDetail = useCallback(async (id: number) => {
    const res = await api.get<APIResponse<PurchaseRequisition>>(
      `/requisitions/${id}`
    );
    return res.data.data;
  }, []);

  const fetchAdminPRDetail = useCallback(async (id: number) => {
    // Admin uses the same admin list endpoint or detail endpoint
    // The backend admin router doesn't have a detail endpoint, so we fetch from the list
    // and find by id, or use the requester detail endpoint with admin privileges
    // Actually, let's fetch from admin list and find, or call the general detail
    // Looking at the backend: admin only has list + review. No admin detail endpoint.
    // We'll fetch from the admin list with all items and find by id
    const res = await api.get<PaginatedResponse<PurchaseRequisition>>(
      "/requisitions/admin/",
      { params: { page: 1, per_page: 100 } }
    );
    const pr = res.data.data.find((p) => p.id === id);
    if (!pr) throw new Error("PR tidak ditemukan");
    return pr;
  }, []);

  const invalidate = useCallback(() => {
    setPrs([]);
    setAdminPrs([]);
    setPos([]);
  }, []);

  return (
    <ProcurementContext.Provider
      value={{
        prs,
        prsLoading,
        adminPrs,
        adminPrsLoading,
        pos,
        posLoading,
        fetchMyPRs,
        fetchAdminPRs,
        fetchPOs,
        fetchPRDetail,
        fetchAdminPRDetail,
        invalidate,
      }}
    >
      {children}
    </ProcurementContext.Provider>
  );
}

export function useProcurement(): ProcurementContextType {
  const ctx = useContext(ProcurementContext);
  if (!ctx) {
    throw new Error(
      "useProcurement must be used within ProcurementProvider"
    );
  }
  return ctx;
}
