"""
FHIRFlat adapter for PolyFLAME

Reads in FHIRFlat files and provides commonly used analysis functions
"""

import configparser
from pathlib import Path
from typing import Final, Sequence

import numpy as np
import pandas as pd

from .types import DataPlotInfo, SourceInfo, Taxonomy
from .util import get_checksum, load_taxonomy, msg_part_not_found, with_readable_terms

METADATA_FILE: Final[str] = "fhirflat.ini"

DEFAULT_TAXONOMY = load_taxonomy("fhirflat-isaric3")
DEFAULT_AGE_BINS = [-1, *list(5 * np.arange(25))]  # highest age of 120


def read_metadata(file: Path) -> SourceInfo:
    "Read FHIRFlat metadata file"
    cf = configparser.ConfigParser()
    cf.read(file)
    metadata = cf["metadata"]
    n = metadata.get("n", "")
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
    actual_checksum = get_checksum(metadata["path"] / metadata["checksum_file"])
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


def part_file(data: SourceInfo, resource: str) -> Path:
    path = data["path"]
    resource_file = path / f"{resource}.parquet"
    if not resource_file.exists():
        raise ValueError(msg_part_not_found(data, resource))
    return resource_file


def read_part(
    data: SourceInfo, resource: str, column_mappings: dict[str, str] | None = None
) -> pd.DataFrame:
    df = pd.read_parquet(part_file(data, resource))
    if column_mappings:
        df = df[list(column_mappings.keys())]  # only keep columns in mappings
        return df.rename(columns=column_mappings)
    else:
        return df


def read_condition(data: SourceInfo, tx: Taxonomy = DEFAULT_TAXONOMY):
    condition = read_part(
        data,
        "condition",
        {
            "subject": "subject",
            "extension.presenceAbsence.code": "presenceAbsence",
            "code.code": "condition",
            "category.code": "category",
        },
    )
    return with_readable_terms(
        condition, tx, [{"column": "presenceAbsence", "drop_nulls": True}, {"column": "condition"}]
    )


def condition_proportion(data: SourceInfo, tx: Taxonomy) -> DataPlotInfo:
    "Returns proportions of condition"
    condition = read_condition(data, tx)

    # Uses the fact that True = 1 and False = 0 in Python 3, so .mean()
    # gives the proportion of rows where condition is present amongst
    # all patients for whom the condition was recorded
    df = condition.groupby("condition").presenceAbsence.mean().reset_index()
    df = df[~pd.isna(df.presenceAbsence)].rename(columns={"presenceAbsence": "proportion"})
    return {
        "data": df,
        "type": "proportion",
        "cols": {"label": "condition"},
    }


def condition_upset(data: SourceInfo, N: int = 5) -> DataPlotInfo:
    "Returns UpSet plot data, for top `N` conditions (default 5)"
    condition = read_condition(data)[["subject", "condition", "presenceAbsence"]]

    # get top N conditions
    condition_counts = condition[condition.presenceAbsence].condition.value_counts()
    top_conditions = list(condition_counts[:N].index)
    condition = condition[condition.condition.isin(top_conditions)]

    df = condition.pivot(index="subject", columns="condition")
    df.columns = [p[1] for p in df.columns.to_flat_index()]
    return {"data": df, "type": "upset", "title": "Condition UpSet plot"}


def age_pyramid(
    data: SourceInfo,
    tx: Taxonomy = DEFAULT_TAXONOMY,
    age_bins: Sequence[int] = DEFAULT_AGE_BINS,
) -> DataPlotInfo:
    patient = with_readable_terms(
        read_part(
            data,
            "patient",
            {
                "extension.birthSex.code": "gender",
                "extension.age.value": "age",
                "extension.age.code": "age_unit",
                "id": "subject",
            },
        ),
        tx,
        [{"column": "gender"}],
    )

    encounter = with_readable_terms(
        read_part(
            data,
            "encounter",
            {"subject": "subject", "admission.dischargeDisposition.code": "outcome"},
        ),
        tx,
        [{"column": "outcome"}],
    )
    encounter["subject"] = encounter["subject"].map(lambda x: x.removeprefix("Patient/"))

    # http://unitsofmeasure.org|a represents years - drop infants
    patient = patient[patient.age_unit == "http://unitsofmeasure.org|a"]
    patient = patient.merge(encounter, on="subject", how="inner")

    # create age groups and format them as strings
    patient["age_group"] = pd.cut(patient["age"], bins=age_bins).map(
        lambda iv: f"{iv.left + 1} - {iv.right}"
    )
    patient = patient[["gender", "age_group", "outcome"]].value_counts().reset_index()

    return {
        "data": patient,
        "type": "pyramid",
        "cols": {"side": "gender", "y": "age_group", "stack_group": "outcome", "value": "count"},
    }
