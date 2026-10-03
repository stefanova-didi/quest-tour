import { useEffect, useId, useRef, type ReactNode } from "react";

export function ConfirmSheet({ title, body, cost, confirmLabel, danger = false, busy = false, onConfirm, onCancel }: {
  title: string; body: ReactNode; cost?: ReactNode; confirmLabel: string; danger?: boolean; busy?: boolean;
  onConfirm(): void; onCancel(): void;
}) {
  const titleId = useId();
  const confirmRef = useRef<HTMLButtonElement>(null);
  useEffect(() => { confirmRef.current?.focus(); }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onCancel(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);
  return (
    <div className="qs-overlay qc-scrim" onClick={(e) => { if (e.target === e.currentTarget) onCancel(); }}>
      <div className="qc-sheet" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <h2 className="qc-sheet__title" id={titleId}>{title}</h2>
        <p className="qc-sheet__body">{body}</p>
        {cost && <div className="qc-sheet__cost">{cost}</div>}
        <div className="qc-sheet__actions">
          <button ref={confirmRef} type="button" disabled={busy} onClick={onConfirm}
                  className={`qc-btn ${danger ? "qc-btn--danger" : "qc-btn--primary"} qc-btn--block`}>{confirmLabel}</button>
          <button type="button" className="qc-btn qc-btn--secondary qc-btn--block" onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  );
}
