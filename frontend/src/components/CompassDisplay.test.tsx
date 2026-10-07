import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CompassDisplay } from "./CompassDisplay";

function makePosition(lat: number, lon: number): GeolocationPosition {
  return {
    coords: {
      latitude: lat,
      longitude: lon,
      altitude: null,
      accuracy: 10,
      altitudeAccuracy: null,
      heading: null,
      speed: null,
    },
    timestamp: Date.now(),
  } as GeolocationPosition;
}

describe("CompassDisplay", () => {
  let watchCallback: ((p: GeolocationPosition) => void) | null = null;
  let watchError: (() => void) | null = null;
  let watchId = 0;
  let originalGeolocation: Geolocation | undefined;

  beforeEach(() => {
    watchCallback = null;
    watchError = null;
    watchId = 0;
    originalGeolocation = navigator.geolocation;

    const mockGeolocation: Geolocation = {
      watchPosition: vi.fn((success, error) => {
        watchCallback = success as (p: GeolocationPosition) => void;
        watchError = error as (() => void) | null;
        return ++watchId;
      }),
      clearWatch: vi.fn(),
      getCurrentPosition: vi.fn(),
    } as unknown as Geolocation;

    Object.defineProperty(navigator, "geolocation", {
      value: mockGeolocation,
      configurable: true,
      writable: true,
    });
  });

  afterEach(() => {
    cleanup();
    Object.defineProperty(navigator, "geolocation", {
      value: originalGeolocation,
      configurable: true,
      writable: true,
    });
  });

  it("shows static bearing text when heading is unavailable", () => {
    render(<CompassDisplay lat={42.7} lon={23.3} />);
    act(() => {
      watchCallback?.(makePosition(42.6977, 23.3219));
    });
    expect(screen.getByText("The landmark is west of you.")).toBeInTheDocument();
  });

  it("shows unavailable message when geolocation fails", () => {
    render(<CompassDisplay lat={42.7} lon={23.3} />);
    act(() => {
      watchError?.();
    });
    expect(screen.getByText("Compass unavailable – check location permission")).toBeInTheDocument();
  });

  it("shows unavailable message when geolocation is not supported", () => {
    Object.defineProperty(navigator, "geolocation", {
      value: undefined,
      configurable: true,
      writable: true,
    });
    render(<CompassDisplay lat={42.7} lon={23.3} />);
    expect(screen.getByText("Compass unavailable – check location permission")).toBeInTheDocument();
  });

  // The landmark is due north of the position in every rotation test below, so the arrow
  // should point straight up (rotation 270, since the glyph points right) when facing north.
  function renderFacingNorthTarget() {
    render(<CompassDisplay lat={1} lon={0} />);
    act(() => {
      watchCallback?.(makePosition(0, 0));
    });
  }

  function orient(type: "deviceorientation" | "deviceorientationabsolute", fields: Record<string, unknown>) {
    act(() => {
      const event = new Event(type);
      for (const [key, value] of Object.entries(fields)) {
        Object.defineProperty(event, key, { value, configurable: true });
      }
      window.dispatchEvent(event);
    });
  }

  function arrowRotation(): string | undefined {
    return (document.querySelector(".qc-compass__arrow") as HTMLElement | null)?.style.transform;
  }

  it("rotates the arrow from an absolute Android reading (alpha runs counter-clockwise)", () => {
    renderFacingNorthTarget();
    orient("deviceorientationabsolute", { alpha: 0, absolute: true });
    expect(arrowRotation()).toBe("rotate(270deg)"); // facing north: arrow up

    // Facing west (alpha 90 → heading 270): north is to the user's right, arrow right.
    orient("deviceorientationabsolute", { alpha: 90, absolute: true });
    expect(arrowRotation()).toBe("rotate(360deg)"); // unwrapped from 270 the short way
  });

  it("rotates the arrow from Safari's webkitCompassHeading", () => {
    renderFacingNorthTarget();
    // Facing east: north is to the user's left, arrow left.
    orient("deviceorientation", { alpha: 42, absolute: false, webkitCompassHeading: 90 });
    expect(arrowRotation()).toBe("rotate(180deg)");
  });

  it("keeps the static bearing when only a relative alpha is available", () => {
    renderFacingNorthTarget();
    orient("deviceorientation", { alpha: 90, absolute: false });
    expect(screen.getByText("The landmark is north of you.")).toBeInTheDocument();
    expect(document.querySelector(".qc-compass__arrow")).toBeNull();
  });

  it("accounts for the screen being rotated to landscape", () => {
    Object.defineProperty(window.screen, "orientation", { value: { angle: 90 }, configurable: true });
    try {
      renderFacingNorthTarget();
      // Device top points west (alpha 90) but the screen is rotated 90°, so the user faces north.
      orient("deviceorientationabsolute", { alpha: 90, absolute: true });
      expect(arrowRotation()).toBe("rotate(270deg)");
    } finally {
      Object.defineProperty(window.screen, "orientation", { value: undefined, configurable: true });
    }
  });

  describe("iOS motion permission", () => {
    let originalDOE: unknown;
    beforeEach(() => {
      originalDOE = window.DeviceOrientationEvent;
    });
    afterEach(() => {
      Object.defineProperty(window, "DeviceOrientationEvent", { value: originalDOE, configurable: true, writable: true });
    });

    function installRequestPermission(result: "granted" | "denied") {
      const requestPermission = vi.fn(() => Promise.resolve(result));
      Object.defineProperty(window, "DeviceOrientationEvent", {
        value: { requestPermission },
        configurable: true,
        writable: true,
      });
      return requestPermission;
    }

    it("offers to request permission when no heading arrives", async () => {
      const requestPermission = installRequestPermission("granted");
      renderFacingNorthTarget();
      const button = screen.getByRole("button", { name: "Show direction arrow" });
      await act(async () => {
        button.click();
      });
      expect(requestPermission).toHaveBeenCalledTimes(1);
      // Still offered until an event actually arrives (Safari fires them right after granting).
      expect(screen.getByRole("button", { name: "Show direction arrow" })).toBeInTheDocument();
      orient("deviceorientation", { alpha: 0, webkitCompassHeading: 0 });
      expect(arrowRotation()).toBe("rotate(270deg)");
    });

    it("hides the offer after permission is denied", async () => {
      installRequestPermission("denied");
      renderFacingNorthTarget();
      await act(async () => {
        screen.getByRole("button", { name: "Show direction arrow" }).click();
      });
      expect(screen.queryByRole("button", { name: "Show direction arrow" })).toBeNull();
      expect(screen.getByText("The landmark is north of you.")).toBeInTheDocument();
    });

    it("shows no button where the browser needs no permission", () => {
      Object.defineProperty(window, "DeviceOrientationEvent", { value: undefined, configurable: true, writable: true });
      renderFacingNorthTarget();
      expect(screen.queryByRole("button")).toBeNull();
    });
  });
});
