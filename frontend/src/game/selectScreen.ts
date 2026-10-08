import type { GameState } from "../api/types";

export type Screen = "cover" | "welcome" | "task" | "correct" | "revealed" | "photo" | "landmark" | "finish" | "timesup";
export interface LocalUi { coverSeen: boolean; ackedPosition: number | null; photoFlowPosition: number | null; }
export const EMPTY_UI: LocalUi = { coverSeen: false, ackedPosition: null, photoFlowPosition: null };

export function selectScreen(state: GameState, ui: LocalUi): Screen {
  if (state.status === "not_started") return ui.coverSeen ? "welcome" : "cover";   // the cover is one tap, once per page load
  if (state.status === "timed_out") return "timesup";
  if (state.phase === "results" || state.task === null) return "finish";
  if (state.phase === "task") return "task";
  if (state.phase === "photo") {
    if (ui.ackedPosition === state.position || ui.photoFlowPosition === state.position) return "photo";
    return state.task.completion === "revealed" ? "revealed" : "correct";
  }
  return ui.photoFlowPosition === state.position ? "photo" : "landmark";
}
