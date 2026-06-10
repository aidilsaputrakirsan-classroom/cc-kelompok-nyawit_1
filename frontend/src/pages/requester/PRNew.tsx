import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../../services/api";
import { useToast } from "../../contexts/ToastContext";
import { useProcurement } from "../../contexts/ProcurementContext";
import type { PRLineItemInput, PRCreatePayload, APIResponse, PurchaseRequisition } from "../../types";

const EMPTY_ITEM: PRLineItemInput = {
  item_name: "",
  quantity: 1,
  unit_of_measure: "pcs",
  estimated_unit_price: 0,
};

export default function RequesterPRNew() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { invalidate } = useProcurement();

  const [title, setTitle] = useState("");
  const [justification, setJustification] = useState("");
  const [items, setItems] = useState<PRLineItemInput[]>([{ ...EMPTY_ITEM }]);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  // ── Line item helpers ──────────────────────────────────────────
  const updateItem = (index: number, field: keyof PRLineItemInput, value: string | number) => {
    setItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, [field]: value } : item))
    );
  };

  const addItem = () => {
    setItems((prev) => [...prev, { ...EMPTY_ITEM }]);
  };

  const removeItem = (index: number) => {
    if (items.length <= 1) return; // minimal 1 item
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const getSubtotal = (item: PRLineItemInput) =>
    Math.round(item.quantity * item.estimated_unit_price * 100) / 100;

  const getTotal = () =>
    items.reduce((sum, item) => sum + getSubtotal(item), 0);

  // ── Validation ─────────────────────────────────────────────────
  const validate = (): string[] => {
    const errs: string[] = [];
    if (!title.trim()) errs.push("Judul PR wajib diisi.");
    if (!justification.trim()) errs.push("Justifikasi wajib diisi.");
    if (items.length === 0) errs.push("Minimal 1 line item diperlukan.");

    items.forEach((item, i) => {
      const n = i + 1;
      if (!item.item_name.trim()) errs.push(`Item #${n}: Nama item wajib diisi.`);
      if (item.quantity <= 0) errs.push(`Item #${n}: Quantity harus > 0.`);
      if (!item.unit_of_measure.trim()) errs.push(`Item #${n}: Satuan wajib diisi.`);
      if (item.estimated_unit_price <= 0) errs.push(`Item #${n}: Harga estimasi harus > 0.`);
    });

    if (errs.length === 0 && getTotal() <= 0) {
      errs.push("Total harus lebih dari 0.");
    }

    return errs;
  };

  // ── Submit ─────────────────────────────────────────────────────
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors([]);
    setSubmitting(true);

    const payload: PRCreatePayload = {
      title: title.trim(),
      justification: justification.trim(),
      items: items.map((item) => ({
        item_name: item.item_name.trim(),
        quantity: Number(item.quantity),
        unit_of_measure: item.unit_of_measure.trim(),
        estimated_unit_price: Number(item.estimated_unit_price),
      })),
    };

    try {
      await api.post<APIResponse<PurchaseRequisition>>("/requisitions/", payload);
      showToast("success", "Purchase Requisition berhasil dibuat!");
      invalidate();
      navigate("/requester/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string; message?: string } } })
          ?.response?.data?.detail ??
        (err as { response?: { data?: { message?: string } } })?.response?.data
          ?.message ??
        "Gagal membuat Purchase Requisition.";
      showToast("error", msg);
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(val);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Buat Purchase Requisition Baru</h2>
        <Link to="/requester/dashboard" className="btn btn-outline">
          &larr; Kembali
        </Link>
      </div>

      {errors.length > 0 && (
        <div className="alert alert-error">
          <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
            {errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit} className="pr-form">
        {/* Title & Justification */}
        <div className="form-card">
          <div className="form-group">
            <label htmlFor="title">Judul PR *</label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Contoh: Pengadaan Laptop untuk Tim Engineering"
              maxLength={255}
            />
          </div>
          <div className="form-group">
            <label htmlFor="justification">Justifikasi / Alasan *</label>
            <textarea
              id="justification"
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              placeholder="Jelaskan alasan pengadaan ini diperlukan..."
              rows={3}
              maxLength={2000}
            />
          </div>
        </div>

        {/* Line Items */}
        <div className="form-card">
          <div className="form-card-header">
            <h3>List Items</h3>
            <button type="button" className="btn btn-sm btn-primary" onClick={addItem}>
              + Tambah Item
            </button>
          </div>

          <div className="line-items-table-wrapper">
            <table className="table line-items-table">
              <thead>
                <tr>
                  <th style={{ width: "40px" }}>No</th>
                  <th>Nama Item</th>
                  <th style={{ width: "90px" }}>Qty</th>
                  <th style={{ width: "100px" }}>Satuan</th>
                  <th style={{ width: "160px" }}>Harga Estimasi</th>
                  <th style={{ width: "140px" }} className="text-right">Subtotal</th>
                  <th style={{ width: "50px" }}></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => (
                  <tr key={index}>
                    <td className="text-muted">{index + 1}</td>
                    <td>
                      <input
                        type="text"
                        value={item.item_name}
                        onChange={(e) => updateItem(index, "item_name", e.target.value)}
                        placeholder="Nama item"
                        className="input-inline"
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min={1}
                        value={item.quantity}
                        onChange={(e) => updateItem(index, "quantity", parseInt(e.target.value) || 0)}
                        className="input-inline input-number"
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={item.unit_of_measure}
                        onChange={(e) => updateItem(index, "unit_of_measure", e.target.value)}
                        placeholder="pcs"
                        className="input-inline"
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min={0}
                        step="any"
                        value={item.estimated_unit_price}
                        onChange={(e) =>
                          updateItem(index, "estimated_unit_price", parseFloat(e.target.value) || 0)
                        }
                        className="input-inline input-number"
                      />
                    </td>
                    <td className="text-right font-mono">
                      {formatCurrency(getSubtotal(item))}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-sm btn-icon btn-danger-ghost"
                        onClick={() => removeItem(index)}
                        disabled={items.length <= 1}
                        title="Hapus item"
                      >
                        &times;
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={5} className="text-right" style={{ fontWeight: 700 }}>
                    Total Estimasi
                  </td>
                  <td className="text-right font-mono" style={{ fontWeight: 700 }}>
                    {formatCurrency(getTotal())}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* Submit */}
        <div className="form-actions">
          <Link to="/requester/dashboard" className="btn btn-outline">
            Batal
          </Link>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? "Mengirim..." : "Submit Requisition"}
          </button>
        </div>
      </form>
    </div>
  );
}
