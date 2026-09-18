import pytest

from ocr.engine import OcrEngine, page_from_result, resolve_models


def test_resolve_models_maps_a_tier_to_its_detector_and_recogniser():
    assert resolve_models("small") == ("PP-OCRv6_small_det", "PP-OCRv6_small_rec")
    assert resolve_models("tiny") == ("PP-OCRv6_tiny_det", "PP-OCRv6_tiny_rec")
    assert resolve_models("medium") == ("PP-OCRv6_medium_det", "PP-OCRv6_medium_rec")


def test_resolve_models_returns_none_for_auto_so_lang_picks_the_models():
    assert resolve_models("auto") is None


def test_resolve_models_rejects_an_unknown_tier_naming_the_valid_ones():
    with pytest.raises(ValueError, match="mahoosive"):
        resolve_models("mahoosive")


def test_max_side_caps_the_detector_input_instead_of_upscaling_it():
    # PaddleOCR's own limit_type is "min", which *enlarges* anything smaller
    # than the limit. Capping requires flipping the type as well as the length.
    options = OcrEngine(max_side=1280).pipeline_options()

    assert options["text_det_limit_side_len"] == 1280
    assert options["text_det_limit_type"] == "max"


def test_without_max_side_the_detector_limit_is_left_to_paddleocr():
    options = OcrEngine().pipeline_options()

    assert "text_det_limit_side_len" not in options
    assert "text_det_limit_type" not in options


def test_pipeline_options_carry_the_resolved_tier_model_names():
    options = OcrEngine(models="tiny").pipeline_options()

    assert options["text_detection_model_name"] == "PP-OCRv6_tiny_det"
    assert options["text_recognition_model_name"] == "PP-OCRv6_tiny_rec"


def test_onnxruntime_is_requested_explicitly_because_paddle_is_the_upstream_default():
    assert OcrEngine(engine="onnxruntime").pipeline_options()["engine"] == "onnxruntime"


def test_choosing_paddle_leaves_the_engine_key_out_so_paddleocr_uses_its_own():
    assert "engine" not in OcrEngine(engine="paddle").pipeline_options()


def test_lang_is_omitted_when_a_tier_pins_the_model_names():
    # PaddleOCR ignores `lang` whenever explicit model names are given, and warns
    # about it. Sending both would make --lang look effective when it is not.
    assert "lang" not in OcrEngine(models="small", lang="ja").pipeline_options()


def test_lang_is_sent_when_model_choice_is_left_to_paddleocr():
    assert OcrEngine(models="auto", lang="ja").pipeline_options()["lang"] == "ja"


def raw_result(**overrides):
    """Shape of a PaddleOCR 3.x OCR result, trimmed to the keys we consume."""
    result = {
        "input_path": "samples/invoice_sample.png",
        "rec_texts": ["INVOICE", "Invoice No"],
        "rec_scores": [0.9987, 0.9712],
        "rec_polys": [
            [[60, 40], [240, 40], [240, 66], [60, 66]],
            [[900, 47], [1000, 47], [1000, 61], [900, 61]],
        ],
    }
    result.update(overrides)
    return result


def test_page_from_result_pairs_each_text_with_its_score_and_polygon():
    page = page_from_result(raw_result(), source="invoice.png")

    assert [(ln.text, ln.confidence, ln.bbox.to_list()) for ln in page.lines] == [
        ("INVOICE", 0.9987, [60.0, 40.0, 240.0, 66.0]),
        ("Invoice No", 0.9712, [900.0, 47.0, 1000.0, 61.0]),
    ]


def test_page_from_result_unwraps_the_res_envelope_of_the_json_attribute():
    page = page_from_result({"res": raw_result()}, source="invoice.png")

    assert [ln.text for ln in page.lines] == ["INVOICE", "Invoice No"]


def test_page_from_result_drops_detections_that_recognised_no_text():
    page = page_from_result(
        raw_result(
            rec_texts=["INVOICE", "   ", "Invoice No"],
            rec_scores=[0.99, 0.10, 0.97],
            rec_polys=[
                [[60, 40], [240, 40], [240, 66], [60, 66]],
                [[10, 90], [20, 90], [20, 95], [10, 95]],
                [[900, 47], [1000, 47], [1000, 61], [900, 61]],
            ],
        ),
        source="invoice.png",
    )

    assert [ln.text for ln in page.lines] == ["INVOICE", "Invoice No"]


def test_page_to_dict_reports_source_line_count_and_reading_order_text():
    page = page_from_result(raw_result(), source="invoice.png")
    page.engine["paddleocr_version"] = "3.7.0"

    payload = page.to_dict()

    assert payload["source"] == "invoice.png"
    assert payload["line_count"] == 2
    assert payload["text"] == "INVOICE\tInvoice No"
    assert payload["engine"]["paddleocr_version"] == "3.7.0"
    assert payload["lines"][0] == {
        "text": "INVOICE",
        "confidence": 0.9987,
        "bbox": [60.0, 40.0, 240.0, 66.0],
    }
