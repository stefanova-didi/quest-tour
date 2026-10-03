import type { GameState } from "../api/types";
import { Confetti } from "../components/art";
import { GameFrame, type FrameProps } from "../components/GameFrame";
import { Icon } from "../components/Icon";

export function CorrectScreen({ state, frame, onContinue }: { state: GameState; frame: FrameProps; onContinue(): void }) {
  return (
    <GameFrame
      frame={frame}
      mainClassName="qs-main qs-main--center"
      actions={
        <div className="qs-actions">
          <button type="button" className="qc-btn qc-btn--primary qc-btn--block" onClick={onContinue}>
            <Icon name="camera" />Take a photo, create a memory
          </button>
          <p className="t-caption" style={{ textAlign: "center" }}>A team photo unlocks the next riddle.</p>
        </div>
      }
    >
      <Confetti />
      <div className="qs-badge"><Icon name="check" /></div>
      <h1 className="t-display-xl" style={{ marginTop: 12 }}>Correct!</h1>
      <div style={{ display: "grid", gap: 4 }}>
        <p className="t-body t-muted">You found it:</p>
        <p className="t-display-l">{state.task!.landmark?.name}</p>
      </div>
    </GameFrame>
  );
}
