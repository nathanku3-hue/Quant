from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping


_YES = {"Y", "YES", "TRUE", "1"}


def confirm_execution_intent(
    *,
    is_tty: bool,
    env: Mapping[str, str] | None = None,
    prompt_func: Callable[[str], str] | None = None,
) -> bool:
    """
    Guardrail for production-impacting payload generation.

    Policy:
      - Interactive TTY: require explicit operator input (Y/YES).
      - Non-interactive: require explicit environment override
        `TZ_EXECUTION_CONFIRM=YES`.
    """
    env_map = env or {}
    if is_tty:
        prompter = prompt_func or input
        decision = str(prompter("\n[EXECUTION] Generate Broker Payload? (Y/N): ")).strip().upper()
        return decision in _YES

    override = str(env_map.get("TZ_EXECUTION_CONFIRM", "")).strip().upper()
    return override in _YES
