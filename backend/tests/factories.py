from dataclasses import dataclass
from datetime import datetime, timedelta

from questtour.models import Assignment, Game, GameTask, Landmark, Team
from questtour.tokens import hash_token

TOKEN = "explorers-token-0123456789abcdefghijklmnop"
OTHER_TOKEN = "owls-token-0123456789abcdefghijklmnopqrstu"
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
RIDDLE = (
    "Golden domes shine over the square that bears my name. I was built to honour "
    "soldiers who fell for this land's freedom. Who am I?"
)


@dataclass
class Seed:
    token: str
    other_token: str
    game_id: int
    assignment_id: int


def _default_landmarks() -> list[Landmark]:
    nevsky = Landmark(
        host_id="default",
        key="nevsky",
        name="Alexander Nevsky Cathedral",
        task_text=RIDDLE,
        task_image="a" * 64 + ".svg",
        accepted_answers=["Alexander Nevsky Cathedral", "Alexander Nevsky"],
        hint1="Look for the largest golden domes in the city centre.",
        hint2="The cathedral is named after a Russian saint and prince.",
        info_text="Built 1882–1912.\n\nOne of the largest Orthodox cathedrals.",
        info_image=None,
    )
    rotunda = Landmark(
        host_id="default",
        key="rotunda",
        name="Rotunda of St George",
        task_text="A red-brick church hides in a courtyard. Which?",
        task_image=None,
        accepted_answers=["Rotunda of St. George", "St George Rotunda"],
        hint1="Look in a courtyard behind the presidency.",
        hint2=None,
        info_text="The oldest building in Sofia.",
        info_image=None,
    )
    serdika = Landmark(
        host_id="default",
        key="serdika",
        name="Ancient Serdika Complex",
        task_text="Roman streets under your feet. Where?",
        task_image=None,
        accepted_answers=["Ancient Serdika", "Serdika"],
        hint1=None,
        hint2=None,
        info_text="Constantine called it 'my Rome'.",
        info_image=None,
    )
    return [nevsky, rotunda, serdika]


def seed_game(
    session,
    now: datetime,
    *,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    max_duration_minutes: int = 240,
    landmarks: list[Landmark] | None = None,
) -> Seed:
    landmarks = landmarks if landmarks is not None else _default_landmarks()
    game = Game(
        host_id="default",
        key="sofia-old-town",
        name="Sofia Old Town Quest",
        intro="Welcome!\n\nHave fun.",
        time_zone="Europe/Sofia",
        max_duration_minutes=max_duration_minutes,
        reveal_after_attempts=5,
        reveal_after_minutes=20,
        reveal_penalty_minutes=30,
    )
    game.tasks = [
        GameTask(position=i, landmark=lm) for i, lm in enumerate(landmarks)
    ]
    explorers = Team(host_id="default", key="explorers", name="The Explorers", participants=4)
    owls = Team(host_id="default", key="owls", name="Night Owls", participants=3)
    window = {
        "valid_from": valid_from or now - timedelta(days=1),
        "valid_until": valid_until or now + timedelta(days=2),
    }
    mine = Assignment(
        host_id="default",
        team=explorers,
        game=game,
        token_hash=hash_token(TOKEN),
        exit_message="Thank you for exploring Sofia with us!",
        **window,
    )
    theirs = Assignment(
        host_id="default",
        team=owls,
        game=game,
        token_hash=hash_token(OTHER_TOKEN),
        exit_message="Thanks!",
        **window,
    )
    session.add_all([game, explorers, owls, mine, theirs])
    session.commit()
    return Seed(TOKEN, OTHER_TOKEN, game.id, mine.id)


SERVICE_TOKEN = "service-token-0123456789abcdefghijklmnop"


def add_service_assignment(session, seed: Seed, now: datetime) -> str:
    """A service (test) team on the seeded game whose validity window closed long ago (R-25)."""
    game = session.get(Assignment, seed.assignment_id).game
    team = Team(host_id="default", key="qa-service", name="QA Service", is_service=True)
    session.add_all(
        [
            team,
            Assignment(
                host_id="default",
                team=team,
                game=game,
                token_hash=hash_token(SERVICE_TOKEN),
                valid_from=now - timedelta(days=30),
                valid_until=now - timedelta(days=29),
                exit_message="Test run complete.",
            ),
        ]
    )
    session.commit()
    return SERVICE_TOKEN


ANSWERS = ["Alexander-Nevsky", "rotunda of st george", "SERDIKA"]


def play_through(client, token: str, clock, *, minutes_per_task: int = 10) -> dict:
    """Start and finish all three seeded tasks (answer, photo, advance). Returns the final state."""
    client.post(f"/api/play/{token}/start")
    state = None
    for position, answer in enumerate(ANSWERS):
        clock.advance(minutes=minutes_per_task)
        client.post(f"/api/play/{token}/answer", json={"position": position, "answer": answer})
        client.post(
            f"/api/play/{token}/photo",
            data={"position": str(position)},
            files={"file": ("p.jpg", JPEG, "image/jpeg")},
        )
        state = client.post(f"/api/play/{token}/advance", json={"position": position}).json()[
            "state"
        ]
    return state
