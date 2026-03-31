"""Smoke test for host adapter to onboarding flow.

This script validates that a host adapter can build a standard host_context and
that the init/onboarding flow can consume it.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.jiuwenclaw_adapter import JiuwenclawAdapter
from scripts.tools.init_skill_profile import run as init_skill_profile


def main() -> None:
    agent_root = Path.home() / ".jiuwenclaw" / "agent"
    runtime_root = Path(tempfile.mkdtemp()) / "runtime-data"
    os.environ["EARTH_ONLINE_DATA_ROOT"] = str(runtime_root)

    adapter = JiuwenclawAdapter(agent_root=agent_root)
    host_context = adapter.build_host_context("I want to set up Earth Online")
    init_result = init_skill_profile({"host_context": host_context})

    checks = {
        "has_platform": bool(
            host_context.get("host", {}).get("platform") == "jiuwenclaw"
        ),
        "has_user_id": bool(host_context.get("user", {}).get("id")),
        "has_current_date": bool(host_context.get("session", {}).get("current_date")),
        "has_uncertainties": bool("uncertainties" in host_context.get("context", {})),
        "init_has_next_action": bool(init_result.get("next_action")),
    }

    print(
        json.dumps(
            {
                "agent_root": str(agent_root),
                "checks": checks,
                "host_context": host_context,
                "init_result": init_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
