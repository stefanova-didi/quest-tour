import { useEffect, useRef, type CSSProperties } from "react";
import type { Clock } from "../api/types";
import { formatHms, formatLeft, formatPenalty } from "../lib/format";
import { useNow } from "../lib/useNow";
import { Icon } from "./Icon";

const WARNING_SECONDS = 15 * 60;

export function GameHeader({ clock, position, taskCount, receivedAt, onTimeUp }: {
  clock: Clock; position: number; taskCount: number; receivedAt: number; onTimeUp(): void;
}) {
  const now = useNow(clock.running ? 1000 : null);
  const drift = clock.running ? Math.max(0, Math.floor((now - receivedAt) / 1000)) : 0;
  const elapsed = clock.elapsed_seconds + drift;
  const remaining = clock.remaining_seconds === null ? null : Math.max(0, clock.remaining_seconds - drift);
  const warning = clock.running && remaining !== null && remaining <= WARNING_SECONDS;
  const taskNo = Math.min(position + 1, taskCount);
  const penalty = clock.penalty_minutes > 0 ? formatPenalty(clock.penalty_minutes) : null;

  const firedFor = useRef<number | null>(null);
  useEffect(() => {                                  // the server decides; ask it as soon as the local clock hits 0
    if (clock.running && remaining === 0 && firedFor.current !== receivedAt) {
      firedFor.current = receivedAt;
      onTimeUp();
    }
  }, [clock.running, remaining, receivedAt, onTimeUp]);

  return (
    <header className={warning ? "qc-header qc-header--warning" : "qc-header"}
            aria-label={warning ? "Game status – time running out" : "Game status"} style={{ flex: "none" }}>
      <div className="qc-header__top">
        <span className="qc-header__clock"><Icon name="clock" />{formatHms(elapsed)}</span>
        {warning
          ? <span className="qc-header__left">{formatLeft(remaining!)}</span>
          : penalty && <span className="qc-tag qc-tag--on-dark">{penalty}</span>}
      </div>
      <div className="qc-header__progress">
        <span>Task {taskNo} of {taskCount}{warning && penalty ? ` · ${penalty}` : ""}</span>
        <div className="qc-progress qc-progress--seg" role="progressbar" aria-label="Quest progress"
             aria-valuenow={taskNo} aria-valuemin={0} aria-valuemax={taskCount}
             style={{ "--segments": taskCount } as CSSProperties}>
          <span style={{ width: `${(taskNo / taskCount) * 100}%` }} />
        </div>
      </div>
    </header>
  );
}
