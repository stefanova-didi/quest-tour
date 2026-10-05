import { useState } from "react";
import { ConfirmSheet } from "./ConfirmSheet";

/** R-25: shown only on service (test) links, on every screen. */
export function ServiceBar({ onReset }: { onReset(): Promise<unknown> }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const confirm = async () => {
    setBusy(true);
    try {
      await onReset();
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };
  return (
    <>
      <div className="qs-service-bar" role="region" aria-label="Test link">
        <span className="qs-service-bar__label">Test link · no time limits</span>
        <button type="button" className="qs-service-bar__btn" onClick={() => setConfirming(true)}>
          Reset test run
        </button>
      </div>
      {confirming && (
        <div className="qs-service-sheet">
          <ConfirmSheet
            title="Reset this test run?"
            body="All progress, answers and photos of this test run are deleted and the game starts again from the beginning."
            confirmLabel="Reset"
            danger
            busy={busy}
            onConfirm={() => void confirm()}
            onCancel={() => setConfirming(false)}
          />
        </div>
      )}
    </>
  );
}
