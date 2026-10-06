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

  it("rotates the arrow when position and heading are available", () => {
    render(<CompassDisplay lat={1} lon={0} />);
    act(() => {
      watchCallback?.(makePosition(0, 0));
    });
    act(() => {
      const event = new Event("deviceorientation") as unknown as DeviceOrientationEvent;
      Object.defineProperty(event, "alpha", { value: 0, configurable: true });
      window.dispatchEvent(event);
    });
    const arrow = document.querySelector(".qc-compass__arrow");
    expect(arrow).toBeInTheDocument();
    expect(arrow).toHaveStyle({ transform: "rotate(270deg)" });
  });
});
