import { useEffect, useState } from "react";
import { bearing, bearingWord } from "../lib/bearing";
import { Icon } from "./Icon";

export function CompassDisplay({ lat, lon }: { lat: number; lon: number }) {
  const [position, setPosition] = useState<GeolocationPosition | null>(null);
  const [positionError, setPositionError] = useState(false);
  const [heading, setHeading] = useState<number | null>(null);

  useEffect(() => {
    if (!navigator.geolocation) { setPositionError(true); return; }
    const id = navigator.geolocation.watchPosition(
      (p) => { setPosition(p); setPositionError(false); },
      () => { setPositionError(true); },
      { enableHighAccuracy: false, maximumAge: 10000 },
    );
    return () => navigator.geolocation.clearWatch(id);
  }, []);

  useEffect(() => {
    const onOrient = (e: DeviceOrientationEvent) => {
      if (e.alpha != null) setHeading(e.alpha);
    };
    window.addEventListener("deviceorientation", onOrient);
    return () => window.removeEventListener("deviceorientation", onOrient);
  }, []);

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
    return (
      <div className="qc-hint">
        <div className="qc-hint__head"><span><Icon name="compass" size={18} /> Compass</span></div>
        <p className="qc-hint__text">The landmark is {bearingWord(degs)} of you.</p>
      </div>
    );
  }

  // The arrow icon points right by default; subtract 90° so 0° rotation points up/north.
  const rotation = (degs - heading - 90 + 360) % 360;
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
