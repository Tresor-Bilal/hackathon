from __future__ import annotations

from pathlib import Path
import argparse
import os
import pandas as pd

IN_DIR = Path("data/processed")
COMBINED_PATH = IN_DIR / "combined_questions.csv"

FILES = [
    ("bio_questions.csv", "bio"),
    ("chem_questions.csv", "chem"),
    ("cyber_questions.csv", "cyber"),
]


def get_os_csv_sep() -> str:
    """Use ';' on Windows for better Excel compatibility, ',' elsewhere."""
    return ";" if os.name == "nt" else ","


def detect_csv_sep(path: Path) -> str:
    """Detect CSV separator (',' or ';') from header."""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines:
        return get_os_csv_sep()
    header = lines[0]
    return ";" if header.count(";") > header.count(",") else ","


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a sample: N questions per theme.")
    parser.add_argument("--n", type=int, default=5, help="Number of questions per theme (default: 5)")
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle questions before sampling (deterministic with seed=0).",
    )
    args = parser.parse_args()

    n = args.n
    if n <= 0:
        raise ValueError("--n must be a positive integer")

    # Clean old sample files
    for f in IN_DIR.glob("sample_*_per_theme.csv"):
        f.unlink()
        print(f"[INFO] Removed old sample file: {f}")

    parts = []

    for fname, theme in FILES:
        path = IN_DIR / fname

        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        in_sep = detect_csv_sep(path)
        df = pd.read_csv(path, sep=in_sep)

        if "question" not in df.columns:
            raise ValueError(f"File {path} has no 'question' column")

        # Clean empty questions
        df["question"] = df["question"].astype(str)
        df = df[df["question"].str.strip().ne("")]

        if args.shuffle:
            df = df.sample(frac=1, random_state=0).reset_index(drop=True)

        sample = df.head(n).copy()
        sample["theme"] = theme
        sample["source"] = "wmdp"

        parts.append(sample[["theme", "source", "question"]])

        if len(sample) < n:
            print(f"[WARN] Only {len(sample)} questions available for theme '{theme}'")

    out = pd.concat(parts, ignore_index=True)
    out_path = IN_DIR / f"sample_{n}_per_theme.csv"

    out.to_csv(out_path, index=False, encoding="utf-8", sep=get_os_csv_sep())

    # Remove combined (reset mode)
    if COMBINED_PATH.exists():
        COMBINED_PATH.unlink()
        print("[INFO] Removed existing combined_questions.csv")

    print(f"[OK] Created {out_path} with {len(out)} questions ({n} per theme)")


if __name__ == "__main__":
    main()