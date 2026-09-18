"""Command line entry point: image in, every recognised text line out."""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Protocol, Sequence

from .engine import AUTO_MODELS, ENGINES, MODEL_TIERS, OcrEngine, OcrPage

EXIT_OK = 0
EXIT_BAD_INPUT = 2
EXIT_NO_TEXT = 3


class Reader(Protocol):
    """What the CLI needs from an OCR engine."""

    def read(self, image_path: Path, visualization_dir: Path | None = None) -> OcrPage: ...


def silence_backend_noise() -> None:
    """Mute PaddlePaddle/PaddleX chatter that says nothing about the OCR result.

    Paddle warns about a missing ``ccache`` on import even though nothing here
    compiles C++ extensions, and PaddleX logs every model construction and cache
    hit at INFO.

    ``paddlex/__init__.py`` calls its own ``setup_logging()``, which pins the
    level to INFO and honours no environment variable, so the level has to be
    raised *after* that import rather than before. Importing it here is not extra
    work: building the pipeline imports it anyway moments later. Real warnings and
    errors still reach stderr, and ``--verbose`` keeps everything.

    Applied by the CLI only, so importing this package as a library never
    reconfigures a caller's logging.
    """
    warnings.filterwarnings("ignore", message="No ccache found", category=UserWarning)

    import paddlex  # noqa: F401  - its import-time setup_logging() must run first

    logging.getLogger("paddlex").setLevel(logging.WARNING)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ocr",
        description="Dump every text line of an invoice image using PaddleOCR 3.x.",
    )
    parser.add_argument("image", help="path to the invoice image (png, jpg, bmp, ...)")
    parser.add_argument(
        "-f",
        "--format",
        choices=("json", "text"),
        default="json",
        help="json: lines with confidence and bbox (default). text: reading-order text only.",
    )
    parser.add_argument(
        "-o", "--out", type=Path, help="write the output to this file instead of stdout"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="drop recognised lines scoring below this threshold (0.0-1.0)",
    )
    parser.add_argument(
        "--models",
        choices=(*MODEL_TIERS, AUTO_MODELS),
        default="small",
        help=(
            "model size tier (default: small). Measured on a 1440x3000 receipt, CPU: "
            "tiny ~2s (drops dense table rows), small ~6s, medium ~18s (PaddleOCR's own "
            "default). auto lets --lang/--ocr-version pick."
        ),
    )
    parser.add_argument(
        "--max-side",
        type=int,
        metavar="PX",
        help=(
            "cap the detector's input to PX on its longest side (default: PaddleOCR's own "
            "limit). Recognition still crops from the full-resolution image. 1280 roughly "
            "halves detection time on large scans."
        ),
    )
    parser.add_argument(
        "--engine",
        choices=ENGINES,
        default="onnxruntime",
        help=(
            "inference backend (default: onnxruntime, measured 4-7x faster than paddle on "
            "CPU for identical text). Use paddle to fall back to PaddlePaddle."
        ),
    )
    parser.add_argument(
        "--lang",
        help=(
            "recognition language (default: en). Only has an effect with --models auto: "
            "the PP-OCRv6 tiers are single multilingual models and PaddleOCR ignores --lang "
            "once a model name is pinned."
        ),
    )
    parser.add_argument(
        "--ocr-version",
        help="pin a model generation, e.g. PP-OCRv5. Requires --models auto",
    )
    parser.add_argument("--device", help="inference device, e.g. cpu or gpu:0")
    parser.add_argument(
        "--textline-orientation",
        action="store_true",
        help="enable the text line orientation classifier (needed for upside-down lines)",
    )
    parser.add_argument(
        "--save-visualization",
        type=Path,
        metavar="DIR",
        help="also write PaddleOCR's annotated image into DIR",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="let PaddleOCR/Paddle log model loading and warnings to stderr",
    )
    return parser


def main(argv: Sequence[str] | None = None, engine: Reader | None = None) -> int:
    args = build_parser().parse_args(argv)

    image = Path(args.image)
    if not image.is_file():
        print(f"error: no such image: {image}", file=sys.stderr)
        return EXIT_BAD_INPUT

    if not args.verbose:
        silence_backend_noise()

    if args.lang and args.models != AUTO_MODELS:
        print(
            f"warning: --lang {args.lang} is ignored with --models {args.models}; "
            f"pass --models auto to select language-specific models",
            file=sys.stderr,
        )

    reader: Reader = engine or OcrEngine(
        lang=args.lang or "en",
        engine=args.engine,
        max_side=args.max_side,
        models=args.models,
        ocr_version=args.ocr_version,
        device=args.device,
        use_textline_orientation=args.textline_orientation,
    )
    page = reader.read(image, args.save_visualization)

    if args.min_confidence > 0:
        kept = [line for line in page.lines if line.confidence >= args.min_confidence]
        page = dataclasses.replace(page, lines=kept)

    if not page.lines:
        print(
            f"error: no text recognised in {image} "
            f"(min-confidence {args.min_confidence})",
            file=sys.stderr,
        )
        return EXIT_NO_TEXT

    payload = page.to_dict()
    rendered = (
        payload["text"]
        if args.format == "text"
        else json.dumps(payload, indent=2, ensure_ascii=False)
    )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
