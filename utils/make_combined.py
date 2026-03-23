from __future__ import annotations

from pathlib import Path
import os
import pandas as pd
import subprocess

IN_DIR = Path("data/processed")
EXT_PATH = IN_DIR / "extension_questions.csv"
OUT_PATH = IN_DIR / "combined_questions.csv"


def get_os_csv_sep() -> str:
    return ";" if os.name == "nt" else ","


def detect_csv_sep(path: Path) -> str:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines:
        return get_os_csv_sep()
    header = lines[0]
    return ";" if header.count(";") > header.count(",") else ","


def normalize_columns(df: pd.DataFrame, source_value: str) -> pd.DataFrame:
    if "theme" not in df.columns or "question" not in df.columns:
        raise ValueError("Missing required columns: theme, question")

    df = df.copy()
    df["source"] = source_value
    df["theme"] = df["theme"].astype(str).str.strip().str.lower()
    df["source"] = df["source"].astype(str).str.strip().str.lower()
    df = df[["theme", "source", "question"]]
    df["question"] = df["question"].astype(str)
    df = df[df["question"].str.strip().ne("")]
    df = df.drop_duplicates(subset=["theme", "source", "question"]).reset_index(drop=True)
    return df


def main() -> None:
    # Cherche le sample existant
    sample_files = sorted(IN_DIR.glob("sample_*_per_theme.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
    if sample_files:
        sample_path = sample_files[0]
        print(f"[INFO] Using existing sample: {sample_path.name}")
    else:
        # Aucun sample : génère le sample par défaut avec n=5
        print("[INFO] No sample found, generating default sample with n=5")
        subprocess.run(["python", "utils/make_sample.py"], check=True)
        sample_files = sorted(IN_DIR.glob("sample_*_per_theme.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not sample_files:
            raise FileNotFoundError("Failed to generate default sample")
        sample_path = sample_files[0]

    if not EXT_PATH.exists():
        raise FileNotFoundError(f"Missing extension file: {EXT_PATH}")

    # Supprime l'ancien combined si présent
    if OUT_PATH.exists():
        OUT_PATH.unlink()
        print(f"[INFO] Removed existing {OUT_PATH.name}")

    # Lecture sample
    sample_sep = detect_csv_sep(sample_path)
    df_sample = pd.read_csv(sample_path, sep=sample_sep)
    df_sample = normalize_columns(df_sample, "wmdp")

    # Lecture extension
    ext_sep = detect_csv_sep(EXT_PATH)
    df_ext = pd.read_csv(EXT_PATH, sep=ext_sep)
    df_ext = normalize_columns(df_ext, "extension")

    # Combine
    combined = pd.concat([df_sample, df_ext], ignore_index=True)

    # Sauvegarde
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_PATH, index=False, encoding="utf-8", sep=get_os_csv_sep())

    print(f"[OK] Wrote {OUT_PATH} with {len(combined)} rows "
          f"(wmdp={len(df_sample)}, extension={len(df_ext)})")


if __name__ == "__main__":
    main()