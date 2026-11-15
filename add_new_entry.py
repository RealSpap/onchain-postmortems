#!/usr/bin/env python3
"""Moved to tools/add_new_entry.py. This stub keeps the old command `python3 add_new_entry.py` working."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "tools" / "add_new_entry.py"), run_name="__main__")
