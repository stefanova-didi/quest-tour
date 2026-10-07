import { useEffect, useState } from "react";
import { adminApi, getServerReference, isServerError } from "../api";

export function Dashboard() {
  const [seedError, setSeedError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    adminApi
      .seedError()
      .then((res) => {
        if (!cancelled) setSeedError(res.error);
      })
      .catch((err) => {
        if (!cancelled) {
          if (isServerError(err)) {
            setSeedError(`Server error ${getServerReference(err) ?? ""}`);
          }
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="admin-section">
      <h1 className="t-title">Dashboard</h1>
      {seedError && (
        <div className="qc-field__error" role="alert">
          Seed error: {seedError}
        </div>
      )}
      {loading ? (
        <p className="t-body">Loading…</p>
      ) : (
        <nav className="admin-dashboard" aria-label="Admin sections">
          <a className="qc-btn qc-btn--secondary" href="/admin/landmarks">
            Landmarks
          </a>
          <a className="qc-btn qc-btn--secondary" href="/admin/games">
            Games
          </a>
          <a className="qc-btn qc-btn--secondary" href="/admin/teams">
            Teams
          </a>
          <a className="qc-btn qc-btn--secondary" href="/admin/photos">
            Photos
          </a>
        </nav>
      )}
    </div>
  );
}
