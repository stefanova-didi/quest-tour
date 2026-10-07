import { ConfirmSheet } from "../../components/ConfirmSheet";

interface ConfirmDialogProps {
  title: string;
  body: string;
  confirmLabel: string;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  title,
  body,
  confirmLabel,
  danger = false,
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <ConfirmSheet
      title={title}
      body={body}
      confirmLabel={confirmLabel}
      danger={danger}
      busy={busy}
      onConfirm={onConfirm}
      onCancel={onCancel}
    />
  );
}
