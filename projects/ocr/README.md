# ocr

Dump **every** text line of an English invoice or supermarket till receipt with
[PaddleOCR](https://www.paddleocr.ai/) 3.x.

No server, no Flask, no field guessing: you hand it an image, you get back every recognised
line with its confidence and pixel box, plus a reading-order text rendering of the page.
What you do with those lines is up to you.

```console
$ uv run ocr samples/invoice_sample.png --format text
NORTHWIND ANALYTICS LTD	INVOICE
144 Harbour Street, Suite 12
Bristol BS1 4QD, United Kingdom	Invoice No INV-2026-0417
VAT GB 342 8871 09	Invoice Date 12 August 2026
Due Date 11 September 2026
PO Number PO-88213
Terms Net 30
BILL TO	SHIP TO
Vega Logistics Inc.	Vega Logistics Inc. - Depot 4
...
DESCRIPTION	QTY	UNIT PRICE	TAX	AMOUNT
Freight data pipeline build	1	12,400.00	20%	12,400.00
Milestone 2 of 3 - ingestion layer
...
Amount Due	GBP 24,716.00
```

Columns survive because boxes are clustered into visual rows before being read
left-to-right — PaddleOCR's own output order interleaves columns.

## Requirements

- **Python 3.12 or 3.13.** `paddlepaddle` 3.3.1 publishes wheels for cp39–cp313 only, so
  3.14 cannot resolve. This project resolves on `>=3.12,<3.14` on its own, and its
  `.python-version` pins 3.12 as the default.
- [uv](https://docs.astral.sh/uv/)
- CPU is enough. Apple silicon runs natively.

## Setup

```bash
uv sync        # from projects/ocr
```

Every `uv run` in the rest of this file is run from `projects/ocr` too, so the `samples/`
paths resolve.

That fills this project's own `.venv` with ~930 MB (paddlepaddle, paddlex, opencv, scipy,
onnxruntime…). The **first OCR run** additionally downloads model weights into
`~/.paddlex/official_models` — 31 MB for the default `PP-OCRv6_small_*_onnx` pair, more if
you switch `--models` or `--engine`. Both are one-time costs; later runs are offline.

## Usage

```bash
# full JSON to stdout
uv run ocr samples/invoice_sample.png

# reading-order text only
uv run ocr samples/invoice_sample.png --format text

# JSON to a file, plus PaddleOCR's annotated image
uv run ocr invoice.png --out result.json --save-visualization viz/

# drop shaky detections
uv run ocr invoice.png --min-confidence 0.9
```

| Option | Default | Purpose |
| --- | --- | --- |
| `image` | – | Path to the invoice image (png, jpg, bmp, …) |
| `-f, --format {json,text}` | `json` | Full payload, or just the reading-order text |
| `-o, --out PATH` | stdout | Write output to a file instead of stdout |
| `--min-confidence FLOAT` | `0.0` | Discard lines scoring below the threshold |
| `--engine {onnxruntime,paddle}` | `onnxruntime` | Inference backend — see [Speed](#speed) |
| `--max-side PX` | PaddleOCR default | Cap detector input on the long edge |
| `--models {tiny,small,medium,auto}` | `small` | Model size tier — see [Speed](#speed) |
| `--lang` | `en` | Recognition language — **only effective with `--models auto`** |
| `--ocr-version` | PaddleOCR default | Pin a model generation, e.g. `PP-OCRv5` |
| `--device` | auto | `cpu`, `gpu:0`, … |
| `--textline-orientation` | off | Enable the 180° text-line classifier (upside-down lines) |
| `--save-visualization DIR` | – | Also write PaddleOCR's annotated image into `DIR` |
| `-v, --verbose` | off | Let PaddleOCR/Paddle log model loading and warnings to stderr |

By default stderr stays empty: Paddle's `ccache` warning and PaddleX's model-loading INFO
lines are muted, so stdout is the only thing you see. `--verbose` brings them back.

`--ocr-version` also requires `--models auto` — PaddleOCR ignores both it and `--lang` once a
model name is pinned, and the CLI tells you so rather than silently dropping the flag.

Exit codes: `0` success, `2` image path missing or not a file (checked **before** models load),
`3` no text recognised above the threshold.

### JSON shape

```json
{
  "source": "samples/invoice_sample.png",
  "engine": {
    "paddleocr_version": "3.7.0",
    "paddlepaddle_version": "3.3.1",
    "lang": "en",
    "engine": "onnxruntime",
    "models": "small",
    "text_detection_model": "PP-OCRv6_small_det",
    "text_recognition_model": "PP-OCRv6_small_rec",
    "text_det_max_side": "auto",
    "ocr_version": "default",
    "device": "auto",
    "use_textline_orientation": false,
    "use_doc_orientation_classify": false,
    "use_doc_unwarping": false
  },
  "line_count": 72,
  "text": "NORTHWIND ANALYTICS LTD\tINVOICE\n...",
  "lines": [
    { "text": "NORTHWIND ANALYTICS LTD", "confidence": 0.9859, "bbox": [62.0, 61.0, 445.0, 83.0] },
    { "text": "INVOICE", "confidence": 0.9999, "bbox": [1018.0, 61.0, 1176.0, 94.0] }
  ]
}
```

`bbox` is `[x0, y0, x1, y1]` in pixels, origin top-left, derived from the full detection polygon
(so rotated text still yields a correct enclosing box). `lines` and `text` are both in reading
order and both respect `--min-confidence`.

Pull fields out with whatever you like, e.g. `jq`:

```bash
uv run ocr invoice.png | jq -r '.lines[] | select(.confidence < 0.95) | .text'
```

### Use it as a library

```python
from pathlib import Path
from ocr import OcrEngine

page = OcrEngine(lang="en").read(Path("invoice.png"))
for line in page.lines:
    print(line.confidence, line.bbox.to_list(), line.text)
```

## How it works

| Module | Responsibility |
| --- | --- |
| `src/ocr/models.py` | `BBox` / `TextLine` primitives; polygon → box, vertical-overlap maths |
| `src/ocr/layout.py` | Row clustering, reading order, text rendering. Pure geometry |
| `src/ocr/engine.py` | The only PaddleOCR-aware module: builds the pipeline, converts results into `OcrPage` |
| `src/ocr/cli.py` | Argument parsing, filtering, output, exit codes |

Two boxes belong to the same row when their vertical extents overlap by at least 30 % of the
*shorter* box's height — that keeps a 26 px heading and a 14 px value printed beside it together.

PaddleOCR is imported lazily, so `--help` and bad-path errors return instantly instead of paying
the multi-second framework import.

## Measured on the bundled samples

Apple M4 Max, CPU, defaults (`--engine onnxruntime --models small`), wall clock for the
whole command:

| Sample | Size | Lines | Total | Inference | Confidence min / mean |
| --- | --- | --- | --- | --- | --- |
| `invoice_sample.png` — corporate invoice | 1240 × 1304 | 72 | 2.0 s | 0.72 s | 0.961 / 0.994 |
| `receipt_sample.png` — till receipt, rotated 1.4° | 1440 × 3000 | 109 | 2.2 s | 0.96 s | 0.704 / 0.986 |

The remaining ~1.2 s is fixed startup (interpreter, `import paddleocr`, session construction).
Reuse one `OcrEngine` across images and you pay it once.

No invoice line scores below 0.95. On the receipt exactly seven do, and they are the masked
asterisk runs (`************4471` at 0.704, `***` at 0.759, `6354********`), three single-letter
`Z` VAT codes, and `TILL 04` at 0.943 — every price, total and address line is above 0.95.

## Speed

Two knobs matter, and the defaults are chosen from measurements, not vibes.

**`--engine` — the big one.** ONNX Runtime is 4–7× faster than PaddlePaddle on CPU for the
*same weights*, and on Apple silicon it picks up the CoreML execution provider. Predict time on
the receipt / invoice:

| `--models` | `--engine paddle` | `--engine onnxruntime` **(default)** | Text difference |
| --- | --- | --- | --- |
| `tiny` | 2.18 s / 1.63 s | **0.31 s / 0.21 s** | 3 lines differ on the receipt |
| `small` **(default)** | 6.32 s / 5.19 s | **0.96 s / 0.72 s** | identical |
| `medium` | 18.91 s / 13.47 s | **3.98 s / 3.15 s** | identical |

ONNX weights are separate pre-converted downloads (`PP-OCRv6_small_det_onnx`, …) fetched on
first use; no conversion step and no `paddle2onnx` at runtime.

**`--models` — accuracy floor.** Inference cost is linear in the number of text *lines*, not
pixels: 109 lines → 6.4 s, 66 lines → 3.6 s, 17 lines → 1.2 s on the paddle engine, while
shrinking the receipt 8× in area only saved 2 s. So the recogniser tier dominates.
`tiny` drops rows in dense tables (it lost the five-column VAT summary at full resolution);
`small` differs from `medium` only in spacing inside masked numbers:

```diff
-CARD	**** **** ****	4471          +CARD	************4471
-CLUBCARD	6354	**** ****	2210  +CLUBCARD	6354********	2210
-IBAN: GB29 LOYD 3096 1741 8822 03   +IBAN: GB29 LOYD 30961741 8822 03
```

`--max-side PX` caps detector input on the long edge (recognition still crops from the
full-resolution image); `1280` cut paddle-engine detection roughly in half on the 3000 px receipt.

Measured and rejected: raising `text_recognition_batch_size` (no effect — already batched
internally), and downscaling the input (loses real rows before it saves much time). There is no
GPU path for PaddlePaddle on Apple silicon — its macOS arm64 wheels are CPU-only and oneDNN
kernels are x86-only, which is precisely why the ONNX Runtime backend wins.

The receipt is the harder sample on purpose: thermal-paper tones, torn edges, dense monospace
and a slight rotation, so every detection is a skewed quad rather than an axis-aligned box.
It still comes back whole — line items, the five-column VAT summary, the masked card number
and the barcode digits:

```console
$ uv run ocr samples/receipt_sample.png --format text
FRESHMART
SUPERMARKET
142 Kingsland High Street
...
2	SEMI SKIMMED MILK 2L	Z	2.40
1	BANANAS LOOSE	Z	0.93
0.842 kg @ 1.10/kg
...
ITEMS	16
SUBTOTAL	41.35
CLUBCARD SAVINGS	-2.10
TOTAL GBP	39.25
...
CODE	RATE	NET	VAT	GROSS
A	20.00%	4.78	0.96	5.74
Z	0.00%	33.51	0.00	33.51
```

## Development

```bash
uv run pytest                        # 31 fast unit tests, no models, <1 s
OCR_E2E=1 uv run pytest              # + 5 tests against the real models; whole suite ~3 s
```

The unit tests drive geometry, result parsing and the CLI contract through synthetic text
boxes and a fake engine, so they stay millisecond-fast and deterministic.

Both sample images are rendered from committed HTML (fictional companies and figures).
Regenerate with:

```bash
chromium --headless --screenshot=samples/invoice_sample.png \
         --window-size=1240,1304 samples/invoice_sample.html

chromium --headless --screenshot=samples/receipt_sample.png \
         --window-size=720,1500 --force-device-scale-factor=2 \
         samples/receipt_sample.html
```

## Coming from PaddleOCR 2.x

The 2.x API this project's predecessor used no longer exists:

| PaddleOCR 2.x | PaddleOCR 3.x |
| --- | --- |
| `PaddleOCR(use_gpu=False)` | `PaddleOCR(device="cpu")` |
| `PaddleOCR(show_log=False)` | removed; set `GLOG_minloglevel` for Paddle's C++ logs |
| `PaddleOCR(use_angle_cls=False)` | `PaddleOCR(use_textline_orientation=False)` |
| `ocr.ocr(img, det=True, cls=False)` | `ocr.predict(img)` |
| nested `[[box, (text, score)], …]` | result objects exposing `rec_texts`, `rec_scores`, `rec_polys`, `rec_boxes` |
| — | `use_doc_orientation_classify` / `use_doc_unwarping` sub-pipelines, both off here |
