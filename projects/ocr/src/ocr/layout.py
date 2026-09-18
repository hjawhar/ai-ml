"""Reading-order reconstruction from detected text boxes.

PaddleOCR returns lines in detection order, which interleaves columns on
multi-column documents such as invoices. Grouping boxes into visual rows first,
then ordering left-to-right inside each row, produces text a human would read
in the same sequence.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from .models import BBox, TextLine

#: Fraction of the shorter box's height that must overlap for two boxes to be
#: considered part of the same printed row.
ROW_OVERLAP_RATIO = 0.3


def group_rows(
    lines: Iterable[TextLine], min_overlap: float = ROW_OVERLAP_RATIO
) -> list[list[TextLine]]:
    """Cluster lines into visual rows, each sorted left-to-right."""
    rows: list[list[TextLine]] = []
    bands: list[BBox] = []

    for line in sorted(lines, key=lambda ln: (ln.bbox.y0, ln.bbox.x0)):
        if bands and bands[-1].vertical_overlap_ratio(line.bbox) >= min_overlap:
            rows[-1].append(line)
            band = bands[-1]
            bands[-1] = BBox(0.0, min(band.y0, line.bbox.y0), 0.0, max(band.y1, line.bbox.y1))
        else:
            rows.append([line])
            bands.append(BBox(0.0, line.bbox.y0, 0.0, line.bbox.y1))

    for row in rows:
        row.sort(key=lambda ln: ln.bbox.x0)
    return rows


def reading_order(lines: Iterable[TextLine]) -> list[TextLine]:
    """Flatten lines into top-to-bottom, left-to-right reading order."""
    return [line for row in group_rows(lines) for line in row]


def page_text(lines: Iterable[TextLine], cell_separator: str = "\t") -> str:
    """Render the page as plain text: one line per row, cells tab-separated."""
    rows: Sequence[list[TextLine]] = group_rows(lines)
    return "\n".join(cell_separator.join(line.text for line in row) for row in rows)
