#!/usr/bin/env python3
"""
Batch-validate all Excel files under downloads/ using the project's DataLoader.
Outputs a concise validation report at docs/VALIDATION_REPORT.md.
"""
from __future__ import annotations
import os
import sys
import glob
import traceback
from datetime import datetime
import argparse
from pathlib import Path

# Allow running from repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
CLASS_DIR = REPO_ROOT / "src" / "dashboard" / "Class"
# Ensure the 'Class' package root is on sys.path so 'src.*' inside it resolves
if str(CLASS_DIR) not in sys.path:
    sys.path.insert(0, str(CLASS_DIR))

import pandas as pd  # noqa: E402

from src.data.data_loader import DataLoader  # type: ignore  # noqa: E402
from src.data.ssa_columns import SSAColumns  # type: ignore  # noqa: E402


def validate_file(path: Path) -> dict:
    res = {
        "file": str(path),
        "ok": False,
        "rows": 0,
        "valid_dates": 0,
        "percent_valid_dates": 0.0,
        "empty_ssa_numbers": 0,
        "priorities": {},
        "setores": {},
        "errors": None,
    }
    try:
        loader = DataLoader(str(path))
        df = loader.load_data()
        res["rows"] = len(df)
        # Resolve labels robustly via DataLoader mapping
        def lbl(idx: int) -> str | None:
            # Prefer DataLoader mapping; fallback to name match (case-insensitive)
            name = loader._get_label(idx) if hasattr(loader, "_get_label") else None
            if name and name in df.columns:
                return name
            expected = SSAColumns.COLUMN_NAMES.get(idx)
            if expected:
                for c in df.columns:
                    if str(c).strip().lower() == str(expected).strip().lower():
                        return c
            return None

        # Dates
        em_col = lbl(SSAColumns.EMITIDA_EM)
        dates = df[em_col] if em_col else pd.Series([], dtype="datetime64[ns]")
        valid_mask = dates.notna()
        res["valid_dates"] = int(valid_mask.sum())
        res["percent_valid_dates"] = float(
            0.0 if len(df) == 0 else (res["valid_dates"] / len(df)) * 100.0
        )
        # Empty SSA numbers should be 0 after loader filtering
        num_label = lbl(SSAColumns.NUMERO_SSA)
        if num_label:
            res["empty_ssa_numbers"] = int((df[num_label].astype(str).str.strip() == "").sum())
        # Simple distributions for sanity
        pri_label = lbl(SSAColumns.GRAU_PRIORIDADE_EMISSAO)
        set_label = lbl(SSAColumns.SETOR_EXECUTOR)
        if pri_label and pri_label in df.columns:
            res["priorities"] = df[pri_label].value_counts().to_dict()
        if set_label and set_label in df.columns:
            res["setores"] = df[set_label].value_counts().head(10).to_dict()
        res["ok"] = True
    except Exception:
        res["errors"] = traceback.format_exc()
    return res


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Batch-validate SSA Excel files.")
    parser.add_argument(
        "path",
        nargs="?",
        default=str(REPO_ROOT / "downloads"),
        help="File, folder, or glob pattern (default: downloads/)",
    )
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT / "docs" / "VALIDATION_REPORT.md"),
        help="Output report path (markdown)",
    )
    args = parser.parse_args(argv)

    base = Path(args.path)
    if base.is_dir():
        files = sorted(glob.glob(str(base / "*.xlsx")))
    elif base.is_file():
        files = [str(base)]
    else:
        # treat as glob
        files = sorted(glob.glob(args.path))

    report_path = Path(args.out)

    if not files:
        print("No Excel files found for given path.", file=sys.stderr)
        return 2

    results = [validate_file(Path(p)) for p in files]

    # Write report
    lines = []
    lines.append(f"# Validation Report\n")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
    ok_count = sum(1 for r in results if r["ok"]) 
    lines.append(f"Files scanned: {len(results)} | OK: {ok_count} | FAIL: {len(results)-ok_count}\n")

    for r in results:
        lines.append("\n---\n")
        lines.append(f"## {os.path.basename(r['file'])}\n")
        if r["ok"]:
            lines.append(f"- Rows: {r['rows']}\n")
            lines.append(f"- Valid dates: {r['valid_dates']} ({r['percent_valid_dates']:.1f}%)\n")
            lines.append(f"- Empty SSA numbers: {r['empty_ssa_numbers']}\n")
            lines.append(f"- Top setores (10): {r['setores']}\n")
            lines.append(f"- Priorities: {r['priorities']}\n")
        else:
            lines.append("- Status: FAIL\n")
            lines.append("```\n")
            lines.append(r["errors"] or "Unknown error")
            lines.append("\n````\n")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
