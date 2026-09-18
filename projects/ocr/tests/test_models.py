from ocr.models import BBox, TextLine


def test_bbox_from_polygon_uses_extremes_of_rotated_quad():
    # PaddleOCR returns detection polygons in clockwise order starting at the
    # visual top-left, which for skewed text is NOT the min-x/min-y corner.
    poly = [[110, 42], [300, 20], [305, 60], [115, 82]]

    bbox = BBox.from_polygon(poly)

    assert (bbox.x0, bbox.y0, bbox.x1, bbox.y1) == (110.0, 20.0, 305.0, 82.0)


def test_bbox_vertical_overlap_ratio_is_relative_to_shorter_box():
    tall = BBox(0, 0, 50, 40)
    short = BBox(60, 30, 90, 40)  # overlaps rows 30..40 => all 10px of `short`

    assert tall.vertical_overlap_ratio(short) == 1.0
    assert short.vertical_overlap_ratio(tall) == 1.0


def test_bbox_vertical_overlap_ratio_is_zero_when_disjoint():
    assert BBox(0, 0, 10, 10).vertical_overlap_ratio(BBox(0, 20, 10, 30)) == 0.0


def test_text_line_serializes_bbox_as_four_numbers():
    line = TextLine(text="Invoice No", confidence=0.97, bbox=BBox(1, 2, 3, 4))

    assert line.to_dict() == {
        "text": "Invoice No",
        "confidence": 0.97,
        "bbox": [1.0, 2.0, 3.0, 4.0],
    }
