import { useRef, useState, type ChangeEvent } from "react";
import { HttpError, isConnectionProblem } from "../api/client";
import type { ActionResult, GameState } from "../api/types";
import { GameFrame, type FrameProps } from "../components/GameFrame";
import { Icon } from "../components/Icon";

type Upload =
  | { kind: "idle" } | { kind: "uploading"; progress: number } | { kind: "saved" }
  | { kind: "failed"; reason: "network" | "too_large" | "unsupported" };

const FAILED_TITLE = {
  network: "Upload failed – check your connection",
  too_large: "This photo is larger than 20 MB",
  unsupported: "This file isn't a photo we can save",
} as const;

const MAX_PHOTO_BYTES = 20 * 1024 * 1024;     // same limit as the server (413); checked first to spare a weak signal

export function PhotoScreen({ state, frame, upload: uploadFile, onFlowStart, onUploaded, onContinue, onError }: {
  state: GameState; frame: FrameProps;
  /** Sends the photo for the current position; GameApp wires it to `game.track(api.uploadPhoto(...))`. */
  upload(file: File, onProgress: (pct: number) => void): Promise<ActionResult>;
  onFlowStart(): void; onUploaded(result: ActionResult): void; onContinue(): void;
  /** `game.fail`: LinkNotValid → invalid view; network/5xx → banner + retry. */
  onError(err: unknown): void;
}) {
  const task = state.task!;
  const landmarkName = task.landmark?.name ?? "the landmark";
  const [pending, setPending] = useState<File | null>(null);      // kept until saved (R-23)
  const [upload, setUpload] = useState<Upload>(task.photo_count > 0 ? { kind: "saved" } : { kind: "idle" });
  const camera = useRef<HTMLInputElement>(null);
  const gallery = useRef<HTMLInputElement>(null);

  async function send(file: File) {
    onFlowStart();
    setUpload({ kind: "uploading", progress: 0 });
    try {
      const result = await uploadFile(file, (progress) => setUpload({ kind: "uploading", progress }));
      setPending(null);
      onUploaded(result);
      setUpload(result.outcome === "ok" ? { kind: "saved" } : { kind: "idle" });
    } catch (err) {
      if (err instanceof HttpError && err.status === 413) { setPending(null); setUpload({ kind: "failed", reason: "too_large" }); return; }
      if (err instanceof HttpError && err.status === 415) { setPending(null); setUpload({ kind: "failed", reason: "unsupported" }); return; }
      if (isConnectionProblem(err)) setUpload({ kind: "failed", reason: "network" });   // file kept for Retry
      else setUpload({ kind: "idle" });              // e.g. link no longer valid: GameApp swaps the screen
      onError(err);
    }
  }

  function picked(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";                                  // allow choosing the same file again
    if (!file) return;
    if (file.size > MAX_PHOTO_BYTES) { setUpload({ kind: "failed", reason: "too_large" }); return; }
    setPending(file);
    void send(file);
  }

  const count = task.photo_count;
  const canContinue = count > 0 && upload.kind !== "uploading";
  const locked = (label: string) => (
    <button type="button" className="qc-btn qc-btn--locked qc-btn--block" disabled><Icon name="lock" />{label}</button>
  );

  return (
    <GameFrame frame={frame} mainClassName="qs-main qs-main--top" actions={
      <div className="qs-actions">
        <input ref={camera} className="qs-file-input" type="file" accept="image/*" capture="environment" onChange={picked} aria-hidden="true" tabIndex={-1} />
        <input ref={gallery} className="qs-file-input" type="file" accept="image/*" onChange={picked} aria-hidden="true" tabIndex={-1} />
        {upload.kind === "idle" && <>
          <button type="button" className="qc-btn qc-btn--primary qc-btn--block" onClick={() => camera.current?.click()}><Icon name="camera" />Take a photo</button>
          <button type="button" className="qc-btn qc-btn--secondary qc-btn--block" onClick={() => gallery.current?.click()}><Icon name="gallery" />Choose from gallery</button>
          {canContinue ? <ContinueButton onClick={onContinue} /> : locked("Continue · add a photo first")}
        </>}
        {upload.kind === "uploading" && locked("Continue · waiting for upload")}
        {upload.kind === "saved" && <>
          <button type="button" className="qc-btn qc-btn--secondary qc-btn--block" onClick={() => gallery.current?.click()}><Icon name="camera" />Add another photo</button>
          <ContinueButton onClick={onContinue} />
        </>}
        {upload.kind === "failed" && (canContinue ? <ContinueButton onClick={onContinue} /> : locked("Continue · save a photo first"))}
      </div>
    }>
      <div className="qs-group" style={{ gap: 8 }}>
        <p className="qs-eyebrow"><Icon name="camera" />Photo stop</p>
        <h1 className="t-title">Take a photo of your team at {landmarkName}.</h1>
        <p className="t-body">Get everyone in the shot. You can add more than one photo.</p>
      </div>
      {upload.kind === "idle" && (
        <div className="qc-photo"><div className="qc-photo__icon"><Icon name="camera" /></div>
          <div className="qc-photo__text"><span className="qc-photo__title">No photo yet</span>
            <span className="qc-photo__meta">Take one or choose from your gallery</span></div></div>
      )}
      {upload.kind === "uploading" && (
        <div className="qc-photo" role="status"><div className="qc-photo__icon"><Icon name="camera" /></div>
          <div className="qc-photo__text"><span className="qc-photo__title">Uploading 1 photo… {upload.progress}%</span>
            <div className="qc-photo__bar" role="progressbar" aria-label="Upload progress" aria-valuenow={upload.progress}
                 aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${upload.progress}%` }} /></div>
            <span className="qc-photo__meta">Keep this screen open</span></div></div>
      )}
      {upload.kind === "saved" && (
        <div className="qc-photo qc-photo--saved" role="status"><div className="qc-photo__icon"><Icon name="check" /></div>
          <div className="qc-photo__text"><span className="qc-photo__title">Photo saved ✓</span>
            <span className="qc-photo__meta">{count} photo{count === 1 ? "" : "s"} ready for the album</span></div></div>
      )}
      {upload.kind === "failed" && (
        <div className="qc-photo qc-photo--failed" role="alert" style={{ flexWrap: "wrap" }}>
          <div className="qc-photo__icon"><Icon name="error" /></div>
          <div className="qc-photo__text"><span className="qc-photo__title">{FAILED_TITLE[upload.reason]}</span>
            <span className="qc-photo__meta" style={{ color: "var(--theatre-800)" }}>
              {upload.reason === "network" ? "Your photo is kept. No need to take it again." : "Please choose another photo (JPEG, PNG, HEIC or WebP, up to 20 MB)."}
            </span></div>
          {upload.reason === "network" && pending
            ? <button type="button" className="qc-btn qc-btn--secondary qc-btn--block" onClick={() => void send(pending)}><Icon name="retry" />Retry</button>
            : <button type="button" className="qc-btn qc-btn--secondary qc-btn--block" onClick={() => gallery.current?.click()}><Icon name="gallery" />Choose another photo</button>}
        </div>
      )}
      <div className="qs-note"><Icon name="shield" />
        <p className="t-body">Photos go straight to your host for a surprise album, so you won't see them here.</p></div>
    </GameFrame>
  );
}

function ContinueButton({ onClick }: { onClick(): void }) {
  return <button type="button" className="qc-btn qc-btn--primary qc-btn--block" onClick={onClick}>Continue<Icon name="arrow" /></button>;
}
