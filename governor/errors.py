"""Exceptions raised by trusted-core components. Every one maps to BLOCK."""


class GovernorError(Exception):
    """Base class. The monitor converts every GovernorError into a BLOCK."""


class MalformedCapability(GovernorError):
    pass


class PolicyError(GovernorError):
    """Policy artifact is corrupted, inadmissible or otherwise unusable."""


class PolicyUnavailable(GovernorError):
    pass


class RevocationUnavailable(GovernorError):
    pass


class StateUnavailable(GovernorError):
    """Resource metadata missing or unreadable (safety state UNKNOWN)."""


class StateInconsistent(GovernorError):
    """Resource content and its recorded digest disagree (out-of-band change)."""


class EvidenceUnavailable(GovernorError):
    pass


class ExecutionError(GovernorError):
    pass
