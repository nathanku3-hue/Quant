"""Phase G4 canonical dataset readiness gates."""

from v2_discovery.readiness.canonical_readiness import G4_DEFAULT_REPORT_PATH
from v2_discovery.readiness.canonical_readiness import run_g4_canonical_readiness
from v2_discovery.readiness.canonical_readiness import validate_g4_readiness_report
from v2_discovery.readiness.canonical_readiness import write_g4_readiness_report
from v2_discovery.readiness.canonical_slice import G4_DEFAULT_ARTIFACT_URI
from v2_discovery.readiness.canonical_slice import G4_DEFAULT_MANIFEST_URI
from v2_discovery.readiness.canonical_slice import load_g4_canonical_slice
from v2_discovery.readiness.schemas import G4ReadinessError
from v2_discovery.readiness.schemas import G4ReadinessRun

__all__ = [
    "G4_DEFAULT_ARTIFACT_URI",
    "G4_DEFAULT_MANIFEST_URI",
    "G4_DEFAULT_REPORT_PATH",
    "G4ReadinessError",
    "G4ReadinessRun",
    "load_g4_canonical_slice",
    "run_g4_canonical_readiness",
    "validate_g4_readiness_report",
    "write_g4_readiness_report",
]
