"""IO dependencies."""

from __future__ import annotations

import numpy
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pydantic import AfterValidator
from pydantic.types import StringConstraints
from typing import TYPE_CHECKING, Annotated, Any, Literal
from cachetools import TTLCache, cached
from fastapi import Query
from threading import Lock
from obstore.store import HTTPStore
import zarr

from zarr.storage import ObjectStore

from titiler.core.dependencies import DefaultDependency, ExpressionParams

from rio_tiler.experimental.zarr import Selector
from rio_tiler.types import RIOResampling, WarpResampling

ttl_cache = TTLCache(maxsize=512, ttl=300)


@cached(ttl_cache, lock=Lock())
def _get_geozarr(url: str) -> zarr.cGroup:
    """Create GeoZarr Group from url"""
    store = HTTPStore(url)
    zarr_store = ObjectStore(store=store, read_only=True)
    return zarr.open_group(store=zarr_store, mode="r", zarr_format=3, use_consolidated=True)


def GeoZARRPathParams(
    url: Annotated[str, Query(description="GeoZarr store URL")],
) -> zarr.Group:
    """Create dataset path from args"""
    return _get_geozarr(url)


def _parse_sel(sel: list[str] | None) -> Sequence[Selector]:
    """Parse sel DSL into dictionary.

    Args:
        sel (list of str, optional): List of Selector DSL strings.

    Returns:
        list: list of dimension/values/method.

    """
    sel = sel or []

    _idx: dict[str, Any] = {}
    for s in sel:
        val: str | slice
        dim, val = s.split("=")

        if dim in _idx:
            _idx[dim].append(val)
        else:
            _idx[dim] = [val]

    # Loop through all dimension=values selectors
    # - parse method::value if provided
    # - check if multiple methods are provided for the same dimension
    # - cast values to the dimension dtype
    # - apply the selection
    selectors: list[Selector] = []
    for dimension, values in _idx.items():
        methods, values = zip(  # type: ignore
            *[v.split("::", 1) if "::" in v else (None, v) for v in values]
        )
        method_sets = {m for m in methods if m is not None}
        if len(method_sets) > 1:
            raise ValueError(
                f"Multiple selection methods provided for dimension {dimension}: {methods}"
            )
        method = method_sets.pop() if method_sets else None

        selectors.append(
            {
                "dimension": dimension,
                "values": list(values) if len(values) > 1 else list(values)[0],
                "method": method,
            }
        )

    return selectors


def _parse_reduce(
    reducers: list[str] | None,
) -> list[tuple[str, Callable[..., numpy.ma.MaskedArray]]]:
    """Parse reduce DSL into list of reducers.

    Args:
        reducers (list of str, optional): List of Reducer DSL strings.

    Returns:
        list: list of (dimension, reducer function) tuples.

    """
    if not reducers:
        return []

    REDUCERS = {
        "mean": numpy.ma.mean,
        "median": numpy.ma.median,
        "sum": numpy.ma.sum,
        "prod": numpy.ma.prod,
        "min": numpy.ma.min,
        "max": numpy.ma.max,
        "std": numpy.ma.std,
        "var": numpy.ma.var,
        "count": numpy.ma.count,
    }

    return [
        (reducer.split("::")[0], REDUCERS[reducer.split("::")[1]])
        for reducer in reducers
    ]


SelDimStr = Annotated[
    str,
    StringConstraints(
        pattern=r"^[^=]+=((nearest|pad|ffill|backfill|bfill)::)?([^=:]|:[^:])+$"
    ),
]

ReduceDimStr = Annotated[
    str,
    StringConstraints(
        pattern=r"^([^:]|:[^:])+::(mean|median|sum|prod|min|max|std|var|count)$"
    ),
]


@dataclass
class VariablesParams(DefaultDependency):
    """Zarr Dataset Options."""

    variables: Annotated[
        list[str],
        Query(description="Zarr Array name."),
    ]


@dataclass
class GeoZarrLayerParams(ExpressionParams, VariablesParams):
    """variable + expression + sel."""

    sel: Annotated[
        list[SelDimStr] | None,
        AfterValidator(_parse_sel),
        Query(
            description="GeoZarr Indexing using dimension names `{dimension}={value}` or `{dimension}={method}::{value}`.",
        ),
    ] = None

    reduce: Annotated[
        list[ReduceDimStr] | None,
        AfterValidator(_parse_reduce),
        Query(
            description="GeoZarr Reduction using dimension names `{dimension}={method}::{value}`.",
        ),
    ] = None

@dataclass
class GeoZarrDatasetParams(DefaultDependency):
    """GeoZarr dataset parameters."""

    nodata: Annotated[
        Literal["nan", "inf", "-inf"] | int | float | None,
        AfterValidator(lambda v: numpy.nan if v == "nan" else float(v)),
        Query(
            title="Nodata value",
            description="Overwrite internal Nodata value; nan or valid float values only.",
        ),
    ] = None
    resampling_method: Annotated[
        RIOResampling | None,
        Query(
            alias="resampling",
            description="RasterIO resampling algorithm. Defaults to `nearest`.",
        ),
    ] = None
    reproject_method: Annotated[
        WarpResampling | None,
        Query(
            alias="reproject",
            description="WarpKernel resampling algorithm (only used when doing re-projection). Defaults to `nearest`.",
        ),
    ] = None
