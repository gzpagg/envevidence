"""Generate original synthetic documents + recorded extraction. No real research results."""

import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1] / "envevidence" / "assets"
ROOT.mkdir(parents=True, exist_ok=True)

MAIN_PAGES = [
    [
        "EnvEvidence | Synthetic research fixture",
        "NOT A REAL PUBLICATION. Invented values for software testing only.",
        "This original example is distributed under the repository MIT license.",
        "Study: water treatment using three distinct experimental conditions.",
        "Reported removal refers to the target pollutant. TOC removal is a separate endpoint.",
        "Reagent doses for Trials A and B are reported in the accompanying supplement.",
        "Do not use these invented values for research conclusions or method recommendations.",
    ],
    [
        "Results | Trials A and B",
        "Trial A: acetaminophen in synthetic water, initial concentration 10 mg/L.",
        "Trial A used UV/H2O2 at pH 7.0 for 30 min.",
        "Trial A: acetaminophen removal was 85%; TOC removal was 20%.",
        "Trial B: acetaminophen in synthetic water, initial concentration 10 mg/L.",
        "Trial B used H2O2 in the dark at pH 7.0 for 30 min.",
        "Trial B: acetaminophen removal was 12%; TOC removal was 2%.",
        "These results belong to separate treatment arms and must not be merged.",
    ],
    [
        "Results | Trial C",
        "Trial C: sulfamethoxazole in real wastewater, initial concentration 5 mg/L.",
        "Trial C used UV/H2O2 at pH 6.5 for 60 min.",
        "Trial C: H2O2 dose was 15 mg/L.",
        "Trial C: sulfamethoxazole removal was 64%.",
        "The fixture provides no TOC endpoint for Trial C.",
    ],
]
SUPPLEMENT_PAGES = [
    [
        "Supplement | Reagent doses",
        "Synthetic fixture, linked to the main synthetic study.",
        "Trial A: H2O2 dose was 20 mg/L.",
        "Trial B: H2O2 dose was 20 mg/L.",
    ]
]


def pdf(name, pages):
    c = canvas.Canvas(str(ROOT / name), pagesize=A4, invariant=1)
    c.setTitle("EnvEvidence synthetic fixture - not research data")
    for page_no, lines in enumerate(pages, 1):
        y = 795
        for i, paragraph in enumerate(lines):
            c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 16 if i == 0 else 11)
            for line in simpleSplit(paragraph, "Helvetica", 11, 490):
                c.drawString(50, y, line)
                y -= 19
            y -= 13
        c.setFont("Helvetica", 9)
        c.drawString(50, 35, f"Synthetic fixture | PDF page {page_no}")
        c.showPage()
    c.save()


def field(key, value, unit, quote=None, source="main:p2"):
    return dict(
        key=key,
        value=value,
        unit=unit,
        status="found" if value is not None else "not_found",
        sources=[dict(block_id=source, quote=quote)] if quote else [],
    )


def experiment(
    label, pollutant, matrix, concentration, process, ph, minutes, removal, toc, dose, page
):
    prefix = f"Trial {label}"
    source = f"main:p{page}"
    identity = f"{prefix}: {pollutant} in {matrix}, initial concentration {concentration} mg/L."
    conditions = f"{prefix} used {process} at pH {ph} for {minutes} min."
    result = f"{prefix}: {pollutant} removal was {removal}%;"
    result += f" TOC removal was {toc}%." if toc is not None else ""
    if toc is None:
        result = f"{prefix}: {pollutant} removal was {removal}%."
    dose_source = "supplement:p1" if label in ("A", "B") else source
    return {
        "label": prefix,
        "fields": [
            field("pollutant", pollutant, None, identity, source),
            field("water_matrix", matrix, None, identity, source),
            field("initial_concentration", concentration, "mg/L", identity, source),
            field("process", process, None, conditions, source),
            field(
                "dose",
                f"H2O2: {dose}",
                "mg/L",
                f"{prefix}: H2O2 dose was {dose} mg/L.",
                dose_source,
            ),
            field("ph", ph, None, conditions, source),
            field("reaction_time", minutes, "min", conditions, source),
            field("removal_efficiency", removal, "%", result, source),
            field(
                "mineralization_efficiency",
                f"TOC removal: {toc}" if toc is not None else None,
                "%" if toc is not None else None,
                result if toc is not None else None,
                source,
            ),
        ],
    }


pdf("synthetic_main.pdf", MAIN_PAGES)
pdf("synthetic_supplement.pdf", SUPPLEMENT_PAGES)
recorded = {
    "experiments": [
        experiment(
            "A",
            "acetaminophen",
            "synthetic water",
            "10",
            "UV/H2O2",
            "7.0",
            "30",
            "85",
            "20",
            "20",
            2,
        ),
        experiment(
            "B",
            "acetaminophen",
            "synthetic water",
            "10",
            "H2O2 in the dark",
            "7.0",
            "30",
            "12",
            "2",
            "20",
            2,
        ),
        experiment(
            "C",
            "sulfamethoxazole",
            "real wastewater",
            "5",
            "UV/H2O2",
            "6.5",
            "60",
            "64",
            None,
            "15",
            3,
        ),
    ]
}
(ROOT / "recorded_extraction.json").write_text(
    json.dumps(recorded, ensure_ascii=False, indent=2), encoding="utf-8"
)
(ROOT / "expected.json").write_text(
    json.dumps(
        {
            "kind": "synthetic_expected_results",
            "experiments": 3,
            "values": {
                "Trial A": {
                    "removal_efficiency": "85",
                    "mineralization_efficiency": "TOC removal: 20",
                },
                "Trial B": {
                    "removal_efficiency": "12",
                    "mineralization_efficiency": "TOC removal: 2",
                },
                "Trial C": {"removal_efficiency": "64", "mineralization_efficiency": None},
            },
            "supplement_required_fields": ["Trial A.dose", "Trial B.dose"],
        },
        indent=2,
    ),
    encoding="utf-8",
)
print("Generated two synthetic PDFs and recorded/expected JSON fixtures.")
