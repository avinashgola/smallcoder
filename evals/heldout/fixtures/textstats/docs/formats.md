# Input formats

The pipeline accepts plain text, one document per file. Encoding is assumed to
be UTF-8. Documents larger than 10 MB are rejected upstream.

## Historical note

Earlier versions supported a tab-separated corpus format. That format was
retired and the loader for it now lives in `legacy/corpus_loader.py`, which is
no longer wired into the pipeline.
