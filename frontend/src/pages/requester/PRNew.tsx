import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../../services/api";
import { useToast } from "../../contexts/ToastContext";
import { useProcurement } from "../../contexts/ProcurementContext";
import type { PRLineItemInput, VendorQuoteInput } from "../../types";
import { formatRupiah as _formatRupiah, parseRupiah } from "../../utils/formatHelpers";

// Harus selaras dengan QUOTE_THRESHOLD di backend (default Rp 5.000.000)
const QUOTE_THRESHOLD = 5_000_000;
const MIN_VENDOR_ABOVE = 3;
const MIN_VENDOR_BELOW = 1;

const EMPTY_ITEM: PRLineItemInput = {
  item_name: "",
  quantity: 1,
  unit_of_measure: "pcs",
  estimated_unit_price: 0,
};

const EMPTY_VENDOR: VendorQuoteInput = {
  vendor_name: "",
  vendor_contact: "",
  quoted_price: 0,
  survey_date: "",
  is_recommended: false,
};

export default function RequesterPRNew() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { invalidate } = useProcurement();

  const [title, setTitle] = useState("");
  const [justification, setJustification] = useState("");
  const [items, setItems] = useState<PRLineItemInput[]>([{ ...EMPTY_ITEM }]);
  const [vendors, setVendors] = useState<VendorQuoteInput[]>([{ ...EMPTY_VENDOR }]);
  const [vendorFiles, setVendorFiles] = useState<(File | null)[]>([null]);
  const [recommendedIdx, setRecommendedIdx] = useState<number>(0);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [rupiahInputs, setRupiahInputs] = useState<Record<number, string>>({});

  // ── Line item helpers ──────────────────────────────────────────
  const updateItem = (index: number, field: keyof PRLineItemInput, value: string | number) => {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)));
  };
  const addItem = () => setItems((prev) => [...prev, { ...EMPTY_ITEM }]);
  const removeItem = (index: number) => {
    if (items.length <= 1) return;
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const getSubtotal = (item: PRLineItemInput) =>
    Math.round(item.quantity * item.estimated_unit_price * 100) / 100;
  const getTotal = () => items.reduce((sum, item) => sum + getSubtotal(item), 0);
  const requiredMinVendors = () => (getTotal() > QUOTE_THRESHOLD ? MIN_VENDOR_ABOVE : MIN_VENDOR_BELOW);

  // ── Vendor helpers ─────────────────────────────────────────────
  const updateVendor = (
    index: number,
    field: keyof VendorQuoteInput,
    value: string | number
  ) => {
    setVendors((prev) => prev.map((v, i) => (i === index ? { ...v, [field]: value } : v)));
  };
  
  const updateVendorPrice = (index: number, formattedValue: string) => {
    // Remove formatting characters and parse to number
    const numericValue = parseRupiah(formattedValue);
    setRupiahInputs((prev) => ({ ...prev, [index]: formattedValue }));
    updateVendor(index, "quoted_price", numericValue);
  };
  const addVendor = () => {
    setVendors((prev) => [...prev, { ...EMPTY_VENDOR }]);
    setVendorFiles((prev) => [...prev, null]);
  };
  const removeVendor = (index: number) => {
    if (vendors.length <= 1) return;
    setVendors((prev) => prev.filter((_, i) => i !== index));
    setVendorFiles((prev) => prev.filter((_, i) => i !== index));
    setRecommendedIdx((cur) => {
      if (cur === index) return 0;
      return cur > index ? cur - 1 : cur;
    });
  };
  const updateVendorFile = (index: number, file: File | null) => {
    setVendorFiles((prev) => prev.map((f, i) => (i === index ? file : f)));
  };

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

    if (errs.length === 0 && getTotal() <= 0) errs.push("Total harus lebih dari 0.");

    // Vendor rules
    const minV = requiredMinVendors();
    if (vendors.length < minV) {
      errs.push(
        `Minimal ${minV} penawaran vendor diperlukan untuk total ${formatCurrency(getTotal())}.`
      );
    }
    vendors.forEach((v, i) => {
      const n = i + 1;
      if (!v.vendor_name.trim()) errs.push(`Vendor #${n}: Nama vendor wajib diisi.`);
      if (!v.vendor_contact.trim()) errs.push(`Vendor #${n}: Kontak vendor wajib diisi.`);
      if (v.quoted_price <= 0) errs.push(`Vendor #${n}: Harga penawaran harus > 0.`);
      if (!v.survey_date) errs.push(`Vendor #${n}: Tanggal survei wajib diisi.`);
      if (!vendorFiles[i]) errs.push(`Vendor #${n}: Bukti survei wajib diunggah.`);
    });
    if (recommendedIdx < 0 || recommendedIdx >= vendors.length) {
      errs.push("Tepat satu vendor harus ditandai sebagai rekomendasi.");
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

    const itemsPayload = items.map((item) => ({
      item_name: item.item_name.trim(),
      quantity: Number(item.quantity),
      unit_of_measure: item.unit_of_measure.trim(),
      estimated_unit_price: Number(item.estimated_unit_price),
    }));

    const vendorsPayload = vendors.map((v, i) => ({
      vendor_name: v.vendor_name.trim(),
      vendor_contact: v.vendor_contact.trim(),
      quoted_price: Number(v.quoted_price),
      survey_date: v.survey_date,
      is_recommended: i === recommendedIdx,
    }));

    const formData = new FormData();
    formData.append("title", title.trim());
    formData.append("justification", justification.trim());
    formData.append("items_json", JSON.stringify(itemsPayload));
    formData.append("vendor_quotes_json", JSON.stringify(vendorsPayload));
    vendorFiles.forEach((file, i) => {
      if (file) formData.append(`vendor_quotes[${i}].survey_evidence`, file);
    });

    try {
      await api.post("/requisitions/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      showToast("success", "Purchase Requisition berhasil dibuat!");
      invalidate();
      navigate("/requester/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string; message?: string } } })?.response?.data
          ?.detail ??
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Gagal membuat Purchase Requisition.";
      showToast("error", msg);
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(val);

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
                        onChange={(e) => updateItem(index, "estimated_unit_price", parseFloat(e.target.value) || 0)}
                        className="input-inline input-number"
                      />
                    </td>
                    <td className="text-right font-mono">{formatCurrency(getSubtotal(item))}</td>
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

        {/* Vendor Quotes */}
        <div className="form-card">
          <div className="form-card-header">
            <h3>Penawaran Vendor</h3>
            <button type="button" className="btn btn-sm btn-primary" onClick={addVendor}>
              + Tambah Vendor
            </button>
          </div>

          {vendors.map((v, index) => (
            <div
              key={index}
              className="form-card"
              style={{ marginBottom: "1rem", background: "var(--color-surface-alt)" }}
            >
              <div className="form-card-header">
                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 700 }}>
                  <input
                    type="radio"
                    name="recommended_vendor"
                    checked={recommendedIdx === index}
                    onChange={() => setRecommendedIdx(index)}
                  />
                  Vendor #{index + 1} {recommendedIdx === index && "(Rekomendasi)"}
                </label>
                <button
                  type="button"
                  className="btn btn-sm btn-icon btn-danger-ghost"
                  onClick={() => removeVendor(index)}
                  disabled={vendors.length <= 1}
                  title="Hapus vendor"
                >
                  &times;
                </button>
              </div>

              <div className="form-group">
                <label>Nama Vendor *</label>
                <input
                  type="text"
                  value={v.vendor_name}
                  onChange={(e) => updateVendor(index, "vendor_name", e.target.value)}
                  placeholder="PT Sumber Makmur"
                  maxLength={255}
                />
              </div>
              <div className="form-group">
                <label>Kontak Vendor *</label>
                <input
                  type="text"
                  value={v.vendor_contact}
                  onChange={(e) => updateVendor(index, "vendor_contact", e.target.value)}
                  placeholder="Telepon / email / alamat"
                  maxLength={255}
                />
              </div>
              <div className="form-group">
                <label>Harga Penawaran (Rp) *</label>
                <input
                  type="text"
                  value={rupiahInputs[index] || (v.quoted_price > 0 ? new Intl.NumberFormat('id-ID').format(v.quoted_price) : '')}
                  onChange={(e) => updateVendorPrice(index, e.target.value)}
                  placeholder="Ketik angka, contoh: 1500000"
                />
                {v.quoted_price > 0 && (
                  <small style={{ fontSize: "0.875rem", marginTop: "0.25rem", display: "block", color: "#2563eb", fontWeight: 600 }}>
                    Format Rupiah: {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(v.quoted_price)}
                  </small>
                )}
              </div>
              <div className="form-group">
                <label>Tanggal Survei *</label>
                <input
                  type="date"
                  value={v.survey_date}
                  onChange={(e) => updateVendor(index, "survey_date", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Bukti Survei *</label>
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png,.pdf"
                  onChange={(e) => updateVendorFile(index, e.target.files?.[0] ?? null)}
                />
                {vendorFiles[index] && (
                  <span className="text-muted" style={{ fontSize: "0.9375rem" }}>
                    {vendorFiles[index]!.name} ({(vendorFiles[index]!.size / 1024).toFixed(0)} KB)
                  </span>
                )}
              </div>
            </div>
          ))}
          
          {/* Alert validation - positioned right before submit button */}
          {vendors.length < requiredMinVendors() && (
            <div className="alert alert-error" style={{ marginTop: "1rem" }}>
              <strong>Perhatian:</strong> Minimal <strong>{requiredMinVendors()}</strong> penawaran vendor diperlukan untuk total{" "}
              {formatCurrency(getTotal())}.
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="form-actions">
          <Link to="/requester/dashboard" className="btn btn-outline">
            Batal
          </Link>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Mengirim..." : "Submit Requisition"}
          </button>
        </div>
      </form>
    </div>
  );
}
