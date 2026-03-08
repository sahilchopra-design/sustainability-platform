import React from "react";

/**
 * Global Error Boundary — catches unhandled React render errors
 * across the entire component tree. Displays a graceful fallback UI
 * with recovery options instead of a blank white screen.
 *
 * Implements:
 *   - Class-based componentDidCatch lifecycle
 *   - Error detail logging (console + optional Sentry hook)
 *   - "Retry" (re-render last route) + "Go Home" recovery actions
 *   - Collapsible technical details for developers
 *   - Consistent dark theme matching platform design system
 */

/* ------------------------------------------------------------------ */
/*  Error logging hook — replace with Sentry.captureException() later */
/* ------------------------------------------------------------------ */
function logError(error, errorInfo) {
  // eslint-disable-next-line no-console
  console.error("[ErrorBoundary] Unhandled render error:", error);
  // eslint-disable-next-line no-console
  console.error("[ErrorBoundary] Component stack:", errorInfo?.componentStack);

  // TODO: wire Sentry when P0 #6 (error monitoring) is implemented
  // if (window.Sentry) {
  //   window.Sentry.captureException(error, { extra: errorInfo });
  // }
}

/* ------------------------------------------------------------------ */
/*  Fallback UI                                                       */
/* ------------------------------------------------------------------ */
function FallbackUI({ error, resetError, goHome }) {
  const [showDetails, setShowDetails] = React.useState(false);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#060c18",
        color: "#e2e8f0",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: "2rem",
      }}
    >
      <div
        style={{
          maxWidth: 560,
          width: "100%",
          background: "rgba(15, 23, 42, 0.85)",
          border: "1px solid rgba(56, 189, 248, 0.15)",
          borderRadius: 12,
          padding: "2.5rem",
          boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        }}
      >
        {/* Icon */}
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            background: "rgba(239, 68, 68, 0.12)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: "1.5rem",
          }}
        >
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#ef4444"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        {/* Title */}
        <h1
          style={{
            fontSize: "1.375rem",
            fontWeight: 600,
            color: "#f1f5f9",
            margin: "0 0 0.5rem 0",
          }}
        >
          Something went wrong
        </h1>

        {/* Description */}
        <p
          style={{
            fontSize: "0.9rem",
            color: "#94a3b8",
            lineHeight: 1.6,
            margin: "0 0 1.5rem 0",
          }}
        >
          An unexpected error occurred while rendering this page. Your data is
          safe. You can try reloading the current view or navigate back to the
          dashboard.
        </p>

        {/* Error summary (always visible) */}
        <div
          style={{
            background: "rgba(239, 68, 68, 0.06)",
            border: "1px solid rgba(239, 68, 68, 0.18)",
            borderRadius: 8,
            padding: "0.75rem 1rem",
            marginBottom: "1.25rem",
            fontSize: "0.8rem",
            fontFamily: "monospace",
            color: "#fca5a5",
            wordBreak: "break-word",
            maxHeight: 60,
            overflow: "hidden",
          }}
        >
          {error?.message || "Unknown error"}
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
          <button
            onClick={resetError}
            style={{
              flex: 1,
              padding: "0.625rem 1rem",
              background: "rgba(56, 189, 248, 0.12)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              borderRadius: 8,
              color: "#38bdf8",
              fontWeight: 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.target.style.background = "rgba(56, 189, 248, 0.2)";
            }}
            onMouseLeave={(e) => {
              e.target.style.background = "rgba(56, 189, 248, 0.12)";
            }}
          >
            Retry
          </button>
          <button
            onClick={goHome}
            style={{
              flex: 1,
              padding: "0.625rem 1rem",
              background: "rgba(148, 163, 184, 0.08)",
              border: "1px solid rgba(148, 163, 184, 0.2)",
              borderRadius: 8,
              color: "#94a3b8",
              fontWeight: 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.target.style.background = "rgba(148, 163, 184, 0.15)";
            }}
            onMouseLeave={(e) => {
              e.target.style.background = "rgba(148, 163, 184, 0.08)";
            }}
          >
            Go to Dashboard
          </button>
        </div>

        {/* Collapsible technical details */}
        <button
          onClick={() => setShowDetails((v) => !v)}
          style={{
            background: "none",
            border: "none",
            color: "#64748b",
            fontSize: "0.75rem",
            cursor: "pointer",
            padding: "0.25rem 0",
            display: "flex",
            alignItems: "center",
            gap: 4,
          }}
        >
          <span
            style={{
              display: "inline-block",
              transform: showDetails ? "rotate(90deg)" : "rotate(0deg)",
              transition: "transform 0.15s ease",
            }}
          >
            &#9654;
          </span>
          Technical details
        </button>

        {showDetails && (
          <pre
            style={{
              marginTop: "0.5rem",
              background: "rgba(0,0,0,0.3)",
              border: "1px solid rgba(100,116,139,0.15)",
              borderRadius: 6,
              padding: "0.75rem",
              fontSize: "0.7rem",
              color: "#94a3b8",
              overflow: "auto",
              maxHeight: 200,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {error?.stack || "No stack trace available"}
          </pre>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Error Boundary (class component — React requirement)              */
/* ------------------------------------------------------------------ */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    logError(error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  goHome = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = "/";
  };

  render() {
    if (this.state.hasError) {
      return (
        <FallbackUI
          error={this.state.error}
          resetError={this.resetError}
          goHome={this.goHome}
        />
      );
    }
    return this.props.children;
  }
}

/**
 * Route-level error boundary — wraps individual route components
 * so a single page crash doesn't take down the sidebar/nav.
 */
class RouteErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    logError(error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: "2rem",
            color: "#e2e8f0",
            fontFamily:
              '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          }}
        >
          <div
            style={{
              background: "rgba(239, 68, 68, 0.06)",
              border: "1px solid rgba(239, 68, 68, 0.15)",
              borderRadius: 10,
              padding: "1.5rem",
              maxWidth: 480,
            }}
          >
            <h2
              style={{
                fontSize: "1.1rem",
                fontWeight: 600,
                color: "#fca5a5",
                margin: "0 0 0.5rem 0",
              }}
            >
              Page Error
            </h2>
            <p
              style={{
                fontSize: "0.85rem",
                color: "#94a3b8",
                margin: "0 0 1rem 0",
                lineHeight: 1.5,
              }}
            >
              This section encountered an error. Other parts of the application
              remain functional.
            </p>
            <p
              style={{
                fontSize: "0.75rem",
                fontFamily: "monospace",
                color: "#f87171",
                margin: "0 0 1rem 0",
                wordBreak: "break-word",
              }}
            >
              {this.state.error?.message || "Unknown error"}
            </p>
            <button
              onClick={this.resetError}
              style={{
                padding: "0.5rem 1rem",
                background: "rgba(56, 189, 248, 0.12)",
                border: "1px solid rgba(56, 189, 248, 0.25)",
                borderRadius: 6,
                color: "#38bdf8",
                fontWeight: 500,
                fontSize: "0.8rem",
                cursor: "pointer",
              }}
            >
              Retry
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export { ErrorBoundary, RouteErrorBoundary };
export default ErrorBoundary;
