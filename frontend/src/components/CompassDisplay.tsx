import { useEffect, useRef, useState } from "react";
import { bearing, bearingWord } from "../lib/bearing";
import { headingFromOrientation, normalizeDegrees, screenAngle, unwrapRotation } from "../lib/heading";
import { Icon } from "./Icon";

// iOS 13+ only delivers orientation events after an explicit, gesture-driven permission request.
type OrientationPermission = { requestPermission?: () => Promise<"granted" | "denied"> };
function orientationPermission(): OrientationPermission | undefined {
  return window.DeviceOrientationEvent as unknown as OrientationPermission | undefined;
}

export function CompassDisplay({ lat, lon }: { lat: number; lon: number }) {
  const [position, setPosition] = useState<GeolocationPosition | null>(null);
  const [positionError, setPositionError] = useState(false);
  const [heading, setHeading] = useState<number | null>(null);
  const [headingDenied, setHeadingDenied] = useState(false);
  const lastRotation = useRef<number | null>(null);

  useEffect(() => {
    if (!navigator.geolocation) { setPositionError(true); return; }
    const id = navigator.geolocation.watchPosition(
      (p) => { setPosition(p); setPositionError(false); },
      () => { setPositionError(true); },
      // A coarse (cell/Wi-Fi) fix can be off by a street or more, which at landmark distance
      // flips the bearing; ask for GPS.
      { enableHighAccuracy: true, maximumAge: 10000 },
    );
    return () => navigator.geolocation.clearWatch(id);
  }, []);

  useEffect(() => {
    const onOrient = (e: Event) => {
      const h = headingFromOrientation(e as DeviceOrientationEvent, screenAngle());
      if (h != null) setHeading(h);
    };
    // Listen to both: Chrome puts north-referenced angles only on the `absolute` event,
    // Safari and Firefox only fire the plain one. `headingFromOrientation` drops the
    // relative readings Chrome also sends on `deviceorientation`.
    window.addEventListener("deviceorientationabsolute", onOrient);
    window.addEventListener("deviceorientation", onOrient);
    return () => {
      window.removeEventListener("deviceorientationabsolute", onOrient);
      window.removeEventListener("deviceorientation", onOrient);
    };
  }, []);

  async function enableHeading() {
    try {
      const result = await orientationPermission()?.requestPermission?.();
      if (result !== "granted") setHeadingDenied(true);
    } catch {
      setHeadingDenied(true);
    }
  }

  if (positionError || !position) {
    return (
      <div className="qc-hint">
        <div className="qc-hint__head"><span><Icon name="compass" size={18} /> Compass</span></div>
        <p className="qc-hint__text">Compass unavailable – check location permission</p>
      </div>
    );
  }

  const coords = position.coords;
  const degs = bearing(coords.latitude, coords.longitude, lat, lon);

  if (heading == null) {
    // Reached on a reload after the compass was bought: iOS has forgotten the gesture that
    // granted motion access, so offer a button to ask again.
    const canAsk = typeof orientationPermission()?.requestPermission === "function" && !headingDenied;
    return (
      <div className="qc-hint">
        <div className="qc-hint__head"><span><Icon name="compass" size={18} /> Compass</span></div>
        <p className="qc-hint__text">The landmark is {bearingWord(degs)} of you.</p>
        {canAsk && (
          <button type="button" className="qc-btn qc-btn--secondary qc-btn--block" onClick={enableHeading}>
            Show direction arrow
          </button>
        )}
      </div>
    );
  }

  // The arrow icon points right by default; subtract 90° so 0° rotation points up/north.
  // Unwrap against the previous value so the 0.2s transition never spins the long way.
  const target = degs - heading - 90;
  const rotation = lastRotation.current == null ? normalizeDegrees(target) : unwrapRotation(lastRotation.current, target);
  lastRotation.current = rotation;
  return (
    <div className="qc-hint">
      <div className="qc-hint__head"><span><Icon name="compass" size={18} /> Compass</span></div>
      <div className="qc-compass" aria-label="Compass arrow">
        <div className="qc-compass__arrow" style={{ transform: `rotate(${rotation}deg)` }}>
          <Icon name="arrow" size={48} />
        </div>
      </div>
    </div>
  );
}
