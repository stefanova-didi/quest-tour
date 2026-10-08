import { useState } from "react";
import type { GameState } from "../api/types";
import type { ActOutcome } from "../game/useGame";
import { GameFrame, type FrameProps } from "../components/GameFrame";
import { Icon } from "../components/Icon";
import { Paragraphs } from "../components/Paragraphs";
import { pickText } from "../lib/i18n";

export function LandmarkScreen({ state, frame, language, onNext }: {
  state: GameState; frame: FrameProps; language: string; onNext(): Promise<ActOutcome>;
}) {
  const landmark = state.task!.landmark!;
  const { task_count: count } = state.game;
  const last = state.position + 1 >= count;
  const [busy, setBusy] = useState(false);
  const [pictureFailed, setPictureFailed] = useState(false);
  const landmarkName = pickText(landmark.name, landmark.name_i18n, language);
  const touristInfo = pickText(landmark.info, landmark.info_i18n, language);

  async function next() {
    setBusy(true);
    await onNext();
    setBusy(false);
  }

  return (
    <GameFrame
      frame={frame}
      mainClassName={last ? "qs-main qs-main--end" : "qs-main"}
      actions={
        <div className="qs-actions">
          <button type="button" className="qc-btn qc-btn--primary qc-btn--block" disabled={busy} onClick={next}>
            {last ? <><Icon name="flag" />See results</> : <>Next riddle<Icon name="arrow" /></>}
          </button>
        </div>
      }
    >
      {landmark.picture_url && (pictureFailed
        ? <div className="qs-pic qs-pic--placeholder">{landmarkName}</div>
        : <img className="qs-pic" src={landmark.picture_url} alt={`Picture of ${landmarkName}`} onError={() => setPictureFailed(true)} />)}
      <article className="qs-card">
        <div style={{ display: "grid", gap: 4 }}>
          <p className="qs-eyebrow">Landmark {state.position + 1} of {count}</p>
          <h1 className="t-display-l">{landmarkName}</h1>
        </div>
        <Paragraphs text={touristInfo} />
      </article>
      {last && (
        <div className="qs-card qs-host-card qs-last-card">
          <Icon name="trophy" size={32} />
          <div style={{ display: "grid", gap: 2 }}>
            <p className="t-label" style={{ color: "var(--patina-800)" }}>That was the last landmark!</p>
            <p className="t-body">See your total time and where your team placed.</p>
          </div>
        </div>
      )}
    </GameFrame>
  );
}
