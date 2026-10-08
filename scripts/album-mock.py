"""Generate frontend/src/album/mock.ts from the sample landmarks.yaml: real landmark stories, dummy photos.

usage, from backend/ (its venv has PyYAML):
  uv run python ../scripts/album-mock.py config/landmarks.yaml config/games.yaml ../frontend/src/album/mock.ts
"""
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

landmarks_cfg = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
landmarks = {lm["id"]: lm for lm in landmarks_cfg["landmarks"]}
game = yaml.safe_load(Path(sys.argv[2]).read_text(encoding="utf-8"))["games"][0]
order = game["tasks"]

# A Saturday morning walk: start 10:30 Sofia time (UTC+3 in October), 20–35 minutes per landmark.
start = datetime(2026, 10, 3, 7, 30, tzinfo=UTC)
gaps = [28, 24, 35, 31, 22, 26]
photo_counts = [1, 2, 1, 3, 1, 2]

chapters = []
t = start
for i, lm_id in enumerate(order):
    lm = landmarks[lm_id]
    t = t + timedelta(minutes=gaps[i % len(gaps)])
    reached = t
    photos = []
    for p in range(photo_counts[i % len(photo_counts)]):
        taken = reached + timedelta(minutes=4 + 3 * p)
        photos.append({
            "url": f"https://picsum.photos/seed/{lm_id}-{p + 1}/1200/900",   # dummy photo for the design draft
            "taken_at": taken.isoformat().replace("+00:00", "Z"),
        })
    chapters.append({
        "number": i + 1,
        "landmark": lm["name"],
        "story": lm["tourist_info"].strip(),
        "reached_at": reached.isoformat().replace("+00:00", "Z"),
        "photos": photos,
    })

end = t + timedelta(minutes=12)
album = {
    "game": game["name"],
    "team": "The Explorers",
    "time_zone": game.get("time_zone", "Europe/Sofia"),
    "played_on": start.isoformat().replace("+00:00", "Z"),
    "task_count": len(order),
    "total_seconds": int((end - start).total_seconds()) + 25 * 60,
    "rank": 2,
    "shared_rank": False,
    "host_message": "Thank you for exploring Sofia with us! Here is your journey, landmark by landmark – the "
                    "riddles you cracked, the stories behind the places, and the photos you took along the way.",
    "chapters": chapters,
}

body = json.dumps(album, ensure_ascii=False, indent=2)
out = f'''// Generated from backend/config/landmarks.yaml and games.yaml for the album design draft: the real landmark
// stories, a plausible Saturday-morning timeline, and dummy photos from picsum.photos (loaded only on
// the /album/preview page). Regenerate with scripts/album-mock.py; do not edit by hand.
import type {{ Album }} from "./types";

export const PREVIEW_TOKEN = "preview";

export const MOCK_ALBUM: Album = {body};
'''
Path(sys.argv[3]).write_text(out, encoding="utf-8")
print(f"wrote {sys.argv[3]}: {len(chapters)} chapters, {sum(len(c['photos']) for c in chapters)} photos")
