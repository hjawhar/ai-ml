# tf

TensorFlow labs and the DeepLearning.AI *TensorFlow Developer Professional Certificate*
coursework, kept as notebooks.

- `notebooks/ex1_beginner.ipynb` — first TensorFlow model, end to end.
- `deeplearning-ai/tf-dev-prof-certificate/course1/` — course 1 labs and the week 1
  graded assignment. The labs run against the pinned stack below; the assignment
  (`week1/C1W1_Assignment.ipynb`) also imports `unittests`, the course grader helper,
  which ships only with the DeepLearning.AI course environment and is not included here, so its
  test cells cannot be run.

## Setup

TensorFlow 2.16.1 publishes cp39–cp312 wheels only, so this project pins Python 3.12 —
its own `.python-version`, plus `requires-python = ">=3.12,<3.13"`. On 3.13+ the
resolution fails.

```bash
uv python install 3.12        # once, if 3.12 is not already available
uv sync                       # from projects/tf
```

Verify before opening the notebooks — both lines must match:

```bash
uv run python -V                                              # 3.12.x
uv run python -c "import tensorflow as tf; print(tf.__version__)"   # 2.16.1
```

## Running the notebooks

`ipykernel` is installed as a dev dependency, so this project's venv works directly as a
Jupyter kernel. It is `projects/tf/.venv`. Point VS Code at the interpreter this prints,
run from this directory:

```bash
echo "$PWD/.venv/bin/python"
```

## References

- Course material: <https://github.com/https-deeplearning-ai/tensorflow-1-public/tree/main>
- uv: <https://docs.astral.sh/uv/>
