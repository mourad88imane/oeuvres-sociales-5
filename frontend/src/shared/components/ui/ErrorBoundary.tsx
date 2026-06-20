import { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[ErrorBoundary]", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mb-6"
            style={{ background: "rgba(239,68,68,0.1)" }}>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold mb-2" style={{ color: "#1a1917" }}>
            Une erreur inattendue s'est produite
          </h2>
          <p className="text-sm mb-6 max-w-md" style={{ color: "#8a8882" }}>
            L'application a rencontré une erreur. Veuillez réessayer ou contacter l'équipe technique.
          </p>
          <div className="flex gap-3">
            <button
              onClick={this.handleReset}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-xl font-bold transition-colors"
              style={{
                background: "#1a1917",
                color: "#ffffff",
              }}
              onMouseEnter={e => { e.currentTarget.style.opacity = "0.9"; }}
              onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
            >
              <RefreshCw className="w-4 h-4" />
              Réessayer
            </button>
            <button
              onClick={this.handleReload}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-xl font-bold transition-colors"
              style={{
                border: "1px solid rgba(0,0,0,0.08)",
                color: "#4d4b46",
              }}
              onMouseEnter={e => { e.currentTarget.style.background = "rgba(0,0,0,0.03)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}
            >
              <Home className="w-4 h-4" />
              Recharger la page
            </button>
          </div>
          {this.state.error && (
            <details className="mt-6 text-left max-w-lg">
              <summary className="text-xs font-medium cursor-pointer" style={{ color: "#8a8882" }}>
                Détails techniques
              </summary>
              <pre className="mt-2 p-3 text-xs rounded-xl overflow-auto max-h-32"
                style={{
                  background: "rgba(0,0,0,0.04)",
                  color: "#dc2626",
                  border: "1px solid rgba(0,0,0,0.06)",
                }}>
                {this.state.error.name}: {this.state.error.message}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
