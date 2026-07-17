#!/usr/bin/env python3
"""P6 / bounds guard — keep autonomous execution inside the governance boundary.

Runs as a PreToolUse hook before the agent executes a shell command. It is a fast,
fail-safe fuse, not a full policy engine: it catches the two failure modes that most
often turn a helpful loop into an incident.

  1. Direct pushes to `main`         -> blocked (use a feature branch + PR).
  2. Bypassing required checks       -> blocked (`--no-verify`, `--force` on main).

Exit 0 = allow the command. Exit 2 = block it (the agent must find another path).
Anything the hook doesn't understand is allowed (fail safe), so a bug here can never
stall the loop.
"""
import json
import re
import sys

PROTECTED_BRANCH = "main"

# Patterns that must never run autonomously.
BLOCKERS = [
    (re.compile(r"\bgit\s+push\b.*\b(origin\s+)?" + PROTECTED_BRANCH + r"\b"),
     "Direct push to `main` is not allowed. Open a PR from a feature branch."),
    (re.compile(r"\bgit\s+push\b.*--force\b.*\b" + PROTECTED_BRANCH + r"\b"),
     "Force-push to `main` is not allowed."),
    (re.compile(r"--no-verify\b"),
     "Bypassing required checks (--no-verify) defeats the verification stage."),
    (re.compile(r"\bgit\s+commit\b.*--no-verify\b"),
     "Committing with --no-verify skips the hooks that guarantee quality."),
]


def read_command() -> str:
    """Best-effort extraction of the shell command from the hook payload."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return ""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        return tool_input.get("command") or tool_input.get("cmd") or ""
    return str(tool_input)


def main() -> int:
    command = read_command()
    if not command:
        return 0  # nothing to inspect -> fail safe, allow.

    for pattern, reason in BLOCKERS:
        if pattern.search(command):
            print(f"pre-pr guard: BLOCKED — {reason}", file=sys.stderr)
            print(f"  offending command: {command}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
