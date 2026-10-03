import { Icon } from "./Icon";

export function ConnectionBanner() {
  return (
    <div className="qc-banner" role="status" style={{ flex: "none" }}>
      <Icon name="wifiOff" />
      <span>No connection – retrying…</span>
      <span className="qc-banner__dots" aria-hidden="true"><i /><i /><i /></span>
    </div>
  );
}
