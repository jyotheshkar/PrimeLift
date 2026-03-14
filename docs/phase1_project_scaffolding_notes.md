# Phase 1 Project Scaffolding Notes

This document explains what was implemented for Phase 1, what repository structure was created, and how to verify the scaffold from the terminal.

## Phase 1 Scope

For the current backend-first PrimeLift build, Phase 1 established the local project scaffold needed for the scientific core:

1. project root setup files
2. backend package structure
3. local virtual environment workflow
4. data and docs directories

The current repository is intentionally backend-first. Frontend application work is still deferred to the later frontend phase in `PROJECT_SPEC.md`.

## Files and Directories Created

Root-level setup:

- `.gitignore`
- `requirements.txt`
- `README.md`
- `.venv/`

Backend scaffold:

- `backend/src/primelift/__init__.py`
- `backend/src/primelift/data/`
- `backend/src/primelift/causal/`
- `backend/src/primelift/uplift/`
- `backend/src/primelift/decision/`
- `backend/src/primelift/api/`
- `backend/src/primelift/utils/`
- `backend/tests/`
- `backend/scripts/`

Project data and docs:

- `data/raw/`
- `data/processed/`
- `docs/`

## What Was Implemented

### 1. Python environment setup

The project uses a local virtual environment in:

- `.venv`

The environment workflow is documented in `README.md` for:

- Windows PowerShell
- Mac/Linux

### 2. Requirements file

The dependency baseline is defined in:

- `requirements.txt`

It includes the core libraries needed for the backend-first roadmap, including:

- `pandas`
- `numpy`
- `scipy`
- `scikit-learn`
- `fastapi`
- `uvicorn`
- `pydantic`
- `pytest`

### 3. Backend package scaffold

A modular src-layout Python package was created under:

- `backend/src/primelift/`

This already contains placeholder packages for later work:

- `data`
- `causal`
- `uplift`
- `decision`
- `api`
- `utils`

### 4. Data and docs folders

The project includes:

- `data/raw/` for generated datasets
- `data/processed/` for future downstream outputs
- `docs/` for implementation notes and data contracts

## Important Scope Note

Phase 1 created the structure and local developer workflow.

It did **not** create:

- the frontend app
- FastAPI endpoints
- any analysis logic by itself

Those were implemented in later phases.

## How to Verify Phase 1

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Check the virtual environment interpreter:

```powershell
python --version
```

Check the backend test suite can run from the local environment:

```powershell
python -m pytest backend/tests -q
```

## Terminal Proof: Current Structure

You can inspect the scaffold with:

```powershell
Get-ChildItem backend -Recurse
Get-ChildItem data
Get-ChildItem docs
```

The repository currently contains these scaffolded backend locations:

- `backend/scripts/`
- `backend/src/primelift/api/`
- `backend/src/primelift/causal/`
- `backend/src/primelift/data/`
- `backend/src/primelift/decision/`
- `backend/src/primelift/uplift/`
- `backend/src/primelift/utils/`
- `backend/tests/`

## Test Proof

The scaffold is not just folders on disk. It is runnable inside the local environment.

Run:

```powershell
python -m pytest backend/tests -q
```

Current output at this stage of the repository:

```text
...................                                                      [100%]
19 passed in 3.68s
```

That shows the scaffold is valid enough to support the later implemented phases.

## Short Conclusion

Phase 1 is represented in the repository by:

- a working Python virtual environment workflow
- a modular backend src-layout package
- root setup files
- persistent data and docs directories
- a runnable repository structure that later phases build on
