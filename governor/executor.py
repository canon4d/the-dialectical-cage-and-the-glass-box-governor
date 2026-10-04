"""The only component that mutates a protected resource.

In this prototype the executor accepts an ``Authorization`` that only the
monitor constructs. Python cannot *enforce* that (any in-process code could
import and call ``ProtectedResource.commit``), which is exactly why complete
mediation is reported as NOT ESTABLISHED for v0.1. The class boundary documents
the intended trust interface; an OS-level privilege boundary is roadmap v0.2.
"""

from __future__ import annotations

from .errors import ExecutionError
from .state import ProtectedResource, ResourceState

_SEAL = object()


class Authorization:
    """Minted by the monitor only."""

    __slots__ = ("effect", "resource_id", "event_id")

    def __init__(self, seal, effect: str, resource_id: str, event_id: str):
        if seal is not _SEAL:
            raise ExecutionError("authorization can only be minted by the monitor")
        self.effect, self.resource_id, self.event_id = effect, resource_id, event_id


def mint(effect: str, resource_id: str, event_id: str) -> Authorization:
    return Authorization(_SEAL, effect, resource_id, event_id)


class ProtectedExecutor:
    SUPPORTED = ("write_file", "delete_file")

    def __init__(self, resources: dict):
        self._resources = resources

    def execute(self, auth: Authorization, content, current: ResourceState) -> ResourceState:
        if not isinstance(auth, Authorization):
            raise ExecutionError("missing authorization")
        res: ProtectedResource = self._resources.get(auth.resource_id)
        if res is None or auth.effect not in self.SUPPORTED:
            raise ExecutionError("unsupported execution")
        try:
            return res.commit(auth.effect, content, current)
        except OSError as exc:
            raise ExecutionError(str(exc)) from exc
