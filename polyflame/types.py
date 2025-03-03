"""
Types
=====

Types used throughout polyflame
"""

import sys
from pathlib import Path
from typing import Literal, TypedDict

if sys.version_info < (3, 11):
    from typing_extensions import Required  # pragma: no cover
else:
    from typing import Required  # pragma: no cover

import pandas as pd

PlotType = Literal["pyramid", "upset", "proportion"]
Taxonomy = dict[str, dict[str, str | bool]]


class ReadableTermColumnInfo(TypedDict, total=False):
    """Dictionary type defining the mapping from term columns to
    readable names in a taxonomy"""

    term_column: Required[str]
    "Column in data that should be mapped from codes to readable names"
    taxonomy_section: str
    """Section in taxonomy file that should be used for mapping.
    If not given, this is taken to be the same as ``term_column``"""
    drop_nulls: bool
    """Whether rows containing nulls (after mapping) should be dropped
    from the data, by default, rows are not dropped"""


class SourceInfo(TypedDict):
    "Source information for analysis functions to load data"

    N: int | None
    "Number of patients"
    path: Path
    "Path where source is located"
    checksum: str
    "Data integrity checksum"
    checksum_file: str
    "File for which data integrity checksum is calculated"


class PlotInfo(TypedDict, total=False):
    """Dictionary passed to plotting functions"""

    title: str
    "Title of plot"
    cols: dict[str, str]
    "Column mappings from the column types expected to the actual column names in data"
    colors: list[str]
    "Color palette to use, must be a list of valid RGB color hex codes, with an appropriate length"
    colorSequential: str
    "Palette name to use for sequential colors"
    xlabel: str
    "Label for x-axis"
    ylabel: str
    "Label for y-axis"


class DataPlotInfo(PlotInfo):
    "Extension of :py:class:`polyflame.types.PlotInfo` to add data and plot type"

    data: pd.DataFrame
    "Data corresponding to the plot"
    type: PlotType | None
    "Type of plot"
