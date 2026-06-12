import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * React Error Boundary — catches unhandled JS errors in the component tree
 * and renders a fallback UI instead of crashing the entire application.
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

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-boundary-card">
            <div className="error-boundary-icon">!</div>
            <h2>Terjadi Kesalahan</h2>
            <p className="error-boundary-message">
              Aplikasi mengalami error yang tidak terduga. Silakan coba lagi
              atau kembali ke halaman utama.
            </p>
            {this.state.error && (
              <details className="error-boundary-details">
                <summary>Detail Error</summary>
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
