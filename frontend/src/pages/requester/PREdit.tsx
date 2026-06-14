import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../../services/api";
import { useToast } from "../../contexts/ToastContext";
import { useProcurement } from "../../contexts/ProcurementContext";
import { parseRupiah } from "../../utils/formatHelpers";
import type {
  PRLineItemInput,
  PRCreatePayload,
  APIResponse,
  PurchaseRequisition,
  VendorQuote,
} from "../../types";

const EMPTY_ITEM: PRLineItemInput = {
  item_name: "",
  quantity: 1,
  unit_of_measure: "pcs",
  estimated_unit_price: 0,
};

const EMPTY_VENDOR: Omit<VendorQuote, 'id' | 'pr_id'> = {
  vendor_name: "",
  vendor_contact: "",
  quoted_price: 0,
  survey_date: "",
  survey_evidence_url: "",
  is_recommended: false,
};

export default function RequesterPREdit() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { invalidate } = useProcurement();

  const [title, setTitle] = useState("");
  const [justification, setJustification] = useState("");
  const [items, setItems] = useState<PRLineItemInput[]>([{ ...EMPTY_ITEM }]);
  const [vendors, setVendors] = useState<Array<Omit<VendorQuote, 'id' | 'pr_id'>>>([{ ...EMPTY_VENDOR }]);
  const [vendorFiles, setVendorFiles] = useState<(File | null)[]>([null]);
  const [rupiahInputs, setRupiahInputs] = useState<Record<number, string>>({});
  const [recommendedIdx, setRecommendedIdx] = useState<number>(0);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Load existing PR data
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api
      .get<APIResponse<PurchaseRequisition>>(`/requisitions/${id}`)
      .then((res) => {
        const pr = res.data.data;
        if (pr.status !== "SUBMITTED" && pr.status !== "REJECTED") {
          setLoadError(
            "Hanya PR berstatus SUBMITTED atau REJECTED yang bisa diedit."
          );
          return;
        }
        setTitle(pr.title);
        setJustification(pr.justification || "");
        if (pr.line_items && pr.line_items.length > 0) {
          setItems(
            pr.line_items.map((item) => ({
              item_name: item.item_name,
              quantity: item.quantity,
              unit_of_measure: item.unit_of_measure,
              estimated_unit_price: item.estimated_unit_price,
            }))
          );
        }
        // Load vendor quotes
        if (pr.vendor_quotes && pr.vendor_quotes.length > 0) {
          setVendors(
            pr.vendor_quotes.map((quote) => ({
              vendor_name: quote.vendor_name,
              vendor_contact: quote.vendor_contact,
              quoted_price: quote.quoted_price,
              survey_date: quote.survey_date,
              survey_evidence_url: quote.survey_evidence_url,
              is_recommended: quote.is_recommended,
            }))
          );
          // Set recommended index
          const recIdx = pr.vendor_quotes.findIndex((q) => q.is_recommended);
          if (recIdx >= 0) setRecommendedIdx(recIdx);
          // Initialize rupiah inputs
          const rupiahInit: Record<number, string> = {};
          pr.vendor_quotes.forEach((q, idx) => {
            if (q.quoted_price > 0) {
              rupiahInit[idx] = new Intl.NumberFormat('id-ID').format(q.quoted_price);
            }
          });
          setRupiahInputs(rupiahInit);
        }
      })
      .catch(() => setLoadError("Gagal memuat data PR."))
      .finally(() => setLoading(false));
  }, [id]);

  // Line item helpers
  const updateItem = (
    index: number,
    field: keyof PRLineItemInput,
    value: string | number
  ) => {
    setItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, [field]: value } : item))
    );
  };

  const addItem = () => {
    setItems((prev) => [...prev, { ...EMPTY_ITEM }]);
  };

  const removeItem = (index: number) => {
    if (items.length <= 1) return;
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const getSubtotal = (item: PRLineItemInput) =>
    Math.round(item.quantity * item.estimated_unit_price * 100) / 100;

  const getTotal = () =>
    items.reduce((sum, item) => sum + getSubtotal(item), 0);

  // Vendor quote helpers
  const requiredMinVendors = () => {
    const total = getTotal();
    return total >= 50_000_000 ? 3 : 1;
  };

  const updateVendor = (
    index: number,
    field: keyof Omit<VendorQuote, 'id' | 'pr_id'>,
    value: string | number | boolean | null
  ) => {
    setVendors((prev) =>
      prev.map((v, i) => (i === index ? { ...v, [field]: value } : v))
    );
  };

  const updateVendorPrice = (index: number, formattedValue: string) => {
    const numericValue = parseRupiah(formattedValue);
    setRupiahInputs((prev) => ({ ...prev, [index]: formattedValue }));
    updateVendor(index, "quoted_price", numericValue);
  };

  const addVendor = () => {
    setVendors((prev) => [...prev, { ...EMPTY_VENDOR }]);
    setVendorFiles((prev) => [...prev, null]);
  };

  const removeVendor = (index: number) => {
    if (vendors.length <= requiredMinVendors()) return;
    setVendors((prev) => prev.filter((_, i) => i !== index));
    setVendorFiles((prev) => prev.filter((_, i) => i !== index));
    setRupiahInputs((prev) => {
      const newInputs = { ...prev };
      delete newInputs[index];
      return newInputs;
    });
  };

  const updateVendorFile = (index: number, file: File | null) => {
    setVendorFiles((prev) => prev.map((f, i) => (i === index ? file : f)));
  };

  // Validation
  const validate = (): string[] => {
    const errs: string[] = [];
    if (!title.trim()) errs.push("Judul PR wajib diisi.");
    if (!justification.trim()) errs.push("Justifikasi wajib diisi.");
    if (items.length === 0) errs.push("Minimal 1 line item diperlukan.");

    items.forEach((item, i) => {
      const n = i + 1;
      if (!item.item_name.trim())
        errs.push(`Item #${n}: Nama item wajib diisi.`);
      if (item.quantity <= 0) errs.push(`Item #${n}: Quantity harus > 0.`);
      if (!item.unit_of_measure.trim())
        errs.push(`Item #${n}: Satuan wajib diisi.`);
      if (item.estimated_unit_price <= 0)
        errs.push(`Item #${n}: Harga estimasi harus > 0.`);
    });

    if (errs.length === 0 && getTotal() <= 0) {
      errs.push("Total harus lebih dari 0.");
    }

    // Vendor validation
    const minVendors = requiredMinVendors();
    if (vendors.length < minVendors) {
      errs.push(`Minimal ${minVendors} penawaran vendor diperlukan.`);
    }

    vendors.forEach((v, i) => {
      const n = i + 1;
      if (!v.vendor_name.trim())
        errs.push(`Vendor #${n}: Nama vendor wajib diisi.`);
      if (!v.vendor_contact.trim())
        errs.push(`Vendor #${n}: Kontak vendor wajib diisi.`);
      if (v.quoted_price <= 0)
        errs.push(`Vendor #${n}: Harga penawaran harus > 0.`);
      if (!v.survey_date)
        errs.push(`Vendor #${n}: Tanggal survei wajib diisi.`);
      // Check if file is uploaded or existing file exists
      if (!vendorFiles[i] && (!v.survey_evidence_url || v.survey_evidence_url.trim() === "")) {
        errs.push(`Vendor #${n}: Bukti survei wajib diunggah.`);
      }
    });

    // Check for single recommended vendor
    const recommendedCount = vendors.filter((v) => v.is_recommended).length;
    if (recommendedCount !== 1) {
      errs.push("Harus ada tepat 1 vendor yang direkomendasikan.");
    }

    return errs;
  };

  // Submit update
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors([]);
    setSubmitting(true);

    try {
      // First, update line items and PR info using existing endpoint
      const prPayload: PRCreatePayload = {
        title: title.trim(),
        justification: justification.trim(),
        items: items.map((item) => ({
          item_name: item.item_name.trim(),
          quantity: Number(item.quantity),
          unit_of_measure: item.unit_of_measure.trim(),
          estimated_unit_price: Number(item.estimated_unit_price),
        })),
      };

      await api.put<APIResponse<PurchaseRequisition>>(
        `/requisitions/${id}`,
        prPayload
      );

      // Then, update vendor quotes using new endpoint with multipart/form-data
      const formData = new FormData();
      formData.append("vendor_quotes_json", JSON.stringify(
        vendors.map((v, idx) => ({
          vendor_name: v.vendor_name.trim(),
          vendor_contact: v.vendor_contact.trim(),
          quoted_price: Number(v.quoted_price),
          survey_date: v.survey_date,
          is_recommended: idx === recommendedIdx,
        }))
      ));

      // Append files
      vendorFiles.forEach((file, idx) => {
        if (file) {
          formData.append(`vendor_quotes[${idx}].survey_evidence`, file);
        }
      });

      await api.put<APIResponse<PurchaseRequisition>>(
        `/requisitions/${id}/vendors`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      showToast("success", "Purchase Requisition dan vendor quotes berhasil diperbarui!");
      invalidate();
      navigate(`/requester/pr/${id}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string; message?: string } } })
          ?.response?.data?.detail ??
        (err as { response?: { data?: { message?: string } } })?.response?.data
          ?.message ??
        "Gagal memperbarui Purchase Requisition.";
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

  if (loading) return <p className="text-muted">Memuat data PR...</p>;
  if (loadError)
    return <div className="alert alert-error">{loadError}</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Edit Purchase Requisition</h2>
        <Link to={`/requester/pr/${id}`} className="btn btn-outline">
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
            <button
              type="button"
              className="btn btn-sm btn-primary"
              onClick={addItem}
            >
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
                  <th style={{ width: "140px" }} className="text-right">
                    Subtotal
                  </th>
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
                        onChange={(e) =>
                          updateItem(index, "item_name", e.target.value)
                        }
                        placeholder="Nama item"
                        className="input-inline"
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min={1}
                        value={item.quantity}
                        onChange={(e) =>
                          updateItem(
                            index,
                            "quantity",
                            parseInt(e.target.value) || 0
                          )
                        }
                        className="input-inline input-number"
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={item.unit_of_measure}
                        onChange={(e) =>
                          updateItem(
                            index,
                            "unit_of_measure",
                            e.target.value
                          )
                        }
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
                          updateItem(
                            index,
                            "estimated_unit_price",
                            parseFloat(e.target.value) || 0
                          )
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
                  <td
                    colSpan={5}
                    className="text-right"
                    style={{ fontWeight: 700 }}
                  >
                    Total Estimasi
                  </td>
                  <td
                    className="text-right font-mono"
                    style={{ fontWeight: 700 }}
                  >
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
                  disabled={vendors.length <= requiredMinVendors()}
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
                    File baru: {vendorFiles[index]!.name} ({(vendorFiles[index]!.size / 1024).toFixed(0)} KB)
                  </span>
                )}
                {!vendorFiles[index] && v.survey_evidence_url && v.survey_evidence_url.trim() !== "" && (
                  <span className="text-muted" style={{ fontSize: "0.9375rem" }}>
                    Menggunakan file existing: <a href={`${import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:9395'}/${v.survey_evidence_url}`} target="_blank" rel="noopener noreferrer">Lihat file</a>
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
          <Link to={`/requester/pr/${id}`} className="btn btn-outline">
            Batal
          </Link>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? "Menyimpan..." : "Simpan Perubahan"}
          </button>
        </div>
      </form>
    </div>
  );
}
