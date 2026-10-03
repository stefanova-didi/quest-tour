import type { GameState } from "../api/types";
import { HourglassArt } from "../components/art";
import { ConnectionBanner } from "../components/ConnectionBanner";
import type { FrameProps } from "../components/GameFrame";
import { Icon } from "../components/Icon";
import { Leaderboard } from "../components/Leaderboard";
import { Paragraphs } from "../components/Paragraphs";
import { Toast } from "../components/Toast";
import { formatLimit } from "../lib/format";

export function TimesUpScreen({ state, frame }: { state: GameState; frame: FrameProps }) {
  const results = state.results!;
  const { game, team } = state;
  const done = results.tasks_completed;
  return (
    <div className="qs">
      {frame.offline && <ConnectionBanner />}
      <div className="qs-scroll">
        <section className="qs-curtain">
          <HourglassArt />
          <h1 className="t-display-xl">Time's up!</h1>
          <p className="t-body" style={{ maxWidth: 270 }}>
            {results.end_reason === "window_closed"
              ? "Thanks for playing. The time window for this game has closed."
              : `Thanks for playing. The ${formatLimit(game.max_duration_minutes)} limit for this game has been reached.`}
          </p>
        </section>
        <main className="qs-main">
          <section className="qs-card" aria-labelledby="done-label">
            <p className="t-caption" id="done-label">Tasks completed</p>
            <p className="t-timer-xl" style={{ margin: 0 }}>{done} of {game.task_count}</p>
            <div className="qc-progress qs-progress--light" role="progressbar" aria-label="Tasks completed"
                 aria-valuenow={done} aria-valuemin={0} aria-valuemax={game.task_count}>
              <span style={{ width: `${(done / game.task_count) * 100}%` }} />
            </div>
            <p className="t-body">Only teams that complete every task are ranked, so {team.name} aren't on the leaderboard this time.</p>
          </section>
          <Leaderboard rows={results.leaderboard} gameName={game.name} />
          <section className="qs-card qs-host-card" aria-labelledby="host-label">
            <p className="qs-eyebrow" id="host-label" style={{ color: "var(--patina-800)" }}><Icon name="gift" />From your host</p>
            <Paragraphs text={results.exit_message} />
          </section>
        </main>
      </div>
      {frame.notice && <Toast message={frame.notice} onDone={frame.onNoticeDone} />}
    </div>
  );
}
