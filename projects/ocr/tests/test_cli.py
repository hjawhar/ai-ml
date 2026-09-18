import json

import pytest

from ocr.cli import main
from ocr.models import BBox, TextLine
from ocr.engine import OcrPage


class FakeEngine:
    """Stands in for PaddleOCR so the CLI contract can be tested in milliseconds."""

    def __init__(self, page: OcrPage):
        self.page = page
        self.calls: list[tuple] = []

    def read(self, image_path, visualization_dir=None):
        self.calls.append((image_path, visualization_dir))
        return self.page


class ExplodingEngine:
    def read(self, image_path, visualization_dir=None):
        raise AssertionError("OCR must not run for invalid input")


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "invoice.png"
    path.write_bytes(b"not really a png, the engine is faked")
    return path


def page_with(lines: list[TextLine], source: str = "invoice.png") -> OcrPage:
    return OcrPage(source=source, lines=lines, engine={"paddleocr_version": "3.7.0"})


def test_missing_image_exits_2_without_loading_the_ocr_models(tmp_path, capsys):
    exit_code = main([str(tmp_path / "nope.png")], engine=ExplodingEngine())

    assert exit_code == 2
    assert "nope.png" in capsys.readouterr().err


def test_explicit_lang_with_a_pinned_tier_says_it_will_be_ignored(image, capsys):
    engine = FakeEngine(page_with([TextLine("Rechnung", 0.99, BBox(10, 10, 90, 30))]))

    exit_code = main([str(image), "--lang", "de", "--models", "small"], engine=engine)

    err = capsys.readouterr().err
    assert exit_code == 0
    assert "--lang de" in err
    assert "--models auto" in err


def test_no_lang_notice_when_model_choice_is_left_to_paddleocr(image, capsys):
    engine = FakeEngine(page_with([TextLine("Rechnung", 0.99, BBox(10, 10, 90, 30))]))

    main([str(image), "--lang", "de", "--models", "auto"], engine=engine)

    assert capsys.readouterr().err == ""


def test_image_without_any_recognised_text_exits_3(image, capsys):
    exit_code = main([str(image)], engine=FakeEngine(page_with([])))

    assert exit_code == 3
    assert "no text" in capsys.readouterr().err.lower()


def test_json_output_lists_every_line_in_reading_order(image, capsys):
    engine = FakeEngine(
        page_with(
            [
                TextLine("Invoice No", 0.97, BBox(900, 47, 1000, 61)),
                TextLine("NORTHWIND ANALYTICS LTD", 0.99, BBox(60, 50, 420, 76)),
            ]
        )
    )

    exit_code = main([str(image)], engine=engine)

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert [line["text"] for line in payload["lines"]] == [
        "NORTHWIND ANALYTICS LTD",
        "Invoice No",
    ]
    assert payload["line_count"] == 2
    assert payload["engine"]["paddleocr_version"] == "3.7.0"


def test_min_confidence_filters_low_scoring_lines_from_lines_and_text(image, capsys):
    engine = FakeEngine(
        page_with(
            [
                TextLine("Amount Due", 0.99, BBox(60, 100, 200, 120)),
                TextLine("4T1I|", 0.31, BBox(60, 200, 200, 220)),
            ]
        )
    )

    exit_code = main([str(image), "--min-confidence", "0.8"], engine=engine)

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert [line["text"] for line in payload["lines"]] == ["Amount Due"]
    assert payload["text"] == "Amount Due"


def test_text_format_prints_reading_order_text_only(image, capsys):
    engine = FakeEngine(
        page_with(
            [
                TextLine("Qty", 0.99, BBox(700, 400, 740, 416)),
                TextLine("Description", 0.99, BBox(60, 400, 200, 416)),
                TextLine("Onboarding workshop", 0.98, BBox(60, 440, 300, 456)),
            ]
        )
    )

    exit_code = main([str(image), "--format", "text"], engine=engine)

    assert exit_code == 0
    assert capsys.readouterr().out == "Description\tQty\nOnboarding workshop\n"


def test_out_path_receives_the_json_and_stdout_stays_empty(image, tmp_path, capsys):
    destination = tmp_path / "result.json"
    engine = FakeEngine(page_with([TextLine("Amount Due", 0.99, BBox(60, 100, 200, 120))]))

    exit_code = main([str(image), "--out", str(destination)], engine=engine)

    assert exit_code == 0
    assert capsys.readouterr().out == ""
    assert json.loads(destination.read_text())["lines"][0]["text"] == "Amount Due"
