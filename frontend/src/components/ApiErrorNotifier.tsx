import { useEffect } from "react";
import { useToast } from "../contexts/ToastContext";
import { subscribeApiErrors } from "../utils/apiErrorEvents";

/**
 * Menampilkan toast ramah pengguna saat interceptor API mendeteksi error global.
 * Dipasang di dalam ToastProvider.
 */
export default function ApiErrorNotifier() {
  const { showToast } = useToast();

  useEffect(() => {
    return subscribeApiErrors((message) => {
      showToast("error", message);
    });
  }, [showToast]);

  return null;
}
