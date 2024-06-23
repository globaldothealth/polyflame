"""
Tests for polyflame.fhirflat
"""

from pathlib import Path
import pytest

from polyflame.types import SourceInfo
from polyflame.fhirflat import (
    read_metadata,
    use_source,
    part_file,
    condition_upset,
    condition_proportion,
    age_pyramid,
)

DATA = Path("tests/data")
CHECKSUM = "03cc8e28d97a6a3ab20926d7c3f891f14e119eb882c6e8d3deb07e1b79eed089"
SOURCE: SourceInfo = {
    "N": 10,
    "checksum": CHECKSUM,
    "checksum_file": "sha256sums.txt",
    "path": Path("tests/data"),
}


def test_read_metadata():
    assert read_metadata(DATA / "fhirflat.toml") == SOURCE


def test_use_source():
    assert use_source(DATA, CHECKSUM) == SOURCE


def test_use_source_filenotfound():
    with pytest.raises(FileNotFoundError):
        use_source(Path("tests/notexists"), "")


def test_use_source_incorrect_checksum():
    with pytest.raises(ValueError, match=".*failed checksum validation"):
        assert use_source(DATA, "")


def test_part_file():
    source = use_source(DATA, CHECKSUM)
    assert part_file(source, "patient") == DATA / "patient.parquet"


def test_part_file_missing():
    source = use_source(DATA, CHECKSUM)
    with pytest.raises(FileNotFoundError):
        part_file(source, "immunization")


def test_condition_upset():
    df = condition_upset(SOURCE)["data"]
    assert (
        df.to_csv()
        == """subject,diabetes,headache
Patient/0f0836fe-8e72-4e2b-8869-2807b3599beb,False,True
Patient/4308f3e1-76e9-47ee-920e-a06fb472b9cc,False,False
Patient/540f5e28-6fc6-4625-9c4a-f66a0fefb7aa,False,True
Patient/6e86a167-c523-48bc-8af0-8b7d004cfc01,False,False
Patient/6f3681fb-dd4f-49a7-9d1a-ccb8fb7940f1,False,False
Patient/7ef87588-55c7-4f48-bbf2-896e1a837454,False,False
Patient/9a5be5ad-637a-44cb-a525-80abd55e9961,False,True
Patient/9ded1a45-69b7-4200-9d4d-34f9996cbea6,False,False
Patient/b4a9a271-2bc0-42b9-ab7f-f99c7a66b983,True,True
Patient/cfd5ad0f-cace-4ecd-891d-2b4ab8a10245,False,True
"""
    )


def test_condition_proportion():
    df = condition_proportion(SOURCE)["data"]
    assert (
        df.to_csv(index=False)
        == """condition,proportion
diabetes,1.0
headache,0.5
"""
    )


def test_age_pyramid():
    df = age_pyramid(SOURCE)["data"]
    assert (
        df.to_csv(index=False)
        == """gender,age_group,outcome,count
female,16 - 20,censored,1
female,41 - 45,alive,1
female,46 - 50,discharged,1
female,81 - 85,alive,1
male,1 - 5,alive,1
male,6 - 10,alive,1
male,31 - 35,alive,1
male,56 - 60,alive,1
male,86 - 90,alive,1
male,96 - 100,alive,1
"""
    )
