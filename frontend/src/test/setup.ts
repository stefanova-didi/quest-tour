import "@testing-library/jest-dom/vitest";

// Node >= 22 defines its own (disabled) `localStorage` global, which blocks
// vitest's jsdom environment from installing the real one (window === globalThis
// here, so the blocked global wins and `localStorage` is undefined in tests).
// Provide a Map-backed stand-in with a mockable `Storage` prototype instead.
class StoragePolyfill {
  #store = new Map<string, string>();
  get length() { return this.#store.size; }
  key(index: number) { return [...this.#store.keys()][index] ?? null; }
  getItem(key: string) { return this.#store.has(key) ? this.#store.get(key)! : null; }
  setItem(key: string, value: string) { this.#store.set(String(key), String(value)); }
  removeItem(key: string) { this.#store.delete(key); }
  clear() { this.#store.clear(); }
}
Object.defineProperty(globalThis, "Storage", { value: StoragePolyfill, configurable: true });
Object.defineProperty(globalThis, "localStorage", { value: new StoragePolyfill(), configurable: true });

