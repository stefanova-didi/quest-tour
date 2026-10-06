import { useState, type FormEvent } from "react";
import type { GameState, Hint } from "../api/types";
import type { ActOutcome } from "../game/useGame";
import { CompassDisplay } from "../components/CompassDisplay";
import { ConfirmSheet } from "../components/ConfirmSheet";
import { GameFrame, type FrameProps } from "../components/GameFrame";
import { Icon } from "../components/Icon";
import { formatPenalty } from "../lib/format";
import { useNow } from "../lib/useNow";

type Pending = { kind: "hint"; hint: Hint } | { kind: "reveal" } | { kind: "compass" } | null;
type Act = Promise<ActOutcome>;

export function TaskScreen({ state, receivedAt, frame, onAnswer, onHint, onReveal, onCompass }: {
  state: GameState; receivedAt: number; frame: FrameProps;
  onAnswer(answer: string): Act; onHint(hint: 1 | 2): Act; onReveal(): Act; onCompass(): Act;
}) {
  const task = state.task!;
  const game = state.game;
  const compass = task.compass;
  const [answer, setAnswer] = useState("");
  const [wrong, setWrong] = useState(false);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<Pending>(null);
  const now = useNow(task.reveal_unlocked || task.reveal_unlocks_in_seconds === null ? null : 1000);
  const revealOpen = task.reveal_unlocked ||
    (task.reveal_unlocks_in_seconds !== null && (now - receivedAt) / 1000 >= task.reveal_unlocks_in_seconds);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy || answer.trim() === "") return;
    setBusy(true);
    const outcome = await onAnswer(answer);
    setBusy(false);
    setWrong(outcome === "wrong");        // input keeps its text (TaskWrong, TaskOffline)
  }

  async function confirm() {
    if (!pending) return;
    setBusy(true);
    try {
      if (pending.kind === "hint") {
        await onHint(pending.hint.number);
      } else if (pending.kind === "compass") {
        // iOS requires DeviceOrientation permission from a user gesture; the confirm button is it.
        const DOE = window.DeviceOrientationEvent as unknown as { requestPermission?: () => Promise<string> };
        if (DOE?.requestPermission) {
          try { await DOE.requestPermission(); } catch { /* denied/unsupported: proceed with static bearing fallback */ }
        }
        await onCompass();
      } else {
        await onReveal();
      }
    } finally {
      setBusy(false);
      setPending(null);
    }
  }

  const riddle = (
    <>
      <p className="qs-eyebrow"><Icon name="riddle" />Riddle</p>
      <p className="t-riddle">{task.text}</p>
    </>
  );

  return (
    <GameFrame
      frame={frame}
      toastHigh
      mainClassName={task.picture_url ? "qs-main" : "qs-main qs-main--top-lg"}
      actions={
        <form className="qs-actions" onSubmit={submit}>
          <div className={wrong ? "qc-field qc-field--error" : "qc-field"}>
            <label className="qc-field__label" htmlFor="answer">Your answer</label>
            <input className="qc-input" id="answer" placeholder="Type the landmark's name" autoComplete="off" maxLength={500}
                   autoCapitalize="off" spellCheck={false} value={answer} aria-invalid={wrong || undefined}
                   aria-describedby={wrong ? "answer-error" : undefined}
                   onChange={(e) => { setAnswer(e.target.value); setWrong(false); }} />
            {wrong && (
              <div className="qc-field__error" id="answer-error" role="status"><Icon name="error" />Not quite – try again</div>
            )}
          </div>
          <button type="submit" className="qc-btn qc-btn--primary qc-btn--block" disabled={busy}>Submit</button>
        </form>
      }
      overlay={pending && (
        (() => {
          const sheetProps =
            pending.kind === "hint"
              ? { title: `Open hint ${pending.hint.number}?`, confirmLabel: "Open hint",
                  body: <>This adds <span className="qc-tag">{formatPenalty(pending.hint.penalty_minutes)}</span> to your time.</> }
              : pending.kind === "compass"
              ? { title: "Open compass?", confirmLabel: "Open compass",
                  body: <>This adds <span className="qc-tag">{formatPenalty(compass!.penalty_minutes)}</span> to your time.</> }
              : { title: "Give up and reveal the answer?", confirmLabel: "Reveal", danger: true,
                  body: <>This adds <span className="qc-tag">{formatPenalty(game.reveal_penalty_minutes)}</span> to your time. You'll still visit the landmark and take your photo.</> };
          return (
            <ConfirmSheet
              busy={busy} onCancel={() => setPending(null)} onConfirm={confirm}
              {...sheetProps}
            />
          );
        })()
      )}
    >
      {task.picture_url
        ? <><img className="qs-pic" src={task.picture_url} alt="Task picture" /><div className="qs-group" style={{ gap: 8 }}>{riddle}</div></>
        : <div className="qs-card qs-riddle-card">{riddle}</div>}
      <div className="qs-group">
        {task.hints.length > 0 && (
          <div className="qs-group-head"><h2 className="t-label">Need help?</h2><p className="t-caption">Hints add time to your total.</p></div>
        )}
        {task.hints.map((hint) =>
          hint.opened ? (
            <div className="qc-hint" key={hint.number}>
              <div className="qc-hint__head"><span>Hint {hint.number}</span><span>{formatPenalty(hint.penalty_minutes)} added</span></div>
              <p className="qc-hint__text">{hint.text}</p>
            </div>
          ) : hint.available ? (
            <button type="button" className="qc-hint-btn" key={hint.number} onClick={() => setPending({ kind: "hint", hint })}>
              <span>Hint {hint.number}</span><span className="qc-tag">{formatPenalty(hint.penalty_minutes)}</span>
            </button>
          ) : (
            <button type="button" className="qc-hint-btn" key={hint.number} disabled>
              <span className="qs-inline-icon"><Icon name="lock" size={18} />Hint {hint.number}</span>
              <span className="qs-hint-meta">after hint 1 · {formatPenalty(hint.penalty_minutes)}</span>
            </button>
          ))}
        {compass && (
          compass.opened ? (
            <CompassDisplay key="compass" lat={compass.lat} lon={compass.lon} />
          ) : (
            <button type="button" className="qc-hint-btn" onClick={() => setPending({ kind: "compass" })}>
              <span className="qs-inline-icon"><Icon name="compass" size={18} />Compass</span>
              <span className="qc-tag">{formatPenalty(compass.penalty_minutes)}</span>
            </button>
          )
        )}
        {revealOpen ? (
          <button type="button" className="qc-hint-btn" onClick={() => setPending({ kind: "reveal" })}>
            <span className="qs-inline-icon"><Icon name="flag" size={18} />Give up and reveal answer</span>
            <span className="qc-tag">{formatPenalty(game.reveal_penalty_minutes)}</span>
          </button>
        ) : (
          <button type="button" className="qc-hint-btn qs-hint-btn--two-line" disabled>
            <span className="qs-reveal-locked">
              <span className="qs-inline-icon"><Icon name="lock" size={18} />Reveal answer</span>
              <span className="qs-hint-meta">Unlocks after {game.reveal_after_attempts} tries or {game.reveal_after_minutes} min</span>
            </span>
            <span className="qs-hint-meta">{formatPenalty(game.reveal_penalty_minutes)}</span>
          </button>
        )}
      </div>
    </GameFrame>
  );
}
