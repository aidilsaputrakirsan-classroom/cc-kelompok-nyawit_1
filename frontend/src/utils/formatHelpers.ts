/**
 * Utility helpers for currency and date formatting
 */

/**
 * Format number as Indonesian Rupiah (IDR)
 * Example: 1500000 → "Rp 1.500.000"
 */
export function formatRupiah(value: number | string): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'Rp 0';
  
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

/**
 * Parse Rupiah formatted string back to number
 * Example: "Rp 1.500.000" → 1500000
 */
export function parseRupiah(value: string): number {
  if (!value) return 0;
  // Remove "Rp", dots, commas, and spaces
  const cleaned = value.replace(/[Rp\s.,]/g, '');
  const num = parseInt(cleaned, 10);
  return isNaN(num) ? 0 : num;
}

/**
 * Format date to Indonesian format dd/mm/yyyy
 * Example: "2024-01-15" → "15/01/2024"
 */
export function formatDateID(dateStr: string): string {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    
    return `${day}/${month}/${year}`;
  } catch {
    return dateStr;
  }
}

/**
 * Format date with time to Indonesian format
 * Example: "2024-01-15T10:30:00" → "15/01/2024, 10:30"
 */
export function formatDateTimeID(dateStr: string): string {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${day}/${month}/${year}, ${hours}:${minutes}`;
  } catch {
    return dateStr;
  }
}

/**
 * Convert input value to Rupiah format for display in input fields
 * Returns formatted string like "1.500.000" (without Rp prefix for input)
 */
export function formatInputRupiah(value: number | string): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num) || num === 0) return '';
  
  return new Intl.NumberFormat('id-ID').format(num);
}
