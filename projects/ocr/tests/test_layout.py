from ocr.layout import group_rows, page_text, reading_order
from ocr.models import BBox, TextLine


def line(text: str, x0: float, y0: float, x1: float, y1: float, conf: float = 0.99) -> TextLine:
    return TextLine(text=text, confidence=conf, bbox=BBox(x0, y0, x1, y1))


def test_group_rows_joins_boxes_that_overlap_vertically_despite_different_heights():
    # A 26px heading and a 14px value printed on the same visual row: their
    # centres are 5px apart and their heights differ by ~2x.
    heading = line("INVOICE", 60, 40, 240, 66)
    value = line("INV-2026-0417", 900, 47, 1080, 61)

    rows = group_rows([value, heading])

    assert [[ln.text for ln in row] for row in rows] == [["INVOICE", "INV-2026-0417"]]


def test_group_rows_keeps_vertically_separated_lines_apart():
    rows = group_rows([line("Bill To", 60, 200, 140, 216), line("Vega Logistics Inc.", 60, 230, 260, 246)])

    assert [[ln.text for ln in row] for row in rows] == [["Bill To"], ["Vega Logistics Inc."]]


def test_reading_order_emits_left_column_before_a_slightly_higher_right_column():
    # Sorting by y alone would emit "Invoice No" first because it sits 3px higher.
    left = line("NORTHWIND ANALYTICS LTD", 60, 50, 420, 76)
    right = line("Invoice No", 900, 47, 1000, 61)

    assert [ln.text for ln in reading_order([right, left])] == [
        "NORTHWIND ANALYTICS LTD",
        "Invoice No",
    ]


def test_page_text_separates_cells_with_tabs_and_rows_with_newlines():
    lines = [
        line("Description", 60, 400, 200, 416),
        line("Qty", 700, 400, 740, 416),
        line("Onboarding workshop", 60, 440, 300, 456),
        line("2", 700, 440, 720, 456),
    ]

    assert page_text(lines) == "Description\tQty\nOnboarding workshop\t2"


def test_page_text_of_empty_page_is_empty_string():
    assert page_text([]) == ""
