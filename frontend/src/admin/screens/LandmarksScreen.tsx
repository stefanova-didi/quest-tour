import { useEffect, useMemo, useState } from "react";
import { adminApi, getServerReference, isConflictError, isServerError, isValidationError, normalizeField } from "../api";
import type { AdminValidationError } from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EntityForm } from "../components/EntityForm";
import { FieldErrorList } from "../components/FieldErrorList";
import type { Landmark, LandmarkInput } from "../types";

type LandmarkForm = {
  key: string;
  name: string;
  name_i18n: Record<string, string>;
  task: string;
  task_i18n: Record<string, string>;
  accepted_answers: string[];
  hint1: string;
  hint1_i18n: Record<string, string>;
  hint2: string;
  hint2_i18n: Record<string, string>;
  tourist_info: string;
  tourist_info_i18n: Record<string, string>;
  lat: string;
  lon: string;
};

const LANDMARK_FIELDS = [
  { name: "key", label: "Key", type: "text" as const, required: true },
  { name: "name", i18nName: "name_i18n", label: "Name", type: "i18n-text" as const, required: true },
  { name: "task", i18nName: "task_i18n", label: "Task", type: "i18n-textarea" as const, required: true, rows: 5 },
  { name: "accepted_answers", label: "Accepted answers", type: "list" as const },
  { name: "hint1", i18nName: "hint1_i18n", label: "Hint 1", type: "i18n-text" as const },
  { name: "hint2", i18nName: "hint2_i18n", label: "Hint 2", type: "i18n-text" as const },
  { name: "tourist_info", i18nName: "tourist_info_i18n", label: "Tourist info", type: "i18n-textarea" as const, rows: 5 },
  { name: "lat", label: "Latitude", type: "text" as const },
  { name: "lon", label: "Longitude", type: "text" as const },
];

function emptyForm(): LandmarkForm {
  return {
    key: "",
    name: "",
    name_i18n: {},
    task: "",
    task_i18n: {},
    accepted_answers: [],
    hint1: "",
    hint1_i18n: {},
    hint2: "",
    hint2_i18n: {},
    tourist_info: "",
    tourist_info_i18n: {},
    lat: "",
    lon: "",
  };
}

function landmarkToForm(lm: Landmark): LandmarkForm {
  return {
    key: lm.key,
    name: lm.name,
    name_i18n: lm.name_i18n ?? {},
    task: lm.task,
    task_i18n: lm.task_i18n ?? {},
    accepted_answers: lm.accepted_answers,
    hint1: lm.hint1 ?? "",
    hint1_i18n: lm.hint1_i18n ?? {},
    hint2: lm.hint2 ?? "",
    hint2_i18n: lm.hint2_i18n ?? {},
    tourist_info: lm.tourist_info,
    tourist_info_i18n: lm.tourist_info_i18n ?? {},
    lat: lm.coordinates?.lat.toString() ?? "",
    lon: lm.coordinates?.lon.toString() ?? "",
  };
}

function stripBlankEntries(map: Record<string, string>): Record<string, string> {
  return Object.fromEntries(Object.entries(map).filter(([, v]) => v.trim() !== ""));
}

function formToLandmark(form: LandmarkForm): LandmarkInput {
  const lat = form.lat.trim() === "" ? null : Number(form.lat);
  const lon = form.lon.trim() === "" ? null : Number(form.lon);
  return {
    key: form.key,
    name: form.name,
    name_i18n: stripBlankEntries(form.name_i18n),
    task: form.task,
    task_i18n: stripBlankEntries(form.task_i18n),
    accepted_answers: form.accepted_answers,
    hint1: form.hint1.trim() || null,
    hint1_i18n: stripBlankEntries(form.hint1_i18n),
    hint2: form.hint2.trim() || null,
    hint2_i18n: stripBlankEntries(form.hint2_i18n),
    tourist_info: form.tourist_info,
    tourist_info_i18n: stripBlankEntries(form.tourist_info_i18n),
    coordinates:
      lat !== null && lon !== null && !Number.isNaN(lat) && !Number.isNaN(lon)
        ? { lat, lon }
        : null,
  };
}

function validateCoordinates(form: LandmarkForm): { field: string; message: string }[] {
  const errors: { field: string; message: string }[] = [];
  const lat = form.lat.trim();
  const lon = form.lon.trim();
  if (lat !== "" && Number.isNaN(Number(lat))) {
    errors.push({ field: "lat", message: "Latitude must be a number" });
  }
  if (lon !== "" && Number.isNaN(Number(lon))) {
    errors.push({ field: "lon", message: "Longitude must be a number" });
  }
  return errors;
}

export function LandmarksScreen({ subPath }: { subPath: string }) {
  const [landmarks, setLandmarks] = useState<Landmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Landmark | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<AdminValidationError["errors"]>([]);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [deleteState, setDeleteState] = useState<{ id: number; force: boolean } | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    adminApi
      .landmarks()
      .then(setLandmarks)
      .catch(() => setError("Could not load landmarks."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    const segments = subPath.split("/").filter(Boolean);
    if (segments[0] !== "landmarks") return;
    if (segments[1] === "new") {
      setCreating(true);
      setEditing(null);
    } else if (segments[1]) {
      const id = Number(segments[1]);
      if (!id) return;
      // Defer until the list has loaded so we can find the landmark.
      const target = landmarks.find((lm) => lm.id === id);
      if (target) {
        setEditing(target);
        setCreating(false);
      }
    }
  }, [subPath, landmarks]);

  useEffect(() => {
    if (!dirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  const initial = useMemo(
    () => (editing ? landmarkToForm(editing) : emptyForm()),
    [editing, creating],
  );

  const handleSave = async (form: LandmarkForm) => {
    setError(null);
    setFieldErrors([]);
    setServerError(null);

    if (form.hint2.trim() && !form.hint1.trim()) {
      setFieldErrors([{ field: "hint2", message: "Hint 2 requires Hint 1" }]);
      return;
    }

    const coordErrors = validateCoordinates(form);
    if (coordErrors.length) {
      setFieldErrors(coordErrors);
      return;
    }

    const data = formToLandmark(form);
    setBusy(true);
    try {
      if (editing) {
        await adminApi.updateLandmark(editing.id, { ...data, seen_at: editing.updated_at });
      } else {
        await adminApi.createLandmark(data);
      }
      setEditing(null);
      setCreating(false);
      setDirty(false);
      load();
    } catch (err) {
      if (isValidationError(err)) {
        setFieldErrors(
          (err.body as AdminValidationError).errors.map((e) => ({
            field: normalizeField(e.field),
            message: e.message,
          }))
        );
      } else if (isConflictError(err)) {
        setError("Another admin edited this landmark. Please refresh.");
      } else if (isServerError(err)) {
        setServerError(getServerReference(err) ?? "Server error");
      } else {
        setError("Could not save landmark.");
      }
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (id: number, force = false) => {
    setError(null);
    setBusy(true);
    try {
      await adminApi.deleteLandmark(id, force);
      setDeleteState(null);
      load();
    } catch (err) {
      if (
        !force &&
        isConflictError(err) &&
        err.body &&
        typeof err.body === "object" &&
        "used_by_games" in err.body
      ) {
        setDeleteState({ id, force: true });
      } else {
        setDeleteState(null);
        if (
          isConflictError(err) &&
          err.body &&
          typeof err.body === "object" &&
          "detail" in err.body
        ) {
          setError(`Could not delete landmark: ${(err.body as { detail: string }).detail}`);
        } else {
          setError("Could not delete landmark.");
        }
      }
    } finally {
      setBusy(false);
    }
  };

  const handleFile = async (id: number, kind: "task" | "info", file: File) => {
    try {
      await adminApi.uploadLandmarkPicture(id, kind, file);
      if (editing?.id === id) {
        const updated = await adminApi.landmarks();
        const next = updated.find((lm) => lm.id === id);
        if (next) setEditing(next);
      }
      load();
    } catch {
      setError(`Could not upload ${kind} picture.`);
    }
  };

  if (loading) {
    return (
      <div className="admin-section">
        <h1 className="t-title">Landmarks</h1>
        <p className="t-body">Loading…</p>
      </div>
    );
  }

  if (creating || editing) {
    return (
      <div className="admin-section">
        <h1 className="t-title">{editing ? "Edit landmark" : "New landmark"}</h1>
        {error && <p className="qc-field__error">{error}</p>}
        {serverError && <p className="qc-field__error">Server reference: {serverError}</p>}
        <FieldErrorList errors={fieldErrors} />
        <EntityForm
          fields={LANDMARK_FIELDS}
          initial={initial}
          onSubmit={handleSave}
          onDirtyChange={setDirty}
          submitLabel={editing ? "Update landmark" : "Create landmark"}
          busy={busy}
        />
        {editing && (
          <div className="admin-extra-fields">
            <label className="qc-field">
              <span className="qc-field__label">Task picture</span>
              {editing.task_image_url && (
                <img src={editing.task_image_url} alt="Task" className="admin-thumb" />
              )}
              <input
                className="qc-input"
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFile(editing.id, "task", file);
                }}
                disabled={busy}
              />
            </label>
            <label className="qc-field">
              <span className="qc-field__label">Info picture</span>
              {editing.info_image_url && (
                <img src={editing.info_image_url} alt="Info" className="admin-thumb" />
              )}
              <input
                className="qc-input"
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFile(editing.id, "info", file);
                }}
                disabled={busy}
              />
            </label>
          </div>
        )}
        <div className="admin-actions">
          <button
            className="qc-btn qc-btn--secondary"
            type="button"
            onClick={() => {
              if (dirty && !window.confirm("Discard unsaved changes?")) return;
              setEditing(null);
              setCreating(false);
              setError(null);
              setFieldErrors([]);
              setServerError(null);
            }}
            disabled={busy}
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-section">
      <h1 className="t-title">Landmarks</h1>
      {error && <p className="qc-field__error">{error}</p>}
      <div className="admin-actions">
        <button className="qc-btn qc-btn--primary" type="button" onClick={() => setCreating(true)}>
          New landmark
        </button>
      </div>
      {landmarks.length === 0 ? (
        <p className="t-body">No landmarks yet.</p>
      ) : (
        <ul className="admin-list">
          {landmarks.map((lm) => (
            <li key={lm.id} className="admin-list-item">
              <div>
                <strong className="t-body">{lm.name}</strong>
                <span className="t-caption"> ({lm.key})</span>
              </div>
              <div className="admin-row-actions">
                <button
                  className="qc-btn qc-btn--secondary"
                  type="button"
                  onClick={() => setEditing(lm)}
                >
                  Edit
                </button>
                <button
                  className="qc-btn qc-btn--danger"
                  type="button"
                  onClick={() => setDeleteState({ id: lm.id, force: false })}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {deleteState !== null && (
        <ConfirmDialog
          title={deleteState.force ? "Force delete landmark" : "Delete landmark"}
          body={
            deleteState.force
              ? "This landmark is used by one or more games. Force-deleting will remove it from their task lists. This cannot be undone."
              : "This cannot be undone."
          }
          confirmLabel={deleteState.force ? "Force delete" : "Delete"}
          danger
          busy={busy}
          onConfirm={() => handleDelete(deleteState.id, deleteState.force)}
          onCancel={() => setDeleteState(null)}
        />
      )}
    </div>
  );
}
