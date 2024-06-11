from pathlib import Path
from typing import Literal, TypedDict

PlotType = Literal["pyramid", "upset", "proportion"]


class SourceInfo(TypedDict):
    id: str
    N: int
    checksum: str
    path: Path | str | None


class PlotInfo(TypedDict, total=False):
    """TypedDict passed to plotting functions"""

    title: str
    cols: dict[str, str]
    colors: list[str]
    colorSequential: str
    xlabel: str
    ylabel: str
