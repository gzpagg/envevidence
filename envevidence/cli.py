import argparse
import os
import sys
from pathlib import Path

from .demo import DemoProvider, demo_project
from .exporting import csv_bytes, xlsx_bytes
from .models import Project, Study
from .parsing import parse_pdf
from .pipeline import run_project
from .providers import APIProvider
from .storage import ProjectStore
from .templates import water_treatment_fields


def main():
    parser = argparse.ArgumentParser(
        description="EnvEvidence: source-linked environmental evidence"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Start the local web interface")
    serve.add_argument("--port", type=int, default=8501)
    demo = commands.add_parser("demo", help="Offline synthetic end-to-end example")
    demo.add_argument("--output", type=Path, default=Path("data/demo"))
    extract = commands.add_parser("extract", help="Extract one main PDF with optional supplements")
    extract.add_argument("pdf", type=Path)
    extract.add_argument("--supplement", type=Path, action="append", default=[])
    extract.add_argument("--provider", choices=["openai", "anthropic"], required=True)
    extract.add_argument("--model", required=True)
    extract.add_argument("--output", type=Path, default=Path("data"))
    extract.add_argument(
        "--send-text",
        action="store_true",
        help="Explicitly permit sending parsed text to the selected API",
    )
    extract.add_argument(
        "--allow-partial", action="store_true", help="Accept missing/unparsed pages"
    )
    args = parser.parse_args()
    if args.command == "serve":
        os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
        from streamlit.web import cli

        sys.argv = [
            "streamlit",
            "run",
            str(Path(__file__).with_name("ui.py")),
            "--server.address=127.0.0.1",
            f"--server.port={args.port}",
            "--server.headless=true",
        ]
        cli.main()
        return
    try:
        if args.command == "demo":
            project, provider = demo_project(), DemoProvider()
        else:
            if not args.send_text:
                parser.error(
                    "Use --send-text to permit sending parsed document text to the selected API."
                )
            docs = [parse_pdf(args.pdf.read_bytes(), args.pdf.name)]
            docs.extend(parse_pdf(p.read_bytes(), p.name, "supplement") for p in args.supplement)
            if len({d.sha256 for d in docs}) != len(docs):
                parser.error("Duplicate PDF files.")
            for doc in docs:
                for warning in doc.warnings:
                    print(f"WARNING {doc.filename}: {warning}", file=sys.stderr)
            if any(d.warnings for d in docs) and not args.allow_partial:
                parser.error(
                    "Some pages were not parsed; inspect warnings and use --allow-partial to accept."
                )
            project = Project(
                name=args.pdf.stem,
                provider=args.provider,
                model=args.model,
                fields=water_treatment_fields(),
                studies=[Study(name=args.pdf.stem, documents=docs)],
            )
            env_key = "OPENAI_API_KEY" if args.provider == "openai" else "ANTHROPIC_API_KEY"
            provider = APIProvider(args.provider, args.model, os.getenv(env_key, ""))
        store = ProjectStore(args.output)
        run_project(project, store, provider)
        (args.output / "evidence.csv").write_bytes(csv_bytes(project))
        (args.output / "evidence.xlsx").write_bytes(xlsx_bytes(project))
        print(f"Project: {store.path(project.id)}")
        print(f"Experiments: {len(project.experiments)}; exports: {args.output}")
        if project.runs[-1].status == "failed":
            print(project.runs[-1].error, file=sys.stderr)
            raise SystemExit(1)
    except (ValueError, RuntimeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
