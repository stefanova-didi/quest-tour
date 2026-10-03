import type { ReactNode } from "react";
import { ConnectionBanner } from "./ConnectionBanner";
import { Toast } from "./Toast";

export interface FrameProps { header: ReactNode; offline: boolean; notice: string | null; onNoticeDone(): void; }

export function GameFrame({ frame, mainClassName = "qs-main", actions, overlay, toastHigh = false, children }: {
  frame: FrameProps; mainClassName?: string; actions?: ReactNode; overlay?: ReactNode;
  toastHigh?: boolean; children: ReactNode;
}) {
  const modal = Boolean(overlay);                     // a ConfirmSheet is open: keep focus inside it
  return (
    <div className="qs">
      {frame.header}
      {frame.offline && <ConnectionBanner />}
      <main className={mainClassName} inert={modal}>{children}</main>
      {actions && <div className="qs-actions-slot" inert={modal}>{actions}</div>}
      {frame.notice && <Toast message={frame.notice} onDone={frame.onNoticeDone} high={toastHigh} />}
      {overlay}
    </div>
  );
}
