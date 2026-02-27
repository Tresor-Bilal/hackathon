# utils/make_sample.py
from __future__ import annotations

from pathlib import Path
import argparse
import os

import pandas as pd

IN_DIR = Path("data/processed")

FILES = [
    ("bio_questions.csv", "bio"),
    ("chem_questions.csv", "chem"),
    ("cyber_questions.csv", "cyber"),
]


def get_os_csv_sep() -> str:
    """Use ';' on Windows for better Excel compatibility, ',' elsewhere."""
    return ";" if os.name == "nt" else ","


def detect_csv_sep(path: Path) -> str:
    """Detect whether a CSV uses ',' or ';' by inspecting the header line."""
    header = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    if header.count(";") > header.count(","):
        return ";"
    return ","


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a small sample CSV: N questions per theme.")
    parser.add_argument("--n", type=int, default=5, help="Number of questions per theme (default: 5)")
    args = parser.parse_args()

    n = args.n
    if n <= 0:
        raise ValueError("--n must be a positive integer")

    parts = []
    for fname, theme in FILES:
        path = IN_DIR / fname
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        in_sep = detect_csv_sep(path)
        df = pd.read_csv(path, sep=in_sep)

        if "question" not in df.columns:
            raise ValueError(f"File {path} has no 'question' column")

        # Keep only non-empty questions
        df = df[df["question"].astype(str).str.strip().ne("")].copy()

        # Deterministic (stable) sample: first N rows
        sample = df.head(n).copy()
        sample["theme"] = theme

        parts.append(sample[["theme", "question"]])

    out = pd.concat(parts, ignore_index=True)
    out_path = IN_DIR / f"sample_{n}_per_theme.csv"

    out_sep = get_os_csv_sep()
    out.to_csv(out_path, index=False, encoding="utf-8", sep=out_sep)

    print(f"[OK] Created {out_path} with {len(out)} questions ({n} per theme).")


if __name__ == "__main__":
    main()