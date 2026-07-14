"""Retired M7F3-v7 command stub.

Historical v7 evidence remains auditable, but no v7 engine or callable execution surface
is retained. Use M7F4-v8 for the active exact self-financing implementation.
"""

from __future__ import annotations

import sys
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Reject every v7 invocation without forwarding arguments or importing v8."""
    del argv
    sys.stderr.write(
        "M7F3-v7 executable path is retired. Use "
        "scripts/pead_m7f4_v8_2019_crsp_vertical.py "
        "(EXACT_SELF_FINANCING_IDENTITY). Historical v7 evidence remains for audit only.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
