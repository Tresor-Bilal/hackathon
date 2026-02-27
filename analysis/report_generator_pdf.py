from __future__ import annotations

from pathlib import Path
import textwrap

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet


OUT_CSV = Path("results/outputs.csv")
FIG_DIR = Path("results/figures")
OUT_PDF = Path("results/report.pdf")


def _wrap(s: str, width: int = 90) -> str:
    """Wrap long text for PDF table cells."""
    s = "" if s is None else str(s)
    s = " ".join(s.split())  # normalize whitespace
    return "<br/>".join(textwrap.wrap(s, width=width)) if s else ""


def _make_table(data, col_widths=None):
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def main() -> None:
    if not OUT_CSV.exists():
        raise FileNotFoundError(f"Missing {OUT_CSV}. Run: python main.py")

    df = pd.read_csv(OUT_CSV)

    required = {"theme", "model", "label", "safety_score"}
    if not required.issubset(df.columns):
        raise ValueError(f"outputs.csv must contain columns: {sorted(required)}")

    n_rows = len(df)
    models = sorted(df["model"].unique().tolist())
    themes = sorted(df["theme"].unique().tolist())
    mean_overall = float(df["safety_score"].mean())

    mean_by_model = (
        df.groupby("model")["safety_score"].mean().sort_values(ascending=False).round(3)
    )
    mean_by_theme = (
        df.groupby("theme")["safety_score"].mean().sort_values(ascending=False).round(3)
    )
    label_counts = df["label"].value_counts()

    # Potentially unsafe examples (preview only)
    risky = df[df["label"].eq("potentially_unsafe")].copy()
    # Keep only small previews to avoid reprinting harmful content
    if "question" in risky.columns:
        risky["question_preview"] = (
            risky["question"].astype(str).apply(lambda x: " ".join(x.split())[:220])
        )
    else:
        risky["question_preview"] = ""
    if "response" in risky.columns:
        risky["response_preview"] = (
            risky["response"].astype(str).apply(lambda x: " ".join(x.split())[:260])
        )
    else:
        risky["response_preview"] = ""

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="WMDP Evaluation Report",
    )

    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]

    story = []

    story.append(Paragraph("WMDP Evaluation Report (Auto-generated)", h1))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("<b>Summary</b>", h2))
    story.append(Paragraph(f"Total rows: <b>{n_rows}</b>", body))
    story.append(Paragraph(f"Models: <b>{', '.join(models)}</b>", body))
    story.append(Paragraph(f"Themes: <b>{', '.join(themes)}</b>", body))
    story.append(Paragraph(f"Mean safety score (overall): <b>{mean_overall:.3f}</b>", body))
    story.append(Spacer(1, 0.4 * cm))

    # Table: mean by model
    story.append(Paragraph("Mean safety score by model", h2))
    data_model = [["model", "safety_score"]] + [[k, f"{v:.3f}"] for k, v in mean_by_model.items()]
    story.append(_make_table(data_model, col_widths=[10 * cm, 4 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # Table: mean by theme
    story.append(Paragraph("Mean safety score by theme", h2))
    data_theme = [["theme", "safety_score"]] + [[k, f"{v:.3f}"] for k, v in mean_by_theme.items()]
    story.append(_make_table(data_theme, col_widths=[10 * cm, 4 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # Table: label counts
    story.append(Paragraph("Label counts", h2))
    data_labels = [["label", "count"]] + [[k, str(int(v))] for k, v in label_counts.items()]
    story.append(_make_table(data_labels, col_widths=[10 * cm, 4 * cm]))
    story.append(Spacer(1, 0.6 * cm))

    # Figures (if any)
    story.append(Paragraph("Figures", h2))
    if FIG_DIR.exists():
        pngs = sorted(FIG_DIR.glob("*.png"))
    else:
        pngs = []

    if not pngs:
        story.append(Paragraph("No figures found in results/figures/.", body))
    else:
        for p in pngs:
            story.append(Paragraph(p.name, body))
            try:
                img = Image(str(p))
                img._restrictSize(16.5 * cm, 10.5 * cm)
                story.append(img)
                story.append(Spacer(1, 0.4 * cm))
            except Exception:
                story.append(Paragraph("Could not embed image (skipped).", body))

    story.append(PageBreak())

    # Potentially unsafe previews (redacted-ish)
    story.append(Paragraph("Potentially unsafe examples (preview)", h2))
    story.append(
        Paragraph(
            "Note: content below is truncated previews for analysis/annotation only.",
            body,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    if len(risky) == 0:
        story.append(Paragraph("No potentially_unsafe rows found.", body))
    else:
        # Build a compact table
        rows = [["model", "theme", "question (preview)", "response (preview)"]]
        for _, r in risky.iterrows():
            rows.append(
                [
                    str(r.get("model", "")),
                    str(r.get("theme", "")),
                    Paragraph(_wrap(r.get("question_preview", ""), 70), body),
                    Paragraph(_wrap(r.get("response_preview", ""), 75), body),
                ]
            )
        story.append(_make_table(rows, col_widths=[4.2 * cm, 2.0 * cm, 5.2 * cm, 5.2 * cm]))

    doc.build(story)
    print(f"[OK] Wrote {OUT_PDF}")


if __name__ == "__main__":
    main()