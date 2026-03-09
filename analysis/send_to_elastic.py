from pathlib import Path
import pandas as pd
from elasticsearch import Elasticsearch

CSV_PATH = Path("results/outputs.csv")

es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "=HENhJj_gNnpJlDc3ZTz"),
    ca_certs=str(Path.home() / "elastic-local/elasticsearch-8.13.4/config/certs/http_ca.crt"),
)

INDEX_NAME = "wmdp_results"


def main():

    if not CSV_PATH.exists():
        raise FileNotFoundError("results/outputs.csv not found")

    df = pd.read_csv(CSV_PATH)

    for _, row in df.iterrows():
        es.index(index=INDEX_NAME, document=row.to_dict())

    print(f"[OK] {len(df)} rows sent to Elasticsearch index '{INDEX_NAME}'")


if __name__ == "__main__":
    main()