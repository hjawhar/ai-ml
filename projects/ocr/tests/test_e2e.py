"""End-to-end checks against the real PaddleOCR models.

Opt in with ``OCR_E2E=1``: the first run downloads model weights
(~130 MB) into ``~/.paddlex/official_models`` and takes seconds per image.
"""

import os
from pathlib import Path

import pytest

from ocr.engine import OcrEngine

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
INVOICE = SAMPLES / "invoice_sample.png"
RECEIPT = SAMPLES / "receipt_sample.png"

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("OCR_E2E") != "1",
        reason="set OCR_E2E=1 to run the real models",
    ),
]


@pytest.fixture(scope="module")
def engine():
    return OcrEngine(lang="en")


@pytest.fixture(scope="module")
def invoice_page(engine):
    return engine.read(INVOICE)


@pytest.fixture(scope="module")
def receipt_page(engine):
    return engine.read(RECEIPT)


def test_invoice_text_contains_header_identifiers(invoice_page):
    text = invoice_page.to_dict()["text"]

    assert "INVOICE" in text
    assert "INV-2026-0417" in text


def test_invoice_yields_the_whole_document_not_just_a_fragment(invoice_page):
    # The rendered sample holds ~70 text lines; a detection or cropping
    # regression shows up as a collapse in this count.
    assert len(invoice_page.lines) > 60


def test_invoice_lines_have_plausible_confidence_and_in_bounds_bbox(invoice_page):
    for line in invoice_page.lines:
        assert 0.0 <= line.confidence <= 1.0
        assert 0 <= line.bbox.x0 < line.bbox.x1 <= 1240
        assert 0 <= line.bbox.y0 < line.bbox.y1 <= 1304


def test_rotated_receipt_keeps_label_and_amount_on_one_row(receipt_page):
    # The receipt is printed at -1.4 degrees, so every box is a skewed quad.
    # Recovering this row proves both the polygon-to-bbox extremes and the
    # row clustering survive rotation.
    text = receipt_page.to_dict()["text"]

    assert "FRESHMART" in text
    assert "TOTAL GBP\t39.25" in text


def test_rotated_receipt_recovers_a_five_column_vat_row(receipt_page):
    assert "A\t20.00%\t4.78\t0.96\t5.74" in receipt_page.to_dict()["text"]
