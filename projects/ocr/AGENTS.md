# AGENTS.md

Operating notes for agents working in this repository. Read before editing.

## What this project is

A CLI that runs PaddleOCR 3.x over a single invoice image and emits **every recognised text
line** with confidence and bounding box, plus a reading-order text rendering.

**Deliberately out of scope** (do not add without being asked):

- No invoice *field* extraction — no invoice-number/date/total parsing, no money parsing, no
  line-item table reconstruction. The user cut this scope explicitly.
- No HTTP server, no Flask, no FastAPI. It is a CLI and a library, nothing else.
- No PDF pipeline, no multi-page input. `OcrEngine.read` raises if the input yields more than
  one result rather than silently dropping pages.
- No LLM/VLM post-processing.

## Commands

```bash
uv sync                                # install (Python 3.12/3.13 only)
uv run pytest                          # 31 unit tests, no models, <1 s
OCR_E2E=1 uv run pytest                # + 5 tests on the real models; whole suite ~3 s
uv run ocr samples/invoice_sample.png
uv run ocr samples/receipt_sample.png --format text --min-confidence 0.9
```

## Layout

| Path | Role |
| --- | --- |
| `src/ocr/models.py` | `BBox`, `TextLine`. Pure data + geometry. No imports beyond stdlib |
| `src/ocr/layout.py` | `group_rows`, `reading_order`, `page_text`. Pure geometry, imports `models` only |
| `src/ocr/engine.py` | `OcrPage`, `page_from_result`, `OcrEngine`. **Only** PaddleOCR-aware module |
| `src/ocr/cli.py` | argparse CLI, confidence filtering, output, exit codes |
| `tests/test_*.py` | Unit tests on synthetic boxes + a fake engine; `test_e2e.py` is opt-in |
| `samples/*.html` | Sources of truth for the sample PNGs; each header comment holds its render command |

## Invariants

1. **PaddleOCR stays behind `engine.py`.** `layout.py`, `models.py` and the unit tests must remain
   importable and runnable without paddle installed. If you need engine data elsewhere, widen
   `OcrPage`, do not import paddleocr.
2. **Keep the paddleocr import lazy** (inside `OcrEngine._build` / `describe`). Importing paddle
   costs seconds; `--help` and bad-path errors must stay instant. Exit code 2 is checked before
   any engine work — do not reorder that.
3. **Python pin is load-bearing.** `paddlepaddle` 3.3.1 has no cp314 wheel, so
   `requires-python = ">=3.12,<3.14"` and `.python-version = 3.12` must stay. Do not widen.
4. **Dependencies are pinned exactly** (`paddleocr==3.7.0`, `paddlepaddle==3.3.1`). Bumping
   either means re-running the e2e test, since result-dict keys have changed between majors.
5. **Coordinates come from `rec_polys`**, not `rec_boxes`: `BBox.from_polygon` takes extremes over
   all vertices so skewed text still gets a correct box. Numpy scalars are coerced to `float`
   there — that is what keeps the JSON serialisable.
6. **Row grouping normalises by the shorter box's height** (`ROW_OVERLAP_RATIO = 0.3`). Changing
   this silently reflows every text dump; `tests/test_layout.py` pins the two cases that matter
   (mixed font sizes on one row, and a right column sitting a few pixels higher than the left).
7. **The default model tier is `small`, deliberately** (`OcrEngine.models`, `MODEL_TIERS` in
   `engine.py`). PaddleOCR's own default is the medium server tier, which measured 18.5 s vs 6.4 s
   on the receipt for four whitespace differences and zero character errors. Do not "fix" this
   back to medium; `--models medium` is there for anyone who wants it. `tiny` is faster again
   but drops rows in dense tables, so it is not the default either.
8. **ONNX Runtime is the default backend, deliberately** (`OcrEngine.engine`, `ENGINES` in
   `engine.py`, `onnxruntime` in `dependencies`). It measured 4-7x faster than PaddlePaddle on CPU
   with byte-identical text at the `small` and `medium` tiers (receipt 0.96 s vs 6.32 s), and it
   uses the CoreML execution provider on Apple silicon. Weights come down pre-converted as
   `*_onnx` bundles, so `paddle2onnx` is NOT a runtime dependency — do not add it.
   `paddlepaddle` is still required: `predict()` imports it even on the ONNX path.
9. **`lang`/`ocr_version` and pinned model names are mutually exclusive.** PaddleOCR ignores
   the former once the latter are set and emits a `UserWarning` saying so, so
   `pipeline_options()` sends one branch or the other — never both. The CLI prints a notice when
   `--lang` is combined with a pinned tier instead of dropping it silently.
10. **Backend noise is muted in `cli.py`, not in the library.** `silence_backend_noise()` must
   import `paddlex` *before* raising its log level: `paddlex/__init__.py` runs its own
   `setup_logging()` that pins the level to INFO and honours no environment variable, so a
   `setLevel` call made earlier is silently undone. It is called after the exit-2 path check so
   bad arguments still fail instantly.

## PaddleOCR 3.x facts (2.x knowledge is wrong here)

- Construct with `PaddleOCR(lang=…, use_doc_orientation_classify=…, use_doc_unwarping=…,
  use_textline_orientation=…, device=…, ocr_version=…)`.
- There is **no** `use_gpu`, **no** `show_log`, **no** `use_angle_cls`, and **no** `.ocr()` method.
  Inference is `.predict(path)` and returns a list of dict-like result objects.
- Result keys consumed here: `rec_texts`, `rec_scores`, `rec_polys`. `result.json` wraps the
  payload in `{"res": {...}}`; `page_from_result` handles both shapes.
- Default models are `PP-OCRv6_medium_det` / `PP-OCRv6_medium_rec`, cached in
  `~/.paddlex/official_models` (133 MB), downloaded on first use.
- Paddle's C++ layer logs to stderr; `GLOG_minloglevel` is set in `OcrEngine._build` before the
  import that loads `libpaddle`.

## Testing policy

- TDD: write the failing test first, watch it fail, then implement.
- Unit tests must not download models or touch the network. Inject a fake engine (see
  `tests/test_cli.py`) or feed `page_from_result` a literal result dict.
- Anything needing real weights goes in `tests/test_e2e.py` behind `OCR_E2E=1` and the
  `e2e` marker.
- Assert observable behaviour: emitted text, ordering, confidences, exit codes, JSON shape.
  Do not assert on internals, defaults or mock call counts.
- Changing OCR-visible behaviour? Re-run `OCR_E2E=1 uv run pytest` and re-check the
  numbers quoted in `README.md` ("Measured on the bundled samples") before claiming done.
