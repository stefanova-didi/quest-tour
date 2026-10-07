import { useEffect, useState } from "react";
import { adminApi, getServerReference, isServerError } from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import type { Game, Team, TeamPhotoOut } from "../types";

export function PhotosScreen() {
  const [photos, setPhotos] = useState<TeamPhotoOut[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [teamId, setTeamId] = useState<string>("");
  const [gameId, setGameId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const load = () => {
    setLoading(true);
    Promise.all([
      adminApi.teams(),
      adminApi.games(),
      adminApi.listTeamPhotos(teamId ? Number(teamId) : undefined, gameId ? Number(gameId) : undefined),
    ])
      .then(([t, g, p]) => {
        setTeams(t);
        setGames(g);
        setPhotos(p);
      })
      .catch((err) => {
        if (isServerError(err)) {
          setServerError(getServerReference(err) ?? "Server error");
        } else {
          setError("Could not load photos.");
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleFilter = () => {
    load();
  };

  const handleDelete = async (id: number) => {
    setBusy(true);
    try {
      await adminApi.deleteTeamPhoto(id);
      setDeleteId(null);
      load();
    } catch (err) {
      if (isServerError(err)) {
        setServerError(getServerReference(err) ?? "Server error");
      } else {
        setError("Could not delete photo.");
      }
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="admin-section">
        <h1 className="t-title">Photos</h1>
        <p className="t-body">Loading…</p>
      </div>
    );
  }

  return (
    <div className="admin-section">
      <h1 className="t-title">Photos</h1>
      {error && <p className="qc-field__error">{error}</p>}
      {serverError && <p className="qc-field__error">Server reference: {serverError}</p>}
      <div className="admin-filters">
        <label className="qc-field">
          <span className="qc-field__label">Team</span>
          <select
            className="qc-input"
            value={teamId}
            onChange={(e) => setTeamId(e.target.value)}
            aria-label="Team"
          >
            <option value="">All teams</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <label className="qc-field">
          <span className="qc-field__label">Game</span>
          <select
            className="qc-input"
            value={gameId}
            onChange={(e) => setGameId(e.target.value)}
            aria-label="Game"
          >
            <option value="">All games</option>
            {games.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </label>
        <button className="qc-btn qc-btn--secondary" type="button" onClick={handleFilter}>
          Filter
        </button>
      </div>
      {photos.length === 0 ? (
        <p className="t-body">No photos yet.</p>
      ) : (
        <ul className="admin-list">
          {photos.map((p) => (
            <li key={p.id} className="admin-list-item">
              <div>
                <strong className="t-body">{p.team_name}</strong>
                <span className="t-caption"> — {p.game_name}</span>
                <span className="t-caption"> at {new Date(p.uploaded_at).toLocaleString()}</span>
                <div>
                  <a className="t-body" href={p.url} target="_blank" rel="noreferrer">
                    View photo
                  </a>
                </div>
              </div>
              <div className="admin-row-actions">
                <button
                  className="qc-btn qc-btn--danger"
                  type="button"
                  onClick={() => setDeleteId(p.id)}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {deleteId !== null && (
        <ConfirmDialog
          title="Delete photo"
          body="This cannot be undone."
          confirmLabel="Delete"
          danger
          busy={busy}
          onConfirm={() => handleDelete(deleteId)}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </div>
  );
}
