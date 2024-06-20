"""
FHIRFlat adapter for PolyFLAME

Reads in FHIRFlat files and provides commonly used analysis functions
"""

import configparser
from pathlib import Path
from typing import Final, Sequence

import numpy as np
import pandas as pd

from .types import DataPlotTuple, SourceInfo
from .util import get_checksum, load_taxonomy, msg_part_not_found

METADATA_FILE: Final[str] = "fhirflat.ini"

DEFAULT_TAXONOMY = load_taxonomy("fhirflat-isaric3")
DEFAULT_AGE_BINS = [-1, *list(5 * np.arange(25))]  # highest age of 120


def read_metadata(file: Path) -> SourceInfo:
    "Read FHIRFlat metadata file"
    cf = configparser.ConfigParser()
    cf.read(file)
    metadata = cf["metadata"]
    n = metadata["n"]
    n = int(n) if n.isdigit() else None
    return {
        "n": n,
        "checksum": metadata["checksum"],
        "checksum_file": metadata["checksum_file"],
        "path": file.parent,
    }


def load_data(folder: str, checksum: str) -> SourceInfo:
    "Reads FHIRFlat data"
    metadata_file = Path(folder) / METADATA_FILE
    if not metadata_file.exists():
        raise FileNotFoundError(f"FHIRFlat metadata not found: {metadata_file}")
    metadata = read_metadata(metadata_file)
    expected_checksum = metadata["checksum"]
    actual_checksum = get_checksum(metadata["checksum_file"])
    if not (expected_checksum == actual_checksum == checksum):
        raise ValueError(
            f"""load_data({folder} failed checksum validation
   Wanted: {checksum}
   Actual: {actual_checksum}
Specified: {expected_checksum}.

    Actual and Specified checksums should always match. If this is not the case,
    inform the data administrator of possible data corruption."""
        )
    return metadata


def get_part(data: SourceInfo, resource: str) -> Path:
    path = data["path"]
    resource_file = path / f"{resource}.parquet"
    if not resource_file.exists():
        raise ValueError(msg_part_not_found(data, resource))
    return resource_file


def read_part(
    data: SourceInfo, resource: str, column_mappings: dict[str, str] | None = None
) -> pd.DataFrame:
    df = pd.read_parquet(get_part(data, resource))
    if column_mappings:
        df = df[list(column_mappings.keys())]  # only keep columns in mappings
        return df.rename(columns=column_mappings)
    else:
        return df


def read_condition(data):
    return read_part(
        data,
        "condition",
        {
            "extension.presenceAbsence.code": "is_present",
            "code.code": "code",
            "category.code": "category_code",
        },
    )


def condition_proportion(data: SourceInfo) -> DataPlotTuple:
    "Returns proportions of condition"
    condition = read_condition(data)
    return condition, {}


def condition_upset(data: SourceInfo) -> DataPlotTuple:
    condition = read_condition(data)

    # get top 5 conditions and do upset plot
    # pivot and cast to indicator value
    return condition, {}


def age_pyramid(
    data: SourceInfo,
    tx: dict[str, dict[str, str]] = DEFAULT_TAXONOMY,
    age_bins: Sequence[int] = DEFAULT_AGE_BINS,
) -> DataPlotTuple:
    patient = read_part(
        data,
        "patient",
        {
            "gender.code": "gender",
            "extension.age.value": "age",
            "extension.age.code": "age_unit",
            "id": "subject",
        },
    )
    encounter = read_part(
        data, "encounter", {"subject": "subject", "admission.dischargeDisposition.code": "outcome"}
    )
    encounter["subject"] = encounter["subject"].map(lambda x: x.removeprefix("Patient/"))
    patient["gender"] = patient["gender"].map(tx["gender"])

    # http://unitsofmeasure.org|a represents years
    patient[patient["age_unit"] != "a"]["age"] = 0  # infants
    patient = patient.merge(encounter, on="subject", how="inner")
    patient["outcome"] = patient["outcome"].replace(tx["outcome"])

    # create age groups and format them as strings
    patient["age_group"] = pd.cut(patient["age"], bins=age_bins).map(
        lambda iv: f"{iv.left + 1} - {iv.right}"
    )
    patient = patient[["gender", "age_group", "outcome"]].value_counts().reset_index()

    return patient, {
        "cols": {"side": "gender", "y": "age_group", "stack_group": "outcome", "value": "count"}
    }
