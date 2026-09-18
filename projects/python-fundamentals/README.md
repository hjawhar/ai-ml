# python-fundamentals

Python language coursework from <https://programming-26.mooc.fi/>, written without AI
assistance — the point was to learn the language, not to generate it. Standard library
only; this project has no dependencies.

## Setup

From `projects/python-fundamentals`. The scripts read their fixtures with paths relative
to `src/`, so run them with `src/` as the working directory:

```bash
uv sync
cd src
uv run python files.py
```

## Layout

- `src/files.py` — file I/O drills: reads `data/example.txt` whole, then again line by
  line to total the line lengths; splits `data/grades.csv` on `;` by hand; writes
  `data/new_file.txt` and deletes it again with `os.remove`; rewrites
  `data/coders.csv`; and catches `FileNotFoundError` / `PermissionError` (and a bare
  `except`) on a path that does not exist.
- `src/data_processing.py` — parses `data/courses.json` with `json.loads` and prints
  each course name, then pulls the same kind of data live from the Helsinki
  `stats-mock` API with `urllib.request`, so it needs network access.
- `src/examples.py` — language exercises in one file: `range` loops, a PEP 695 generic
  function, min/max/sum helpers, in-place list `sort`/`reverse`/`insert`/`remove`/`pop`,
  anagram and palindrome checks, a recursive `factorial`, dictionary building,
  `random.randint` dice rolls, and `datetime.now()` formatting. Two more are defined
  but never called — the star pyramid (`print_stars`, its call site is commented out)
  and `set`-based de-duplication (`distinct`) — so running the file prints neither.
- `src/test.py` — a deliberate scoping bug kept as a lesson: `print_reversed` reads the
  global `name_list` instead of its own parameter, so both calls print the same four
  names. The test code sits under `if __name__ == "__main__"`.
- `data/` — fixtures: `example.txt`, `grades.csv`, `coders.csv`, `courses.json`.

`files.py` mutates `data/coders.csv` and creates then deletes `data/new_file.txt` when
it runs. That is intentional.
