"""Shared configuration for Earth Online skill services.

This module centralizes runtime paths and default values so the rest of the
codebase does not hardcode host-specific locations.
"""

import os
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_DATA_ROOT = PROJECT_ROOT / "examples" / "seed-data"
DEFAULT_RUNTIME_DATA_ROOT = PROJECT_ROOT / "runtime" / "data"
DATA_ROOT = Path(os.environ.get("EARTH_ONLINE_DATA_ROOT", DEFAULT_RUNTIME_DATA_ROOT))

USER_FILE = DATA_ROOT / "USER.md"
MEMORY_FILE = DATA_ROOT / "MEMORY.md"
TASKS_FILE = DATA_ROOT / "tasks.json"
POINTS_FILE = DATA_ROOT / "points.json"
ACHIEVEMENTS_FILE = DATA_ROOT / "achievements.json"
REWARDS_FILE = DATA_ROOT / "rewards.json"
INIT_STATE_FILE = DATA_ROOT / ".earth_online_init.json"

SEED_USER_FILE = SEED_DATA_ROOT / "USER.md"
SEED_MEMORY_FILE = SEED_DATA_ROOT / "MEMORY.md"
SEED_TASKS_FILE = SEED_DATA_ROOT / "tasks.json"
SEED_POINTS_FILE = SEED_DATA_ROOT / "points.json"
SEED_ACHIEVEMENTS_FILE = SEED_DATA_ROOT / "achievements.json"
SEED_REWARDS_FILE = SEED_DATA_ROOT / "rewards.json"

DEFAULT_PLAYER_NAME = "玩家"
DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_STYLE = "standard"


RUNTIME_SEED_PAIRS = {
    USER_FILE: SEED_USER_FILE,
    MEMORY_FILE: SEED_MEMORY_FILE,
    TASKS_FILE: SEED_TASKS_FILE,
    POINTS_FILE: SEED_POINTS_FILE,
    ACHIEVEMENTS_FILE: SEED_ACHIEVEMENTS_FILE,
    REWARDS_FILE: SEED_REWARDS_FILE,
}


def ensure_data_root() -> Path:
    """Ensure the local runtime data root exists and is seeded."""

    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for runtime_file, seed_file in RUNTIME_SEED_PAIRS.items():
        if not runtime_file.exists() and seed_file.exists():
            shutil.copy2(seed_file, runtime_file)
    return DATA_ROOT
