import { render, screen } from "@testing-library/react";
import { LinkNotValidScreen } from "./LinkNotValidScreen";

const info = { code: "link_not_valid" as const, opens_at: null, expired_at: null, time_zone: null };

it("explains a link that is not active yet, in the game time zone", () => {
  const { container } = render(<LinkNotValidScreen info={{ ...info, reason: "not_yet", opens_at: "2026-10-10T07:00:00+00:00", time_zone: "Europe/Sofia" }} />);
  expect(screen.getByText("This game link isn't active yet")).toBeInTheDocument();
  expect(screen.getByText("Sat, 10 October 2026")).toBeInTheDocument();
  expect(screen.getByText("10:00")).toBeInTheDocument();
  expect(container.querySelector(".qs-sign--gold")).not.toBeNull();
});

it("shows the last valid day of an expired link", () => {
  const { container } = render(<LinkNotValidScreen info={{ ...info, reason: "expired", expired_at: "2026-09-14T21:00:00+00:00", time_zone: "Europe/Sofia" }} />);
  expect(screen.getByText("This game link isn't active")).toBeInTheDocument();
  expect(screen.getByText("This link expired on 14 September 2026.")).toBeInTheDocument();
  expect(container.querySelector(".qs-sign--red")).not.toBeNull();
});

it("shows no date for an unknown link", () => {
  render(<LinkNotValidScreen info={{ ...info, reason: "unknown" }} />);
  expect(screen.getByText("Please contact your host for a valid link.")).toBeInTheDocument();
  expect(screen.queryByText(/expired on/)).toBeNull();
});
