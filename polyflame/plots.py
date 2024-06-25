"""
Plots
=====

Based on ISARICDraw.py:
https://github.com/ISARICResearch/VERTEX/blob/main/IsaricDraw.py
"""

import colorsys
import itertools
from collections import OrderedDict
from typing import Unpack

import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from .palettes import PALETTE_GLOBALDOTHEALTH
from .types import DataPlotInfo, PlotInfo, PlotType

DEFAULT_HEIGHT = 430
DEFAULT_FONT = "Helvetica"


def ax(cols: dict[str, str], key: str) -> str:
    return cols.get(key, key)


def get_colors(kwargs: PlotInfo) -> list[str]:
    return kwargs.get("colors") or PALETTE_GLOBALDOTHEALTH


def require_columns(
    data: pd.DataFrame, required_columns: list[str], column_mappings: dict[str, str] | None = None
) -> None:
    "Requires a set of columns to be present, raises a ValueError otherwise"
    column_mappings = column_mappings or {}
    mapped_columns = {column_mappings.get(c, c) for c in required_columns}
    if missing_columns := mapped_columns - set(data.columns):
        raise ValueError(f"Required columns or column mappings not present: {missing_columns}")


def lighten(hex_color: str, factor: float = 0.6) -> str:
    "Lightens a hex color by a fraction"
    assert 0 < factor < 1, "Factor should be a fraction between 0 and 1"
    hex_color = hex_color.lstrip("#")
    assert len(hex_color) == 6, "Invalid hex color format"
    r, g, b = (
        int(hex_color[0:2], 16) / 255.0,
        int(hex_color[2:4], 16) / 255.0,
        int(hex_color[4:6], 16) / 255.0,
    )
    hue, luminance, saturation = colorsys.rgb_to_hls(r, g, b)
    luminance = min(1, luminance + factor * (1 - luminance))
    rgb = [int(x * 255) for x in colorsys.hls_to_rgb(hue, luminance, saturation)]
    return "#" + "".join(f"{x:#04x}"[2:] for x in rgb)


def _compute_intersections(dataframe: pd.DataFrame) -> OrderedDict:
    """Find all combinations of categories and their intersection sizes
    Assumes a dataframe has only one-hot encoded (binary 0 or 1) values
    with the column labels as the categories
    """
    categories = dataframe.columns
    intersections = {}
    for r in range(1, len(categories) + 1):
        for combo in itertools.combinations(categories, r):
            # Intersection is where all categories in the combo have a 1
            mask = dataframe[list(combo)].all(axis=1)
            intersections[combo] = int(mask.sum())

    # Sort intersections by size in descending order
    return OrderedDict(sorted(intersections.items(), key=lambda x: x[1], reverse=True))


def upset(data, **kwargs: Unpack[PlotInfo]) -> go.Figure:
    """UpSet plot

    .. code-block:: text

                    Intersection size

        40           █
        30           █  █
        20           █  █     █
        10           █  █  █  █     █
        0            █  █  █  █  █  █  █

        cough        ●        ●     ●  ●
                              |     |  |
        sore throat     ●     ●  ●  |  ●
                                 |  |  |
        headache           ●     ●  ●  ●
    """
    colors = get_colors(kwargs)
    categories = data.columns
    title = kwargs.get("title", "UpSet")
    intersections = _compute_intersections(data)

    # Initialize subplots
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,  # Space between the plots
        subplot_titles=("Intersection Size", ""),  # Titles for subplots
    )

    # Create bar chart traces for intersection sizes
    bar_traces = []
    for intersection, size in intersections.items():
        if size > 0:
            bar_traces.append(
                go.Bar(
                    y=[size],
                    x=[" & ".join(intersection)],
                    orientation="v",
                    name=" & ".join(intersection),
                    marker={"color": colors[0]},
                )
            )

    # Add bar traces to the top subplot
    for trace in bar_traces:
        fig.add_trace(trace, row=1, col=1)

    # Create matrix scatter plot and lines
    for intersection, size in intersections.items():
        if size == 0:
            continue
        x_name = " & ".join(intersection)
        y_coords = [-1 - categories.get_loc(cat) for cat in categories if cat in intersection]  # type: ignore
        x_coords = [x_name] * len(y_coords)

        # Add scatter plot for each point in the intersection
        fig.add_trace(
            go.Scatter(
                x=x_coords,
                y=y_coords,
                mode="markers",
                marker=dict(size=10, color="black"),
                showlegend=False,
                hoverinfo="skip",
            ),
            row=2,
            col=1,
        )

        # Add a line connecting the points
        if len(y_coords) > 1:  # Only add a line if there are at least two points
            fig.add_trace(
                go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode="lines",
                    line=dict(color="black", width=1),
                    showlegend=False,
                    hoverinfo="skip",
                ),
                row=2,
                col=1,
            )

    # Update y-axis for the bar chart subplot
    fig.update_yaxes(title_text="Intersection Size", row=1, col=1)

    # Update y-axis for the matrix subplot to show category names instead of numeric
    fig.update_yaxes(
        tickvals=[-1 - i for i in range(len(categories))],
        ticktext=categories,
        showgrid=False,
        row=2,
        col=1,
    )

    # Hide x-axis line for the bar chart subplot
    fig.update_xaxes(showline=False, row=1, col=1)

    # Hide x-axis ticks and labels for the matrix subplot
    fig.update_xaxes(ticks="", showticklabels=False, showgrid=False, row=2, col=1)

    # Set the overall layout properties
    fig.update_layout(
        title=title,
        showlegend=False,
        height=450,
        font_family=DEFAULT_FONT,  # You may need to adjust the height
    )
    return fig


def cumulative_bar(data: pd.DataFrame, **kwargs: Unpack[PlotInfo]) -> go.Figure:
    """Pivot the DataFrame to get cumulative sums for each stack_group at each timepoint
    Ensure the 'timepoint' column is sorted or create a complete range if necessary
    """
    cols = kwargs.get("cols", {})
    require_columns(data, ["timepoint", "stack_group", "value"], cols)
    colors = get_colors(kwargs)
    timepoints = sorted(data[ax(cols, "timepoint")].unique())
    # all_timepoints = range(min(timepoints), max(timepoints) + 1)
    all_timepoints = range(int(min(timepoints)), int(max(timepoints)) + 1)

    # Create a complete DataFrame with all timepoints
    complete_df = pd.DataFrame(all_timepoints, columns=[ax(cols, "timepoint")])

    # Merge the original dataframe with the complete timepoints dataframe to fill gaps
    merged_df = pd.merge(complete_df, data, on=ax(cols, "timepoint"), how="left")

    # Pivot the merged DataFrame to get cumulative sums for each stack_group at each timepoint
    pivot_df = merged_df.pivot_table(
        index="timepoint",
        columns=ax(cols, "stack_group"),
        values=ax(cols, "value"),
        aggfunc="sum",
    )

    # Forward fill missing values and then calculate the cumulative sum
    pivot_df_ffill = pivot_df.fillna(method="ffill").cumsum()  # type: ignore

    # Create traces for each stack_group with colors from the base_color_map
    assert len(pivot_df_ffill.columns) <= len(
        colors
    ), f"Not enough colors specified, needed for\n{pivot_df_ffill.columns}\ngot {colors}"
    traces = [
        go.Bar(
            x=pivot_df_ffill.index,
            y=pivot_df_ffill[stack_group],
            name=stack_group,
            orientation="v",
            marker=dict(color=color),
        )
        for stack_group, color in zip(pivot_df_ffill.columns, colors, strict=False)
    ]

    return go.Figure(
        data=traces,
        layout=go.Layout(
            title=kwargs.get("title", "Cumulative bar chart"),
            barmode="stack",
            bargap=0,  # Set the gap between bars of the same category to 0
            xaxis=dict(title=ax(cols, "x")),
            yaxis=dict(title=ax(cols, "y")),
            legend=dict(x=1.05, y=1),
            margin=dict(l=100, r=100, t=100, b=50),
            paper_bgcolor="white",
            plot_bgcolor="white",
            height=340,
        ),
    )


def pyramid(data: pd.DataFrame, **kwargs: Unpack[PlotInfo]) -> go.Figure:
    """Dual-stack pyramid plot, used for age pyramid

    .. code-block:: text

        ↓ Age                Female       |          Male
                                          |
        91-95                             |██
        86-90                       █▒▒▒▒▒|▒▒▒▒▒█
        81-85                      ▒▒▒▒▒▒▒|▒▒▒▒▒▒▒▒██
        76-80               ██▒▒▒▒▒▒▒▒▒▒▒▒|▒▒▒▒▒████

        ██ death  ▒▒ discharged
    """
    cols = kwargs.get("cols", {})
    require_columns(data, ["side", "y", "stack_group", "value"], cols)
    colors = get_colors(kwargs)

    c_value = ax(cols, "value")
    c_side = ax(cols, "side")
    c_stack_group = ax(cols, "stack_group")
    c_y = ax(cols, "y")
    stack_groups = data[ax(cols, "stack_group")].unique()
    sides = data[ax(cols, "side")].unique()
    assert len(sides) == 2, "Dataframe must have exactly two unique values for the 'side' column"

    # Build color map
    slots = list(itertools.product(sides, stack_groups))
    assert len(slots) <= len(
        colors
    ), f"Number of provided colours ({len(colors)}) less than required ({len(slots)})"
    color_map = dict(zip(slots, colors, strict=False))

    # Prepare Data Traces
    traces = []
    max_value = data[c_value].abs().max()
    for side, stack_group in slots:
        subset = data[(data[c_side] == side) & (data[c_stack_group] == stack_group)]
        if subset.empty:
            continue
        # Get color from the color_map using both side and stack_group
        color = color_map[side, stack_group]
        traces.append(
            go.Bar(
                y=subset[c_y],
                x=(-subset[c_value] if side == sides[0] else subset[c_value]),
                name=f"{side} {stack_group}",
                orientation="h",
                marker=dict(color=color),  # Use the color from the color_map
            )
        )

    # Sorting y-axis categories
    split_ranges = [
        (int(r.split("-")[0]), int(r.split("-")[1])) for r in data[ax(cols, "y")].unique()
    ]
    sorted_ranges = sorted(split_ranges, key=lambda x: x[0])
    sorted_y_axis = [f"{start}-{end}" for start, end in sorted_ranges]

    # sorted_y_axis = sorted(dataframe['y_axis'].unique(), reverse=True)
    max_value = sum(data.groupby(c_stack_group)[c_value].apply(max))
    # Layout settings
    layout = go.Layout(
        title=kwargs.get("title", "Pyramid plot"),
        barmode="relative",
        xaxis=dict(
            title="Count",
            range=[-max_value, max_value],
            automargin=True,
            tickvals=[-max_value, -max_value / 2, 0, max_value / 2, max_value],
            ticktext=[
                max_value,
                max_value / 2,
                0,
                max_value / 2,
                max_value,
            ],  # Labels as positive numbers
        ),
        yaxis=dict(
            title="Category", automargin=True, categoryorder="array", categoryarray=sorted_y_axis
        ),
        annotations=[
            dict(
                x=(
                    0.2 if side == sides[0] else 0.8
                ),  # Position at 10%, (resp. 90%) from the left edge of the graph
                y=1.1,  # Position just above the top of the graph
                xref="paper",
                yref="paper",
                text=side,
                showarrow=False,
                font=dict(family="Arial", size=14, color="black"),
                align="center",
            )
            for side in sides
        ],
        shapes=[
            # Line at x=0 for reference
            dict(
                type="line",
                x0=0,
                y0=0,  # Start point of the line (y0=-1 to ensure it starts from the bottom)
                x1=0,
                y1=1,  # End point of the line (y1=1 to ensure it goes to the top)
                xref="x",
                yref="paper",  # Reference to x axis and paper for y axis
                line=dict(color="Black", width=2),
            )
        ],
        legend=dict(x=1.05, y=1),
        margin=dict(l=100, r=100, t=100, b=50),
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=DEFAULT_HEIGHT,
    )
    return go.Figure(data=traces, layout=layout)


def proportion(data: pd.DataFrame, **kwargs: Unpack[PlotInfo]) -> go.Figure:
    """Proportions plot by label

    .. code-block:: text

                        Frequency of signs and symptoms

              cough  ████████████████████████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
        sore throat  ████████████████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
              fever  ███████████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒

        ██ yes  ▒▒ no
    """
    cols = kwargs.get("cols", {})
    require_columns(data, ["label", "proportion"], cols)
    colors = get_colors(kwargs)
    c_label = ax(cols, "label")
    c_proportion = ax(cols, "proportion")
    dataframe = data.sort_values(by=[c_label], ascending=False)

    # Calculate the proportion of 'Yes' for each condition and sort
    condition_proportions = (
        dataframe.groupby(c_label)[c_proportion].mean().sort_values(ascending=True)
    )

    sorted_conditions = condition_proportions.index.tolist()

    # Prepare Data Traces
    traces = []
    yes_color, no_color = colors[0], lighten(colors[0])

    for condition in sorted_conditions:
        yes_count = condition_proportions[condition]
        no_count = 1 - yes_count

        # Add "Yes" bar
        traces.append(
            go.Bar(
                x=[yes_count],
                y=[condition],
                name="Yes",
                orientation="h",
                marker=dict(color=yes_color),
                showlegend=condition == sorted_conditions[0],  # Show legend only for the first
            )
        )

        # Add "No" bar
        traces.append(
            go.Bar(
                x=[no_count],
                y=[condition],
                name="No",
                orientation="h",
                marker=dict(color=no_color),
                showlegend=condition == sorted_conditions[0],  # Show legend only for the first
            )
        )

    layout = go.Layout(
        title=kwargs.get("title", "Proportion plot"),
        font_family=DEFAULT_FONT,
        barmode="stack",
        xaxis=dict(title="Proportion", range=[0, 1]),
        yaxis=dict(
            title=c_label,
            automargin=True,
            tickmode="array",
            tickvals=sorted_conditions,
            ticktext=sorted_conditions,
        ),
        bargap=0.1,  # Smaller gap between bars. Adjust this value as needed.
        legend=dict(x=1.05, y=1),
        margin=dict(l=100, r=100, t=100, b=50),
        height=350,
    )

    return go.Figure(data=traces, layout=layout)


def plot_unpacked(
    data: pd.DataFrame, type: PlotType | None, **kwargs: Unpack[PlotInfo]
) -> go.Figure | pd.DataFrame:
    """Generic plotting function dispatcher, unpacked version

    Parameters
    ----------
    data
        Data to plot
    type
        Type of plot, one of *pyramid*, *upset* or *proportion*
    **kwargs
        Additional plot parameters
    """

    if type is None:
        return data
    dispatch = {"upset": upset, "proportion": proportion, "pyramid": pyramid}
    if type not in dispatch.keys():
        raise ValueError(f"Plotting not supported for type: {type}")
    return dispatch[type](data, **kwargs)


def plot(kwargs: DataPlotInfo) -> go.Figure | pd.DataFrame:
    """Generic plotting function for PolyFLAME

    Unlike :meth:`polyflame.plot_unpacked`, this function takes a single
    dictionary as a parameter. This is used together with adapter functions
    from data sources, such as the :doc:`/api/fhirflat`.
    """
    return plot_unpacked(**kwargs)
