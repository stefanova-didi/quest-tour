import type { LinkNotValidInfo } from "../api/types";
import { Icon } from "../components/Icon";
import { formatDateLong, formatDateWeekday, formatTime } from "../lib/format";

export function LinkNotValidScreen({ info }: { info: LinkNotValidInfo }) {
  const tz = info.time_zone ?? "UTC";
  const notYet = info.reason === "not_yet";
  return (
    <div className="qs">
      <main className="qs-main qs-main--center">
        <div className={notYet ? "qs-sign qs-sign--gold" : "qs-sign qs-sign--red"}>
          <Icon name={notYet ? "calendar" : "brokenLink"} />
        </div>
        <div className="qs-center-copy">
          <h1 className="t-title">{notYet ? "This game link isn't active yet" : "This game link isn't active"}</h1>
          <p className="t-body">
            {notYet ? "Come back when it opens – you won't need a new link." : "Please contact your host for a valid link."}
          </p>
        </div>
        {info.reason === "expired" && info.expired_at && (
          <p className="t-caption">
            This link expired on {formatDateLong(new Date(Date.parse(info.expired_at) - 1000).toISOString(), tz)}.
          </p>
        )}
        {notYet && info.opens_at && (
          <div className="qs-card qs-opens-card">
            <span className="t-caption" style={{ color: "var(--gold-700)", fontWeight: 700 }}>Opens on</span>
            <span className="t-title">{formatDateWeekday(info.opens_at, tz)}</span>
            <span className="t-timer">{formatTime(info.opens_at, tz)}</span>
          </div>
        )}
        {notYet && <p className="t-caption">Questions? Contact your host.</p>}
      </main>
    </div>
  );
}
