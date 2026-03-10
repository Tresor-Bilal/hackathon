from pathlib import Path
import os

import pandas as pd
from elasticsearch import Elasticsearch

CSV_PATH = Path("results/outputs.csv")
INDEX_NAME = "wmdp_results"


def detect_csv_sep(path: Path) -> str:
    """Detect whether the CSV uses ',' or ';' by inspecting the header line."""
    header = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    return ";" if header.count(";") > header.count(",") else ","


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError("results/outputs.csv not found. Run main.py first.")

    in_sep = detect_csv_sep(CSV_PATH)
    df = pd.read_csv(CSV_PATH, sep=in_sep)

    # Docker Compose version: Elasticsearch runs locally without TLS/auth
    es = Elasticsearch("http://localhost:9200")

    if not es.ping():
        raise ConnectionError("Cannot connect to Elasticsearch at http://localhost:9200")

    for _, row in df.iterrows():
        es.index(index=INDEX_NAME, document=row.to_dict())

    print(f"[OK] {len(df)} rows sent to Elasticsearch index '{INDEX_NAME}'")


if __name__ == "__main__":
    main()