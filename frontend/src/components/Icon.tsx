import type { ReactElement } from "react";

const PATHS = {
  clock: <><circle cx="12" cy="13" r="8" /><path d="M12 9v4l2.5 2M9 2h6" /></>,
  riddle: <><circle cx="8" cy="15" r="4" /><path d="M11 12l9-9M17 6l3 3M15 8l2 2" /></>,
  camera: <><path d="M4 7h3l2-3h6l2 3h3v12H4z" /><circle cx="12" cy="13" r="3.5" /></>,
  lock: <><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></>,
  flag: <path d="M5 21V4M5 4h11l-2 4 2 4H5" />,
  check: <path d="M5 12.5l4.5 4.5L19 7.5" strokeWidth={2.5} />,
  error: <g strokeWidth={2.5}><circle cx="12" cy="12" r="9" /><path d="M9 9l6 6M15 9l-6 6" /></g>,   // mock: stroke-width 2.5 on the whole svg
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  shield: <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" />,
  team: <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 3.5 6" /></>,
  trophy: <path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8 21h8M9 17h6" />,
  gift: <><rect x="4" y="9" width="16" height="12" rx="1" /><path d="M3 9h18M12 9v12M12 9c-1-3-5-4-5-1.5S10.5 9 12 9zM12 9c1-3 5-4 5-1.5S13.5 9 12 9z" /></>,
  gallery: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="2" /><path d="M21 16l-5-5-9 9" /></>,
  retry: <path d="M4 12a8 8 0 0 1 14-5.3L20 9M20 4v5h-5M20 12a8 8 0 0 1-14 5.3L4 15M4 20v-5h5" />,
  wifiOff: <><path d="M2 8.8a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0" /><circle cx="12" cy="19.5" r="1" fill="currentColor" /><path d="M3 3l18 18" /></>,
  list: <path d="M4 6h16M4 12h16M4 18h10" />,
  bulb: <path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z" />,
  brokenLink: <path d="M9 15l6-6M10.5 6.5l1-1a4.5 4.5 0 0 1 6.4 6.4l-1 1M13.5 17.5l-1 1a4.5 4.5 0 0 1-6.4-6.4l1-1M3 3l18 18" />,
  calendar: <><rect x="4" y="5" width="16" height="16" rx="2" /><path d="M4 10h16M9 3v4M15 3v4" /></>,
  compass: <><circle cx="12" cy="12" r="9" /><path d="M15.5 8.5l-2 5-5 2 2-5z" /></>,
} satisfies Record<string, ReactElement>;
export type IconName = keyof typeof PATHS;     // a literal union, so icon-name typos fail `tsc`

export function Icon({ name, size, className }: { name: IconName; size?: number; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth={2}
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={className}>
      {PATHS[name]}
    </svg>
  );
}
