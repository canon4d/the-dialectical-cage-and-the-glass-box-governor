"""Injectable clocks and id sources. Tests use the fixed variants so that
expiry behaviour and event ids are fully deterministic."""

import itertools
import secrets
import time


class SystemClock:
    def now(self) -> int:
        return int(time.time())


class FixedClock:
    def __init__(self, start: int = 1_700_000_000):
        self._t = int(start)

    def now(self) -> int:
        return self._t

    def advance(self, seconds: int) -> None:
        self._t += int(seconds)

    def set(self, t: int) -> None:
        self._t = int(t)


class RandomIds:
    def next(self, prefix: str) -> str:
        return f"{prefix}-{secrets.token_hex(8)}"


class SequentialIds:
    """Deterministic ids for reproducible test runs."""

    def __init__(self):
        self._c = itertools.count(1)

    def next(self, prefix: str) -> str:
        return f"{prefix}-{next(self._c):06d}"
