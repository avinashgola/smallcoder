# Pipeline stages

1. Load documents (`helpers/io_adapter.py`)
2. Normalize whitespace (`helpers/normalize.py`)
3. Compute statistics (`textstats.py`)
4. Render the report (`reporting/render.py`)

Stages 1, 2 and 4 are stable and have not changed in several releases.
