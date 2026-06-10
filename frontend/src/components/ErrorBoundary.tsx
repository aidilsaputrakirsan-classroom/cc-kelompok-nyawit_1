import { Component, type ErrorInfo, type ReactNode } from "react";
import { getFriendlyApiErrorMessage, isApiError } from "../utils/apiError";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

const isProduction = import.meta.env.PROD;

/**
 * React Error Boundary — menangkap error render dan menampilkan pesan ramah,
 * termasuk error API yang dibungkus sebagai ApiError.
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[ErrorBoundary] Uncaught error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  handleReload = () => {
    window.location.href = "/";
  };

  private getDisplayMessage(): string {
    const { error } = this.state;
    if (!error) {
      return "Aplikasi mengalami gangguan. Silakan coba lagi atau kembali ke halaman utama.";
    }

    if (isApiError(error)) {
      return error.message;
    }

    return getFriendlyApiErrorMessage(error);
  }

  render() {
    if (this.state.hasError) {
      const apiError = isApiError(this.state.error);
      const title = apiError ? "Gagal Memuat Data" : "Terjadi Kesalahan";

      return (
        <div className="error-boundary">
          <div className="error-boundary-card">
            <div className="error-boundary-icon">!</div>
            <h2>{title}</h2>
            <p className="error-boundary-message">{this.getDisplayMessage()}</p>
            {!isProduction && this.state.error && (
              <details className="error-boundary-details">
                <summary>Detail Error (development)</summary>
                <pre>{this.state.error.message}</pre>
              </details>
            )}
            <div className="error-boundary-actions">
              <button className="btn btn-outline" onClick={this.handleReset}>
                Coba Lagi
              </button>
              <button className="btn btn-primary" onClick={this.handleReload}>
                Kembali ke Beranda
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
