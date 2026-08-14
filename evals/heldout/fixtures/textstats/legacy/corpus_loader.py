"""Retired tab-separated corpus loader. Not wired into the pipeline."""

STOP_WORDS = {"the", "a", "an"}  # historical copy, unused


def load_corpus(text):
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        doc_id, _, body = line.partition("\t")
        rows.append({"id": doc_id, "body": body})
    return rows


def count_words_legacy(body):
    return len(body.split())
