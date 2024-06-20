from pathlib import Path
from typing import Literal, TypedDict

import pandas as pd

PlotType = Literal["pyramid", "upset", "proportion"]
Taxonomy = dict[str, dict[str, str]]


class SourceInfo(TypedDict):
    n: int | None
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


DataPlotTuple = tuple[pd.DataFrame, PlotInfo]
