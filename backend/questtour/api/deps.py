import re
from collections.abc import Iterator
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

_DEVICE_ID = re.compile(r"[A-Za-z0-9-]{8,64}")


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


def get_now(request: Request) -> datetime:
    return request.app.state.clock()


def get_device_id(x_device_id: Annotated[str | None, Header()] = None) -> str | None:
    return x_device_id if x_device_id and _DEVICE_ID.fullmatch(x_device_id) else None


SessionDep = Annotated[Session, Depends(get_session)]
NowDep = Annotated[datetime, Depends(get_now)]
DeviceDep = Annotated[str | None, Depends(get_device_id)]
