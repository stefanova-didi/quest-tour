import { useEffect } from "react";
import { Icon } from "./Icon";

export function Toast({ message, onDone, ms = 5000, high = false }: {
  message: string; onDone(): void; ms?: number; high?: boolean;
}) {
  useEffect(() => { const id = window.setTimeout(onDone, ms); return () => window.clearTimeout(id); }, [message, onDone, ms]);
  return (
    <div className={high ? "qs-toast-slot qs-toast-slot--high" : "qs-toast-slot"}>
      <div className="qc-toast" role="status">
        <Icon name="team" />{message}
        <button type="button" aria-label="Dismiss" onClick={onDone}
                style={{ marginLeft: "auto", background: "none", border: 0, color: "inherit", font: "inherit", cursor: "pointer", padding: 4 }}>✕</button>
      </div>
    </div>
  );
}
