import { useEffect, useState } from "react";

export type FieldType = "text" | "textarea" | "number" | "list";

export interface FieldDef {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  placeholder?: string;
  rows?: number;
}

interface EntityFormProps<T> {
  fields: FieldDef[];
  initial: T;
  onSubmit: (data: T) => void | Promise<void>;
  onDirtyChange?: (dirty: boolean) => void;
  errors?: { field: string; message: string }[];
  submitLabel?: string;
  busy?: boolean;
}

function valuesEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a == null || b == null) return a === b;
  if (Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((v, i) => valuesEqual(v, b[i]));
  }
  if (typeof a === "object" && typeof b === "object") {
    const aKeys = Object.keys(a);
    const bKeys = Object.keys(b);
    if (aKeys.length !== bKeys.length) return false;
    return aKeys.every((key) =>
      valuesEqual(
        (a as Record<string, unknown>)[key],
        (b as Record<string, unknown>)[key],
      ),
    );
  }
  return false;
}

function isEmptyValue(value: unknown, type: FieldType): boolean {
  if (value === undefined || value === null) return true;
  if (type === "list") return Array.isArray(value) && value.length === 0;
  if (type === "number") return value === "" || Number.isNaN(Number(value));
  return String(value).trim() === "";
}

export function EntityForm<T extends Record<string, unknown>>({
  fields,
  initial,
  onSubmit,
  onDirtyChange,
  errors,
  submitLabel = "Save",
  busy = false,
}: EntityFormProps<T>) {
  const [values, setValues] = useState<T>(initial);
  const [localErrors, setLocalErrors] = useState<{ field: string; message: string }[]>([]);

  useEffect(() => {
    setValues(initial);
    setLocalErrors([]);
  }, [initial]);

  const dirty = !valuesEqual(values, initial);

  useEffect(() => {
    onDirtyChange?.(dirty);
  }, [dirty, onDirtyChange]);

  const setField = (name: keyof T, value: unknown) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const validate = (next: T) => {
    const nextErrors: { field: string; message: string }[] = [];
    for (const field of fields) {
      if (field.required && isEmptyValue(next[field.name], field.type)) {
        nextErrors.push({ field: field.name, message: `${field.label} is required` });
      }
    }
    return nextErrors;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    const nextErrors = validate(values);
    setLocalErrors(nextErrors);
    if (nextErrors.length === 0) {
      onSubmit(values);
    }
  };

  const fieldErrors = (name: string) =>
    [...(errors ?? []), ...localErrors].filter((err) => err.field === name) ?? [];

  return (
    <form onSubmit={handleSubmit} className="admin-form">
      {fields.map((field) => {
        const errorsForField = fieldErrors(field.name);
        const hasErrors = errorsForField.length > 0;
        return (
          <div
            key={field.name}
            className={`qc-field ${hasErrors ? "qc-field--error" : ""}`}
          >
            <label className="qc-field__label" htmlFor={`field-${field.name}`}>
              {field.label}
            </label>
            {field.type === "text" && (
              <input
                id={`field-${field.name}`}
                className="qc-input"
                type="text"
                value={String(values[field.name] ?? "")}
                onChange={(e) => setField(field.name, e.target.value)}
                aria-required={field.required ? "true" : undefined}
                aria-invalid={hasErrors ? "true" : undefined}
                placeholder={field.placeholder}
              />
            )}
            {field.type === "textarea" && (
              <textarea
                id={`field-${field.name}`}
                className="qc-input"
                value={String(values[field.name] ?? "")}
                onChange={(e) => setField(field.name, e.target.value)}
                aria-required={field.required ? "true" : undefined}
                aria-invalid={hasErrors ? "true" : undefined}
                placeholder={field.placeholder}
                rows={field.rows ?? 4}
              />
            )}
            {field.type === "number" && (
              <input
                id={`field-${field.name}`}
                className="qc-input"
                type="number"
                value={String(values[field.name] ?? "")}
                onChange={(e) => setField(field.name, Number(e.target.value))}
                aria-required={field.required ? "true" : undefined}
                aria-invalid={hasErrors ? "true" : undefined}
                placeholder={field.placeholder}
              />
            )}
            {field.type === "list" && (
              <ListField
                values={(values[field.name] as string[] | undefined) ?? []}
                onChange={(items) => setField(field.name, items)}
                label={field.label}
              />
            )}
            {errorsForField.map((err) => (
              <p key={err.message} className="qc-field__error">
                {err.message}
              </p>
            ))}
          </div>
        );
      })}
      <button className="qc-btn qc-btn--primary" type="submit" disabled={busy}>
        {submitLabel}
      </button>
    </form>
  );
}

function ListField({
  values,
  onChange,
  label,
}: {
  values: string[];
  onChange: (values: string[]) => void;
  label: string;
}) {
  const update = (index: number, value: string) => {
    const next = [...values];
    next[index] = value;
    onChange(next);
  };

  const remove = (index: number) => {
    const next = values.filter((_, i) => i !== index);
    onChange(next);
  };

  const add = () => {
    onChange([...values, ""]);
  };

  return (
    <div className="admin-list-field">
      {values.map((value, index) => (
        <div key={index} className="admin-list-row">
          <input
            className="qc-input"
            type="text"
            value={value}
            onChange={(e) => update(index, e.target.value)}
            aria-label={`${label} ${index + 1}`}
          />
          <button
            type="button"
            className="qc-btn qc-btn--secondary"
            onClick={() => remove(index)}
          >
            Remove
          </button>
        </div>
      ))}
      <button type="button" className="qc-btn qc-btn--secondary" onClick={add}>
        Add {label}
      </button>
    </div>
  );
}
