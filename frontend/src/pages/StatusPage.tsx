import { useState, useEffect, useCallback } from "react";

const GATEWAY_URL =
  import.meta.env.VITE_GATEWAY_URL || "http://localhost";

interface HealthData {
  status: string;
  service?: string;
  version?: string;
  checks?: Record<string, { status: string; [key: string]: unknown }>;
  [key: string]: unknown;
}

interface MetricsData {
  total_requests: number;
  total_errors: number;
  error_rate_percent: string;
  uptime_seconds: number;
  latency: {
    avg_ms: number;
    p50_ms: number;
    p95_ms: number;
    p99_ms: number;
  };
}

const STATUS_COLORS: Record<string, string> = {
  healthy: "#22c55e",
  degraded: "#f59e0b",
  unhealthy: "#ef4444",
  unreachable: "#6b7280",
};

function ServiceCard({
  name,
  icon,
  healthUrl,
  metricsUrl,
}: {
  name: string;
  icon: string;
  healthUrl: string;
  metricsUrl: string | null;
}) {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<string>("");

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(healthUrl);
      setHealth(await res.json());
    } catch {
      setHealth({ status: "unreachable" });
    }

    if (metricsUrl) {
      try {
        const res = await fetch(metricsUrl);
        setMetrics(await res.json());
      } catch {
        setMetrics(null);
      }
    }

    setLastChecked(new Date().toLocaleTimeString());
    setLoading(false);
  }, [healthUrl, metricsUrl]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const status = health?.status || "unreachable";
  const color = STATUS_COLORS[status] || "#6b7280";

  return (
    <div
      style={{
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "20px",
        borderLeft: `4px solid ${color}`,
        background: "#fff",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h3 style={{ margin: 0 }}>
          {icon} {name}
        </h3>
        <span
          style={{
            background: color,
            color: "#fff",
            padding: "4px 12px",
            borderRadius: "20px",
            fontSize: "13px",
            fontWeight: "600",
            textTransform: "uppercase",
          }}
        >
          {loading ? "..." : status}
        </span>
      </div>

      {/* Health checks detail */}
      {health?.checks && (
        <div
          style={{
            marginTop: "12px",
            display: "flex",
            gap: "8px",
            flexWrap: "wrap",
          }}
        >
          {Object.entries(health.checks).map(([key, val]) => (
            <span
              key={key}
              style={{
                fontSize: "12px",
                padding: "2px 8px",
                borderRadius: "6px",
                background:
                  val.status === "healthy" ? "#dcfce7" : "#fef3c7",
                color: val.status === "healthy" ? "#166534" : "#92400e",
              }}
            >
              {key}: {val.status}
            </span>
          ))}
        </div>
      )}

      {/* Metrics */}
      {metrics && (
        <div style={{ marginTop: "16px", fontSize: "14px", color: "#64748b" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: "8px",
            }}
          >
            <div>
              Requests: <strong>{metrics.total_requests}</strong>
            </div>
            <div>
              Errors:{" "}
              <strong
                style={{
                  color: metrics.total_errors > 0 ? "#ef4444" : "inherit",
                }}
              >
                {metrics.total_errors}
              </strong>
            </div>
            <div>
              Error Rate: <strong>{metrics.error_rate_percent}%</strong>
            </div>
            <div>
              Avg Latency: <strong>{metrics.latency?.avg_ms || 0}ms</strong>
            </div>
            <div>
              p95 Latency: <strong>{metrics.latency?.p95_ms || 0}ms</strong>
            </div>
            <div>
              Uptime:{" "}
              <strong>{Math.round((metrics.uptime_seconds || 0) / 60)}min</strong>
            </div>
          </div>
        </div>
      )}

      <div style={{ marginTop: "8px", fontSize: "11px", color: "#94a3b8" }}>
        Last checked: {lastChecked}
      </div>
    </div>
  );
}

export default function StatusPage() {
  return (
    <div style={{ maxWidth: "800px", margin: "40px auto", padding: "0 20px" }}>
      <h1>System Status</h1>
      <p style={{ color: "#64748b" }}>
        Real-time health monitoring — auto-refresh setiap 10 detik
      </p>

      <div style={{ display: "grid", gap: "16px", marginTop: "24px" }}>
        <ServiceCard
          name="Auth Service"
          icon="[A]"
          healthUrl={`${GATEWAY_URL}/auth/health`}
          metricsUrl={`${GATEWAY_URL}/auth/metrics`}
        />
        <ServiceCard
          name="Procurement Service"
          icon="[P]"
          healthUrl={`${GATEWAY_URL}/api/health`}
          metricsUrl={`${GATEWAY_URL}/api/metrics`}
        />
        <ServiceCard
          name="API Gateway"
          icon="[G]"
          healthUrl={`${GATEWAY_URL}/health`}
          metricsUrl={null}
        />
      </div>

      <p style={{ marginTop: "24px", fontSize: "13px", color: "#94a3b8" }}>
        Endpoint: {GATEWAY_URL}
      </p>
    </div>
  );
}
