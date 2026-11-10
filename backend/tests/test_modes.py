"""The regular application stays live unless demo is explicitly selected."""

import os
import subprocess
import sys
from pathlib import Path


def test_live_is_default_and_demo_uses_separate_storage():
    code = """
import os
from unittest.mock import patch
with patch('dotenv.load_dotenv'):
    from app.config import settings
assert settings.mode == os.environ['EXPECTED_MODE']
assert settings.database_url.endswith(os.environ['EXPECTED_DATABASE'])
"""
    backend = Path(__file__).resolve().parents[1]
    for mode, database in [(None, "customer_lens.db"), ("demo", "demo.db")]:
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"APP_MODE", "DATABASE_URL", "DEMO_DATABASE_URL"}
        }
        if mode is not None:
            env["APP_MODE"] = mode
        env["EXPECTED_MODE"] = mode or "live"
        env["EXPECTED_DATABASE"] = database
        subprocess.run(
            [sys.executable, "-c", code],
            cwd=backend,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
