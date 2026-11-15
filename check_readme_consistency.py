#!/usr/bin/env python3
"""Moved to tools/check_readme_consistency.py. This stub keeps the old command `python3 check_readme_consistency.py` working."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "tools" / "check_readme_consistency.py"), run_name="__main__")
