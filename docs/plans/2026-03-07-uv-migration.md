# uv Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace legacy `setup.py`/`setup.cfg`/`requirements.txt` with `pyproject.toml` and adopt `uv` for dependency management, local development, and CI.

**Architecture:** All package metadata moves into a single `pyproject.toml` using the setuptools backend (preserving namespace package support). `uv lock` generates the lockfile. GitHub Actions CI switches to `astral-sh/setup-uv` and tests against Python 3.10–3.12.

**Tech Stack:** uv, setuptools (pyproject.toml backend), GitHub Actions (`astral-sh/setup-uv@v5`)

---

### Task 1: Create pyproject.toml

**Files:**
- Create: `pyproject.toml`

**Step 1: Create the file**

```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sphinxcontrib-pseudocode"
version = "0.7.0"
description = "write LaTeX algorithm in your sphinx-doc powered docs"
readme = "README.md"
license = {text = "BSD"}
authors = [
    {name = "Zeyuan Hu", email = "zeyuan.zack.hu@gmail.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Documentation",
    "Topic :: Utilities",
]
requires-python = ">=3.10"
dependencies = [
    "Sphinx>=4.3",
    "docutils>=0.17",
]

[project.urls]
Homepage = "https://github.com/xxks-kkk/sphinxcontrib-algo/"

[project.optional-dependencies]
docs = [
    "Sphinx>=3.2.1",
    "myst-parser>=0.15.1",
]
dev = [
    "pytest",
]

[tool.setuptools.packages.find]
namespaces = true

[tool.bumpversion]
current_version = "0.7.0"
```

**Step 2: Verify the file was created correctly**

Run: `cat pyproject.toml`
Expected: file contents as above

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add pyproject.toml with setuptools backend and uv support"
```

---

### Task 2: Remove legacy packaging files

**Files:**
- Delete: `setup.py`
- Delete: `setup.cfg`
- Delete: `requirements.txt`

**Step 1: Delete the files**

```bash
git rm setup.py setup.cfg requirements.txt
```

**Step 2: Commit**

```bash
git commit -m "chore: remove legacy setup.py, setup.cfg, and requirements.txt"
```

---

### Task 3: Generate uv.lock and verify the package installs correctly

**Prerequisites:** `uv` must be installed. If not: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Step 1: Generate the lockfile**

```bash
uv lock
```

Expected: `uv.lock` file created in the project root.

**Step 2: Install package with dev dependencies**

```bash
uv sync --extra dev
```

Expected: no errors, package and pytest installed into `.venv/`

**Step 3: Run the tests**

```bash
uv run pytest
```

Expected: all tests pass (same result as before migration)

**Step 4: Commit the lockfile**

```bash
git add uv.lock
git commit -m "chore: add uv.lock"
```

---

### Task 4: Update GitHub Actions CI workflow

**Files:**
- Modify: `.github/workflows/python.yml`

**Step 1: Replace the workflow file contents**

```yaml
name: Python CI
on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [ '3.10', '3.11', '3.12' ]
    name: Python ${{ matrix.python-version }} sample
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --extra dev
      - run: uv run pytest
```

**Step 2: Verify the file looks correct**

Run: `cat .github/workflows/python.yml`
Expected: file contents as above

**Step 3: Commit**

```bash
git add .github/workflows/python.yml
git commit -m "ci: switch to uv and update Python matrix to 3.10-3.12"
```

---

### Task 5: Final verification

**Step 1: Run a full clean install and test cycle**

```bash
uv sync --extra dev
uv run pytest -v
```

Expected: all tests pass

**Step 2: Verify the package builds correctly**

```bash
uv build
```

Expected: `dist/` directory created with a `.whl` and `.tar.gz` file

**Step 3: Check dist contents look correct**

```bash
ls dist/
```

Expected: something like `sphinxcontrib_pseudocode-0.7.0-py3-none-any.whl` and `sphinxcontrib-pseudocode-0.7.0.tar.gz`
