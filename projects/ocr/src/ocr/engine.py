"""PaddleOCR 3.x binding.

This is the only module that knows PaddleOCR exists. Everything downstream
consumes :class:`OcrPage`.

PaddleOCR 3.x is not API-compatible with 2.x: there is no ``use_gpu``,
no ``show_log``, and no ``.ocr()`` method. The pipeline is configured with
``use_doc_orientation_classify`` / ``use_doc_unwarping`` /
``use_textline_orientation`` and invoked through ``.predict()``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .layout import page_text, reading_order
from .models import BBox, TextLine


@dataclass
class OcrPage:
    """Everything one image yielded, plus how it was produced."""

    source: str
    lines: list[TextLine]
    engine: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ordered = reading_order(self.lines)
        return {
            "source": self.source,
            "engine": self.engine,
            "line_count": len(ordered),
            "text": page_text(ordered),
            "lines": [line.to_dict() for line in ordered],
        }


def page_from_result(result: Mapping[str, Any] | Any, source: str) -> OcrPage:
    """Convert one PaddleOCR result into an :class:`OcrPage`.

    Accepts either the result object (which is dict-like and also exposes
    ``.json``) or a plain mapping, with or without the ``{"res": ...}``
    envelope that ``.json`` wraps around the payload.
    """
    data: Mapping[str, Any] = result.json if hasattr(result, "json") else result
    data = data.get("res", data)

    lines = [
        TextLine(text=text, confidence=float(score), bbox=BBox.from_polygon(polygon))
        for text, score, polygon in zip(
            data["rec_texts"], data["rec_scores"], data["rec_polys"], strict=True
        )
        if str(text).strip()
    ]
    return OcrPage(source=source, lines=lines)


#: Detector/recogniser pairs per PP-OCRv6 size tier. PaddleOCR's own default is
#: the medium (server-class) tier, which costs roughly 3x the small tier on CPU
#: for whitespace-level differences in output, so `small` is the default here.
#: Measured on an M4 Max, 1440x3000 receipt: tiny 2.2s, small 6.4s, medium 18.5s.
MODEL_TIERS: dict[str, tuple[str, str]] = {
    "tiny": ("PP-OCRv6_tiny_det", "PP-OCRv6_tiny_rec"),
    "small": ("PP-OCRv6_small_det", "PP-OCRv6_small_rec"),
    "medium": ("PP-OCRv6_medium_det", "PP-OCRv6_medium_rec"),
}

#: Hand model choice back to PaddleOCR, which derives it from `lang`/`ocr_version`.
AUTO_MODELS = "auto"

#: Inference backends. ONNX Runtime measured 4-7x faster than PaddlePaddle on CPU
#: for byte-identical text (M4 Max: receipt 0.96s vs 6.32s), so it is the default.
#: "paddle" means "pass nothing and let PaddleOCR use its own engine".
ONNX_ENGINE = "onnxruntime"
PADDLE_ENGINE = "paddle"
ENGINES = (ONNX_ENGINE, PADDLE_ENGINE)


def resolve_models(tier: str) -> tuple[str, str] | None:
    """Map a tier name to (detector, recogniser), or None to let PaddleOCR choose."""
    if tier == AUTO_MODELS:
        return None
    try:
        return MODEL_TIERS[tier]
    except KeyError:
        valid = ", ".join([*MODEL_TIERS, AUTO_MODELS])
        raise ValueError(f"unknown model tier {tier!r}; expected one of: {valid}") from None


@dataclass
class OcrEngine:
    """Lazy wrapper around the PaddleOCR pipeline.

    Model construction downloads weights on first use and costs seconds, so the
    pipeline is built on the first :meth:`predict` call, not at import time.
    """

    lang: str = "en"
    models: str = "small"
    engine: str = "onnxruntime"
    max_side: int | None = None
    ocr_version: str | None = None
    device: str | None = None
    use_textline_orientation: bool = False
    use_doc_orientation_classify: bool = False
    use_doc_unwarping: bool = False
    _pipeline: Any = field(default=None, init=False, repr=False)

    def pipeline_options(self) -> dict[str, Any]:
        """The exact keyword arguments handed to ``PaddleOCR(...)``."""
        options: dict[str, Any] = {
            "use_textline_orientation": self.use_textline_orientation,
            "use_doc_orientation_classify": self.use_doc_orientation_classify,
            "use_doc_unwarping": self.use_doc_unwarping,
        }
        names = resolve_models(self.models)
        if names is not None:
            # PaddleOCR ignores `lang` and `ocr_version` once model names are
            # pinned, and warns about it. Send one or the other, never both.
            options["text_detection_model_name"] = names[0]
            options["text_recognition_model_name"] = names[1]
        else:
            options["lang"] = self.lang
            if self.ocr_version:
                options["ocr_version"] = self.ocr_version
        if self.max_side:
            # PaddleOCR's default limit_type is "min", which scales images *up*
            # to the limit. "max" is what actually caps detector input.
            options["text_det_limit_side_len"] = self.max_side
            options["text_det_limit_type"] = "max"
        if self.engine != PADDLE_ENGINE:
            options["engine"] = self.engine
        if self.device:
            options["device"] = self.device
        return options

    def _build(self) -> Any:
        # Paddle's C++ layer logs to stderr unless told otherwise; set this
        # before the import that loads libpaddle.
        os.environ.setdefault("GLOG_minloglevel", "2")

        from paddleocr import PaddleOCR

        return PaddleOCR(**self.pipeline_options())

    @property
    def pipeline(self) -> Any:
        if self._pipeline is None:
            self._pipeline = self._build()
        return self._pipeline

    def describe(self) -> dict[str, Any]:
        """Versions and settings that produced a result, for the JSON output."""
        import paddle
        import paddleocr

        names = resolve_models(self.models)
        return {
            "paddleocr_version": paddleocr.__version__,
            "paddlepaddle_version": paddle.__version__,
            "lang": self.lang,
            "engine": self.engine,
            "models": self.models,
            "text_detection_model": names[0] if names else "auto",
            "text_recognition_model": names[1] if names else "auto",
            "text_det_max_side": self.max_side or "auto",
            "ocr_version": self.ocr_version or "default",
            "device": self.device or "auto",
            "use_textline_orientation": self.use_textline_orientation,
            "use_doc_orientation_classify": self.use_doc_orientation_classify,
            "use_doc_unwarping": self.use_doc_unwarping,
        }

    def read(self, image_path: Path, visualization_dir: Path | None = None) -> OcrPage:
        """Run OCR over a single image."""
        results = list(self.pipeline.predict(str(image_path)))
        if len(results) != 1:
            raise ValueError(
                f"expected a single-image input, {image_path} produced {len(results)} results"
            )
        result = results[0]

        if visualization_dir is not None:
            visualization_dir.mkdir(parents=True, exist_ok=True)
            result.save_to_img(str(visualization_dir))

        page = page_from_result(result, source=str(image_path))
        page.engine = self.describe()
        return page
