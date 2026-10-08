import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import type { GameState } from "../api/types";
import { makeState } from "../test/fixtures";
import { WelcomeScreen } from "./WelcomeScreen";

const frame = { header: null, offline: false, notice: null, onNoticeDone: () => {} };

function renderWelcome(overrides: Partial<Omit<Parameters<typeof makeState>[0], "game">> & { game?: Partial<GameState["game"]> } & { onStart?: () => void; onLanguageChange?: (lang: string) => void } = {}) {
  const { onStart = vi.fn(), onLanguageChange = vi.fn(), game: gameOverride, ...stateOverrides } = overrides;
  const base = makeState({ phase: null, status: "not_started", clock: null, task: null, ...stateOverrides });
  const state = gameOverride ? { ...base, game: { ...base.game, ...gameOverride } } : base;
  return render(
    <WelcomeScreen
      state={state}
      frame={frame}
      language="en"
      onLanguageChange={onLanguageChange}
      onStart={onStart}
    />
  );
}

it("lists the rules with the reveal penalty from the game settings", () => {
  renderWelcome();
  expect(screen.getByText("+30 min")).toBeInTheDocument();
  expect(screen.getByText(/You have up to 4 hours\./)).toBeInTheDocument();
  expect(screen.getByText("A city quest in 8 riddles")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Sofia Old Town Quest" })).toBeInTheDocument();
});

it("asks for confirmation before calling onStart", async () => {
  const onStart = vi.fn().mockResolvedValue("ok");
  renderWelcome({ onStart });
  await userEvent.click(screen.getByRole("button", { name: "Start the quest" }));
  expect(screen.getByRole("dialog", { name: "Start the clock?" })).toBeInTheDocument();
  expect(onStart).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Start" }));
  expect(onStart).toHaveBeenCalledTimes(1);
});

it("renders a language menu for the game's available languages", async () => {
  const user = userEvent.setup();
  renderWelcome({ game: { available_languages: ["de", "sr"] } });
  expect(screen.getByRole("button", { name: "Language, EN" })).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Language, EN" }));
  expect(screen.getByRole("option", { name: "DE" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "SR" })).toBeInTheDocument();
});

it("calls onLanguageChange when a language is picked from the menu", async () => {
  const onLanguageChange = vi.fn();
  renderWelcome({ game: { available_languages: ["de", "sr"] }, onLanguageChange });
  await userEvent.click(screen.getByRole("button", { name: "Language, EN" }));
  await userEvent.click(screen.getByRole("option", { name: "SR" }));
  expect(onLanguageChange).toHaveBeenCalledWith("sr");
});
