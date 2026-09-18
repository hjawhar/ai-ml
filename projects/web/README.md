# web

A minimal Flask service — the starting point for HTTP-serving experiments.

## Setup

From `projects/web`:

```bash
uv sync
uv run python app.py
```

Serves on <http://127.0.0.1:5000> with the reloader enabled:

```bash
curl http://127.0.0.1:5000/    # Hello, World!
```

## Layout

- `app.py` — the Flask application. `app` is the module-level instance, `/` is the only
  route, and `main()` starts the development server.
