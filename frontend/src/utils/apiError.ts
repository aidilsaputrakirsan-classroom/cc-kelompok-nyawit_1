import type { AxiosError } from "axios";

export const SERVICE_UNAVAILABLE_MESSAGE = "Service temporarily unavailable";

export function isServiceUnavailable(status?: number): boolean {
  return status === undefined || status === 502 || status === 503 || status === 504;
}

/** Error kustom agar ErrorBoundary bisa menampilkan pesan API yang ramah. */
export class ApiError extends Error {
  readonly statusCode?: number;
  readonly isApiError = true;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

interface ApiErrorBody {
  detail?: string | { msg?: string }[];
  message?: string;
}

/** Ubah response error Axios menjadi pesan yang mudah dipahami pengguna. */
export function getFriendlyApiErrorMessage(error: unknown): string {
  if (!error) {
    return "Terjadi kesalahan yang tidak diketahui. Silakan coba lagi.";
  }

  if (error instanceof ApiError) {
    return error.message;
  }

  const axiosError = error as AxiosError<ApiErrorBody>;

  if (axiosError.code === "ERR_NETWORK" || !axiosError.response) {
    return SERVICE_UNAVAILABLE_MESSAGE;
  }

  const status = axiosError.response.status;

  if (isServiceUnavailable(status)) {
    return SERVICE_UNAVAILABLE_MESSAGE;
  }
  const data = axiosError.response.data;

  if (typeof data?.message === "string" && data.message.trim()) {
    return data.message;
  }

  if (typeof data?.detail === "string" && data.detail.trim()) {
    return data.detail;
  }

  if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
    return data.detail[0].msg;
  }

  switch (status) {
    case 400:
      return "Data yang Anda kirim tidak valid. Periksa kembali formulir.";
    case 401:
      return "Sesi Anda telah berakhir. Silakan login kembali.";
    case 403:
      return "Anda tidak memiliki izin untuk melakukan aksi ini.";
    case 404:
      return "Data yang diminta tidak ditemukan.";
    case 409:
      return "Data sudah ada atau bentrok dengan data lain.";
    case 413:
      return "Ukuran file terlalu besar. Coba unggah file yang lebih kecil.";
    case 422:
      return "Beberapa field tidak valid. Periksa kembali input Anda.";
    case 429:
      return "Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi.";
    case 500:
      return "Server mengalami gangguan. Tim kami sedang menanganinya.";
    default:
      return `Terjadi kesalahan (kode ${status}). Silakan coba lagi.`;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError && error.isApiError;
}
