interface ApiErrorFallbackProps {
  message: string;
  onRetry?: () => void;
}

/** Tampilan inline saat operasi API gagal di dalam halaman. */
export default function ApiErrorFallback({
  message,
  onRetry,
}: ApiErrorFallbackProps) {
  return (
    <div className="api-error-fallback" role="alert">
      <div className="api-error-fallback-icon" aria-hidden="true">
        !
      </div>
      <div className="api-error-fallback-body">
        <h3>Gagal Memuat Data</h3>
        <p>{message}</p>
        {onRetry && (
          <button type="button" className="btn btn-outline btn-sm" onClick={onRetry}>
            Coba Lagi
          </button>
        )}
      </div>
    </div>
  );
}
