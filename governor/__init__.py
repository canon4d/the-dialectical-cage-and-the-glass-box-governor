"""Glass-Box Governor — reference-monitor prototype (Protected File Mutation Profile v1).

This package is the *entire* trusted path of the v0.1 prototype. Everything
outside it (evaluation/, scripts/, web/) is untrusted by design.

Scope statement (see LIMITATIONS.md): this is an in-process reference
implementation of selected execution-security components. It does not claim
complete mediation, kernel assurance, or implementation of the full paper.
"""

__version__ = "0.1.0"
PROFILE_ID = "protected-file-v1"

from .decisions import Decision, Reason, Verdict  # noqa: E402,F401
from .capability import Capability, CapabilityIssuer, CapabilityVerifier  # noqa: E402,F401
from .monitor import ReferenceMonitor, Outcome  # noqa: E402,F401
