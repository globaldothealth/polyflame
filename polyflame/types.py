from pathlib import Path
from typing import Literal, Required, TypedDict

import pandas as pd

PlotType = Literal["pyramid", "upset", "proportion"]
Taxonomy = dict[str, dict[str, str | bool]]


class ReadableTermColumnInfo(TypedDict, total=False):
    term_column: Required[str]
    taxonomy_section: str
    drop_nulls: bool


class SourceInfo(TypedDict):
    N: int | None
    path: Path
    checksum: str
    checksum_file: str


class PlotInfo(TypedDict, total=False):
    """TypedDict passed to plotting functions"""

    title: str
    cols: dict[str, str]
    colors: list[str]
    colorSequential: str
    xlabel: str
    ylabel: str


class DataPlotInfo(PlotInfo):
    data: pd.DataFrame
    type: PlotType | None
