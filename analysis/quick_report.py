from pathlib import Path
import os

import pandas as pd
import matplotlib.pyplot as plt

INPUT_PATH = Path("results/outputs.csv")
FIGURES_DIR = Path("results/figures")


def get_os_csv_sep() -> str:
    """Use ';' on Windows for better Excel compatibility, ',' elsewhere."""
    return ";" if os.name == "nt" else ","


def detect_csv_sep(path: Path) -> str:
    """
    Detect whether the CSV uses ',' or ';' by inspecting the header line.
    This makes the script robust when outputs.csv is produced on another OS.
    """
    header = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    # Simple heuristic: whichever appears more in header wins
    if header.count(";") > header.count(","):
        return ";"
    return ","


def save_bar(series, title, ylabel, out_name):
    plt.figure()
    series.plot(kind="bar")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / out_name, dpi=200)
    plt.close()


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError("results/outputs.csv not found. Run main.py first.")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    in_sep = detect_csv_sep(INPUT_PATH)
    df = pd.read_csv(INPUT_PATH, sep=in_sep)

    print("\n=== BASIC SUMMARY ===")
    print("Total rows:", len(df))
    print("Models:", sorted(df["model"].unique().tolist()))
    print("Themes:", sorted(df["theme"].unique().tolist()))
    print("Mean safety score (overall):", round(df["safety_score"].mean(), 3))

    out_sep = get_os_csv_sep()

    # 1) Mean score by theme
    mean_by_theme = df.groupby("theme")["safety_score"].mean().sort_values(ascending=False)
    save_bar(mean_by_theme, "Mean Safety Score by Theme", "Mean Safety Score", "mean_score_by_theme.png")
    mean_by_theme.to_csv(FIGURES_DIR / "summary_mean_score_by_theme.csv", sep=out_sep, encoding="utf-8")

    # 2) Mean score by model
    mean_by_model = df.groupby("model")["safety_score"].mean().sort_values(ascending=False)
    save_bar(mean_by_model, "Mean Safety Score by Model", "Mean Safety Score", "mean_score_by_model.png")
    mean_by_model.to_csv(FIGURES_DIR / "summary_mean_score_by_model.csv", sep=out_sep, encoding="utf-8")

    # 3) Label distribution (global)
    label_counts = df["label"].value_counts()
    save_bar(label_counts, "Response Label Distribution", "Count", "label_distribution.png")
    label_counts.to_csv(FIGURES_DIR / "summary_label_counts.csv", sep=out_sep, encoding="utf-8")

    # 4) Label distribution by theme (table)
    label_by_theme = pd.crosstab(df["theme"], df["label"])
    label_by_theme.to_csv(FIGURES_DIR / "summary_label_by_theme.csv", sep=out_sep, encoding="utf-8")

    print("\n=== Label counts ===")
    print(label_counts)

    print(f"\n[OK] Figures + summaries saved in results/figures/")


if __name__ == "__main__":
    main()