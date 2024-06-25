"""
Tests for polyflame.util
"""

from pathlib import Path

import pytest

from polyflame.types import SourceInfo
from polyflame.util import get_checksum, load_taxonomy, msg_part_not_found
from polyflame.fhirflat import read_part, with_readable_terms

TAXONOMY = load_taxonomy("fhirflat-isaric3")
CHECKSUM = "03cc8e28d97a6a3ab20926d7c3f891f14e119eb882c6e8d3deb07e1b79eed089"
SOURCE: SourceInfo = {
    "N": 10,
    "checksum": CHECKSUM,
    "checksum_file": "sha256sums.txt",
    "path": Path("tests/data"),
}


def test_get_checksum():
    assert get_checksum("tests/data/sha256sums.txt") == CHECKSUM


def test_load_taxonomy():
    assert load_taxonomy("fhirflat-isaric3")


def test_load_taxonomy_error():
    with pytest.raises(FileNotFoundError):
        load_taxonomy("notfound")


def test_msg_part_not_found():
    assert (
        msg_part_not_found(SOURCE, "immunization")
        == "Data at path=tests/data missing part=immunization"
    )


def test_with_readable_terms():
    patient = with_readable_terms(
        read_part(
            SOURCE,
            "patient",
            {
                "extension.birthSex.code": "gender",
                "extension.age.value": "age",
                "extension.age.code": "age_unit",
                "id": "subject",
            },
        ),
        TAXONOMY,
        [{"term_column": "gender"}],
    )
    # check gender mapped correctly from SNOMED cod
    assert list(patient.gender.unique()) == ["female", "male"]
    # check column renames
    assert set(patient.columns) == {"gender", "age", "age_unit", "subject"}
