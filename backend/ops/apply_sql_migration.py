#!/usr/bin/env python3
"""
Apply one or more SQL migration files using the existing SQLAlchemy engine.

Usage (from repo root or backend/):
  python backend/ops/apply_sql_migration.py backend/database/migrations/FILE.sql [more.sql ...]

This script prints visible progress and stops on first error.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List
from sqlalchemy import text

# Ensure 'backend' directory is on sys.path so `core` imports resolve when running from repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Reuse existing engine configuration
from core.database import engine


def _read_sql_file(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def _strip_line_comments(sql: str) -> str:
    """Remove -- line comments so semicolons in comments don't break splitting."""
    cleaned_lines = []
    for line in sql.splitlines():
        if "--" in line:
            line = line.split("--", 1)[0]
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _split_statements(sql: str) -> List[str]:
    """Naive split on semicolons; good for simple DDL used here."""
    parts: List[str] = []
    sql_no_comments = _strip_line_comments(sql)
    for stmt in sql_no_comments.split(";"):
        s = stmt.strip()
        if not s:
            continue
        parts.append(s)
    return parts


def apply_files(file_paths: List[Path]) -> None:
    if not file_paths:
        print("No SQL files provided.")
        sys.exit(1)

    with engine.begin() as conn:
        for p in file_paths:
            print(f"\n=== Applying: {p} ===")
            sql = _read_sql_file(p)
            stmts = _split_statements(sql)
            for i, stmt in enumerate(stmts, 1):
                print(f"-- Statement {i}/{len(stmts)}")
                conn.execute(text(stmt))
            print(f"✅ Applied {len(stmts)} statements from {p}")

    print("\nAll migrations applied successfully.")


if __name__ == "__main__":
    files = [Path(arg) for arg in sys.argv[1:]]
    apply_files(files)


