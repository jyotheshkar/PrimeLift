# PrimeLift AI

GitHub repository connection is verified, and the repo now contains the first backend slice from `PROJECT_SPEC.md`.

PrimeLift AI is a local-first experimentation and growth analytics product. This repository currently implements only the backend foundation for the project:

- Python backend scaffold
- realistic synthetic London campaign dataset generation
- Phase 3 causal analysis core
- Phase 4 segment uplift analysis
- schema and data dictionary documentation
- quick inspection utility
- lightweight tests

This slice does **not** include the API, frontend, segment-level uplift analysis, or decision engine yet.

## Repository Structure

```text
PrimeLift/
  backend/
    scripts/
      generate_dataset.py
      run_causal_analysis.py
      run_segment_uplift_analysis.py
      render_dataset_view.py
      summarize_dataset.py
    src/
      primelift/
        __init__.py
        api/
        causal/
        data/
          generator.py
          schema.py
          summary.py
          viewer.py
        causal/
          ate.py
        decision/
        uplift/
          segment_analysis.py
        utils/
          paths.py
    tests/
      test_ate.py
      conftest.py
      test_dataset.py
      test_segment_uplift.py
  data/
    raw/
    processed/
  docs/
    london_campaign_users_data_dictionary.md
  PROJECT_SPEC.md
  README.md
  requirements.txt
```

## Environment Setup

Use Python 3.11 or newer.

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
```

### Mac/Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate the Dataset

Create the default 100,000-row London marketing experiment dataset:

```bash
python backend/scripts/generate_dataset.py
```

Output:

- `data/raw/london_campaign_users_100k.csv`

The generator uses a fixed random seed for reproducibility. You can override defaults if needed:

```bash
python backend/scripts/generate_dataset.py --rows 100000 --seed 42
```

## Inspect the Dataset

Print a quick operational summary:

```bash
python backend/scripts/summarize_dataset.py
```

The inspection utility reports:

- row count
- treatment/control split
- conversion rate
- segment counts
- borough counts

## Run Phase 3 Causal Analysis

Run the completed Phase 3 analysis on the generated dataset:

```bash
python backend/scripts/run_causal_analysis.py
```

This prints structured JSON for:

- conversion ATE
- bootstrap 95 percent confidence interval
- treated and control means
- absolute lift
- relative lift
- revenue lift analysis

## Run Phase 4 Segment Uplift Analysis

Run the grouped uplift analysis on the generated dataset:

```bash
python backend/scripts/run_segment_uplift_analysis.py
```

This prints structured JSON for uplift analysis grouped by:

- segment
- london_borough
- device_type
- channel

Each group includes:

- treated conversion rate
- control conversion rate
- uplift
- group size
- confidence indicator

## Run the Tests

```bash
pytest backend/tests -q
```

## Data Dictionary

Column definitions for the generated dataset live in:

- `docs/london_campaign_users_data_dictionary.md`

Detailed notes for the completed Phase 3 work live in:

- `docs/phase3_causal_analysis_notes.md`

Detailed notes for the completed Phase 4 work live in:

- `docs/phase4_segment_uplift_notes.md`

Detailed notes for the completed Phase 1 work live in:

- `docs/phase1_project_scaffolding_notes.md`

Detailed notes for the completed Phase 2 work live in:

- `docs/phase2_dataset_foundation_notes.md`
