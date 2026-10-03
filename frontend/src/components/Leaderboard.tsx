import type { LeaderboardRow } from "../api/types";
import { formatHms } from "../lib/format";

export function Leaderboard({ rows, gameName }: { rows: LeaderboardRow[]; gameName: string }) {
  return (
    <section className="qs-group" aria-labelledby="board-title">
      <div className="qs-group-head">
        <h2 className="t-title" id="board-title">Leaderboard</h2>
        <p className="t-caption">Teams that finished {gameName}</p>
      </div>
      {rows.length === 0 ? <p className="t-body t-muted">No team has finished yet.</p> : (
        <table className="qc-board">
          <thead><tr><th>#</th><th>Team</th><th>Time</th><th style={{ textAlign: "right" }}>Hints</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.rank}-${row.team_name}`} className={row.is_you ? "is-you" : undefined}>
                <td>{row.rank}</td>
                <td className="qc-board__team">{row.team_name}{row.is_you && <span className="qc-you">You</span>}</td>
                <td className="qc-board__time">{formatHms(row.total_seconds)}</td>
                <td>{row.hints_used}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
