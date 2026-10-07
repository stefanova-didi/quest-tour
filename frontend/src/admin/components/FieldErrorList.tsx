interface FieldErrorListProps {
  errors: { field: string; message: string }[];
}

export function FieldErrorList({ errors }: FieldErrorListProps) {
  if (!errors.length) return null;
  return (
    <div className="admin-errors">
      {errors.map((err, index) => (
        <p key={index} className="qc-field__error">
          {err.field}: {err.message}
        </p>
      ))}
    </div>
  );
}
