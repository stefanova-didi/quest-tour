const DEVICE_KEY = "questtour.deviceId";
const TOKEN_KEY = "questtour.lastToken";

function randomId(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

let memoryId: string | null = null;

export function getDeviceId(): string {
  try {
    let id = localStorage.getItem(DEVICE_KEY);
    if (!id) { id = randomId(); localStorage.setItem(DEVICE_KEY, id); }
    return id;
  } catch {
    return (memoryId ??= randomId());    // storage blocked: one random ID per page load, never shared
  }
}

export function rememberToken(token: string): void {
  try { localStorage.setItem(TOKEN_KEY, token); } catch { /* ignore */ }
}
export function forgetToken(token: string): void {
  try { if (localStorage.getItem(TOKEN_KEY) === token) localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
}
export function lastToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}
