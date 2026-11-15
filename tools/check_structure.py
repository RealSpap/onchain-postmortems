#!/usr/bin/env python3
"""Refuse a repository layout that has drifted from the one written in tools/structure.json.

Reusable: the rules live in the JSON file, this script only applies them.
Run from anywhere:   python3 tools/check_structure.py [--root DIR] [--config FILE]
Exit code 0 = layout accepted; 1 = at least one violation (each one is printed).

Rules (all read from the config):
  1. root_files / root_dirs: nothing else may sit at the root (dotfiles and .git are listed too, except .git).
  2. max_root_entries: the count of visible root entries (no leading dot) stays under a ceiling,
     so the allowlist cannot grow quietly.
  3. incident_parent + incident_markers: a folder holding an incident marker file anywhere outside
     the parent folder is refused (an incident folder at the root, or one level too deep).
  4. incident_parent may hold only folders, each with a README.md.
  5. forbidden_names: no work, draft, backup or hand-over file or folder at any depth.
  5b. allowed_paths: every file below the root must match one of these patterns (fnmatch on the path
     relative to the root, "*" also crosses "/"). A file that fits no pattern is refused, whatever its name.
  6. legacy_redirects: old paths kept at the root so a published link still lands somewhere. A folder must hold
     only a short README.md that names <legacy_dir_target>/<name>; a file must be short and name
     <legacy_file_target>/<name>. Their number is capped (max_legacy_redirects) and they do not count
     towards max_root_entries.
"""
import argparse
import fnmatch
import json
import sys
from pathlib import Path

IGNORED = {".git", "__pycache__", ".DS_Store"}


def load_config(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def walk(root):
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part in IGNORED or part.endswith(".pyc") for part in rel.parts):
            continue
        yield p, rel


def check(root, cfg):
    root = Path(root)
    errors = []
    legacy = set(cfg.get("legacy_redirects", []))
    allowed = set(cfg["root_files"]) | set(cfg["root_dirs"])
    parent = cfg["incident_parent"]
    markers = set(cfg["incident_markers"])

    # 1 and 2: the root
    visible = 0
    for entry in sorted(root.iterdir()):
        name = entry.name
        if name in IGNORED:
            continue
        if name in legacy:
            continue
        if name not in allowed:
            kind = "folder" if entry.is_dir() else "file"
            errors.append(f"unexpected {kind} at the root: {name}")
        elif not name.startswith("."):
            visible += 1
    if visible > cfg["max_root_entries"]:
        errors.append(f"{visible} visible entries at the root, the ceiling is {cfg['max_root_entries']}")

    # 3 and 5: whole tree
    for p, rel in walk(root):
        if rel.parts[0] in legacy:
            continue
        for part in rel.parts:
            for pat in cfg["forbidden_names"]:
                if fnmatch.fnmatch(part.lower(), pat.lower()):
                    errors.append(f"forbidden name '{part}' in {rel.as_posix()}")
                    break
            else:
                continue
            break
        if p.is_file() and p.name in markers:
            if rel.parts[0] != parent or len(rel.parts) != 3:
                errors.append(f"incident file {rel.as_posix()} is outside {parent}/<slug>/")

    # 5b: every file must fit the written layout
    patterns = cfg.get("allowed_paths")
    if patterns:
        for p, rel in walk(root):
            if p.is_file() and len(rel.parts) > 1 and rel.parts[0] not in legacy:
                posix = rel.as_posix()
                if not any(fnmatch.fnmatch(posix, pat) for pat in patterns):
                    errors.append(f"file outside the layout: {posix}")

    # 4: the incident parent
    pdir = root / parent
    if pdir.is_dir():
        for child in sorted(pdir.iterdir()):
            if child.name in IGNORED:
                continue
            if not child.is_dir():
                errors.append(f"{parent}/ holds a loose file: {child.name}")
            elif not (child / "README.md").is_file():
                errors.append(f"{parent}/{child.name}/ has no README.md")
    else:
        errors.append(f"missing folder {parent}/")

    # 6: legacy redirects
    present = [n for n in legacy if (root / n).exists()]
    if len(legacy) > cfg.get("max_legacy_redirects", 0):
        errors.append(f"{len(legacy)} legacy redirects listed, the cap is {cfg.get('max_legacy_redirects', 0)}")
    for name in sorted(present):
        d = root / name
        if d.is_file():
            target = f"{cfg.get('legacy_file_target', 'tools')}/{name}"
            text = d.read_text(encoding="utf-8")
            where = name
        else:
            target = f"{cfg.get('legacy_dir_target', parent)}/{name}"
            files = sorted(x.name for x in d.rglob("*") if x.is_file())
            if files != ["README.md"]:
                errors.append(f"legacy redirect {name} must hold only a README.md, found {files}")
                continue
            text = (d / "README.md").read_text(encoding="utf-8")
            where = f"{name}/README.md"
        if len(text.splitlines()) > cfg.get("legacy_max_lines", 12) or target not in text:
            errors.append(f"legacy redirect {where} must be short and name {target}")
    return errors


def main(argv=None):
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(here.parent))
    ap.add_argument("--config", default=str(here / "structure.json"))
    a = ap.parse_args(argv)
    errors = check(a.root, load_config(a.config))
    for e in errors:
        print(f"STRUCTURE: {e}", file=sys.stderr)
    if errors:
        print(f"Structure check FAILED: {len(errors)} violation(s).", file=sys.stderr)
        return 1
    print("Structure check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
