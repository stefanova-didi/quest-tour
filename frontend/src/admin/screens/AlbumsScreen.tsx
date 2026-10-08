import { useEffect, useState } from "react";
import { adminApi, getServerReference, isServerError } from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import type { AlbumRowOut } from "../types";

const END_REASON: Record<AlbumRowOut["end_reason"], string> = {
  finished: "finished", max_duration: "time ran out", window_closed: "window closed",
};

function formatSize(bytes: number): string {
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.round(bytes / 1024)} KB`;
}

/** The memories albums (issue #33): one PDF per run that has ended. The host can generate it ahead
 *  of the team (or again after deleting a photo), download it, and delete it – after which the
 *  team's link no longer serves it until the host generates it again. */
export function AlbumsScreen() {
  const [rows, setRows] = useState<AlbumRowOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [deleteRow, setDeleteRow] = useState<AlbumRowOut | null>(null);

  const fail = (err: unknown, fallback: string) => {
    if (isServerError(err)) setServerError(getServerReference(err) ?? "Server error");
    else setError(fallback);
  };

  const load = () => {
    setLoading(true);
    adminApi.albums()
      .then(setRows)
      .catch((err) => fail(err, "Could not load albums."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const generate = async (row: AlbumRowOut) => {
    setBusyId(row.assignment_id);
    setError(null);
    try {
      await adminApi.generateAlbum(row.assignment_id);
      load();
    } catch (err) {
      fail(err, "Could not generate the album.");
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (row: AlbumRowOut) => {
    if (!row.album) return;
    setBusyId(row.assignment_id);
    try {
      await adminApi.deleteAlbum(row.album.id);
      setDeleteRow(null);
      load();
    } catch (err) {
      fail(err, "Could not delete the album.");
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <div className="admin-section">
        <h1 className="t-title">Albums</h1>
        <p className="t-body">Loading…</p>
      </div>
    );
  }

  return (
    <div className="admin-section">
      <h1 className="t-title">Albums</h1>
      <p className="t-body">
        Each team's memories album is rendered as a PDF when the team first opens it after the game, and kept here.
        Generate one ahead of time, download it, or delete it: a deleted album is no longer served on the team's link.
      </p>
      {error && <p className="qc-field__error">{error}</p>}
      {serverError && <p className="qc-field__error">Server reference: {serverError}</p>}
      {rows.length === 0 ? (
        <p className="t-body">No run has ended yet.</p>
      ) : (
        <ul className="admin-list">
          {rows.map((row) => {
            const album = row.album;
            const busy = busyId === row.assignment_id;
            const live = album !== null && album.deleted_at === null;
            return (
              <li key={row.assignment_id} className="admin-list-item">
                <div>
                  <strong className="t-body">{row.team_name}</strong>
                  <span className="t-caption"> — {row.game_name}</span>
                  <span className="t-caption"> · {END_REASON[row.end_reason]} {new Date(row.ended_at).toLocaleString()}</span>
                  <span className="t-caption"> · {row.photo_count} photo{row.photo_count === 1 ? "" : "s"}</span>
                  <div className="t-caption">
                    {live && `PDF ${formatSize(album.size_bytes)}, generated ${new Date(album.generated_at).toLocaleString()}`}
                    {album && album.deleted_at !== null && `Album deleted ${new Date(album.deleted_at).toLocaleString()}`}
                    {!album && "No album yet"}
                  </div>
                </div>
                <div className="admin-row-actions">
                  {live && (
                    <a className="qc-btn qc-btn--secondary" href={album.url} target="_blank" rel="noreferrer">Download</a>
                  )}
                  <button className="qc-btn qc-btn--secondary" type="button" disabled={busy} onClick={() => generate(row)}>
                    {live ? "Generate again" : "Generate"}
                  </button>
                  {live && (
                    <button className="qc-btn qc-btn--danger" type="button" disabled={busy} onClick={() => setDeleteRow(row)}>
                      Delete
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {deleteRow && (
        <ConfirmDialog
          title={`Delete the album of ${deleteRow.team_name}?`}
          body="The PDF is removed from storage and the team's link stops serving it. You can generate it again later."
          confirmLabel="Delete"
          danger
          busy={busyId === deleteRow.assignment_id}
          onConfirm={() => remove(deleteRow)}
          onCancel={() => setDeleteRow(null)}
        />
      )}
    </div>
  );
}
