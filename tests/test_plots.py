"""
Tests for polyflame.plots
"""

from collections import OrderedDict

import pandas as pd
import pytest

from polyflame.plots import (
    ax,
    get_colors,
    require_columns,
    lighten,
    _compute_intersections,
)


def test_ax():
    assert ax({"hello": "world"}, "hello") == "world"
    assert ax({"there": "something"}, "hello") == "hello"


def test_get_colors():
    assert get_colors({"colors": ["red", "blue"]}) == ["red", "blue"]


def test_require_columns():
    df = pd.DataFrame({"id": [1, 2], "label": ["hello", "world"]})
    require_columns(df, ["x", "y"], {"x": "id", "y": "label"})


def test_require_columns_exception():
    df = pd.DataFrame({"id": [1, 2], "label": ["hello", "world"]})
    with pytest.raises(ValueError):
        require_columns(df, ["x", "y"], {"x": "id"})


def test_lighten():
    assert lighten("#000000") == "#999999"


def test_compute_intersections():
    df = pd.DataFrame({"headache": [1, 1, 0], "diabetes": [0, 1, 0], "hypertension": [0, 1, 1]})
    assert _compute_intersections(df) == OrderedDict(
        {
            ("headache",): 2,
            ("hypertension",): 2,
            ("diabetes",): 1,
            ("headache", "diabetes"): 1,
            ("headache", "hypertension"): 1,
            ("diabetes", "hypertension"): 1,
            ("headache", "diabetes", "hypertension"): 1,
        }
    )
