# ai-ml

Applied AI and Machine Learning: coursework, training labs, code samples and projects,
built while pursuing Master's degree in Applied Artificial Intelligence.

Each project under `projects/` is a self-contained [uv](https://docs.astral.sh/uv/) project.

| Project | What it does | Stack | AI | Progress |
|---|---|---|---|---|
| [`projects/rag`](projects/rag) | Retrieval-Augmented Generation | LangChain | No AI | Done |
| [`projects/tf`](projects/tf) | TensorFlow labs and the DeepLearning.AI *TensorFlow Developer Professional Certificate* coursework. | TensorFlow 2.16, Keras 3.3, Jupyter | No AI | Done |
| [`projects/web`](projects/web) | Minimal Flask service — the base for HTTP-serving experiments. | Flask 3.1 | No AI | Done |
| [`projects/python-fundamentals`](projects/python-fundamentals) | Python language coursework from mooc.fi: file I/O, CSV and JSON handling, error handling. Standard library only. | Python 3.12 stdlib | No AI | Done |
| [`projects/ocr`](projects/ocr) | Extracts every text line from invoice and till-receipt images, with row clustering and reading-order reconstruction. Typed package, argparse CLI, JSON/text output, tested. | PaddleOCR 3.7, ONNX Runtime, pytest | AI-assisted | Done |
| [`projects/autopilot`](projects/autopilot) | Real-time vehicle detection and tracking on video (cars, motorcycles, buses, trucks) with YOLO, rendered frame by frame through OpenCV. | Ultralytics YOLO, ONNX Runtime (GPU), OpenCV, PyTorch (CUDA 13.0) | No AI | In progress |

The **AI** column is deliberate. Learning projects are written without any AI assistance: the
purpose is to write clean code by applying my own knowledge and best practices, and letting a
model write it would ruin the point of learning. Projects marked *AI-assisted* are the opposite
case, built as AI-assisted engineering projects; each ships an `AGENTS.md` describing the
constraints agents work under in that codebase.

## Getting started

```bash
cd projects/<name>
uv sync
```

`<name>` is one of the project names. `uv sync` reads that
project's `.python-version` and its `uv.lock`, and builds the project's own `.venv`
beside them.

First sync of the two heavy projects is a large download — `ocr` about 930 MB and `tf`
about 1.4 GB. `web` is 2.6 MB and `python-fundamentals` has no dependencies at all.

Then follow that project's own `README.md`. If uv says the interpreter is missing,
`uv python install 3.12`.

### Initiating the project using uv (python package manager)
```bash
uv init . --bare --pin-python --python 3.12
```

### 1. Pin Python. TF 2.16.1 has wheels for cp39-cp312 only, so 3.13+ fails to resolve.
```bash
uv python install 3.12
uv python pin 3.12
```

### 2. Fresh venv on the pinned version
```bash
rm -rf .venv
uv venv
```

### 3. Kernel first, as a dev dependency
```bash
uv add --dev ipykernel
```

### 4. Then the course deps
```bash
uv add -r requirements.txt
uv pip install -r requirements.txt
uv sync
```

### 5. Verify. Must print 3.12.x and 2.16.1 before moving to VS Code.
```bash
.venv/bin/python -V
.venv/bin/python -c "import tensorflow as tf; print(tf.__version__)"
```

### 6. Get the interpreter path for VS Code
```bash
echo $PWD/.venv/bin/python
```

### <u>References</u>:
- uv, package manager for Python: https://docs.astral.sh/uv/
- Python Course: https://programming-26.mooc.fi/
- Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow, 3rd Edition: https://www.oreilly.com/library/view/hands-on-machine-learning/9781098125967/

## License

MIT — see [LICENSE](LICENSE).
