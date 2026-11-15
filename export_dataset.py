#!/usr/bin/env python3
"""Moved to tools/export_dataset.py. This stub keeps the old command `python3 export_dataset.py` working."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "tools" / "export_dataset.py"), run_name="__main__")
