"""The sample March 2024 rota that the rota tests share."""

import pytest

from rota.assignments import load

ROTA_LINES = [
    "# cover for March 2024",
    "2024-03-04 | ana  | early",
    "2024-03-05 | ana  | early",
    "2024-03-08 | ana  | night",
    "2024-03-09 | ana  | early",
    "2024-03-10 | ana  | early",
    "2024-03-11 | ana  | early",
    "2024-03-12 | ana  | early",
    "2024-03-13 | ana  | early",
    "2024-03-14 | ana  | early",
    "",
    "2024-03-04 | ben  | late",
    "2024-03-05 | ben  | early",
    "2024-03-06 | ben  | early",
    "2024-03-04 | cara | night",
]


@pytest.fixture
def rota_lines():
    return list(ROTA_LINES)


@pytest.fixture
def rota(rota_lines):
    return load(rota_lines)
