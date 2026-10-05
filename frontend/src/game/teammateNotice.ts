import type { GameState } from "../api/types";

export function teammateNotice(prev: GameState, next: GameState): string | null {
  if (prev.status !== "not_started" && next.status === "not_started") return "The test run was reset";
  if (prev.status === "not_started" && next.status !== "not_started") return "A teammate started the quest";
  if (prev.status === "timed_out" || next.status === "timed_out") return null;
  if (next.position > prev.position) {
    return next.phase === "results" ? "A teammate opened the results" : "A teammate moved on to the next riddle";
  }
  if (next.position !== prev.position || !prev.task || !next.task) return null;
  if (prev.phase === "task" && next.phase !== "task") {
    return next.task.completion === "revealed" ? "A teammate revealed the answer" : "A teammate solved this task";
  }
  if (prev.phase === "photo" && next.phase === "info") return "A teammate saved a photo";
  if (prev.phase === "task" && next.phase === "task") {
    const opened = next.task.hints.find((h) => h.opened && !prev.task!.hints.find((p) => p.number === h.number)?.opened);
    if (opened) return `A teammate opened hint ${opened.number}`;
  }
  return null;
}
