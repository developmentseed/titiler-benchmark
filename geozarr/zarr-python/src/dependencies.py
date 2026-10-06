"""IO dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated
from cachetools import TTLCache, cached
from fastapi import Query
from threading import Lock
from obstore.store import HTTPStore
import zarr

from zarr.storage import ObjectStore

from titiler.core.dependencies import DefaultDependency, ExpressionParams


ttl_cache = TTLCache(maxsize=512, ttl=300)


@cached(ttl_cache, lock=Lock())
def _get_geozarr(url: str) -> zarr.cGroup:
    """Create GeoZarr Group from url"""
    store = HTTPStore(url)
    zarr_store = ObjectStore(store=store, read_only=True)
    return zarr.open_group(store=zarr_store, mode="r")


def GeoZARRPathParams(
    url: Annotated[str, Query(description="GeoZarr store URL")],
) -> zarr.Group:
    """Create dataset path from args"""
    return _get_geozarr(url)


@dataclass
class VariablesParams(DefaultDependency):
    """Zarr Dataset Options."""

    variables: Annotated[
        list[str],
        Query(description="Zarr Array name."),
    ]


@dataclass
class LayerParams(ExpressionParams, VariablesParams):
    """variable + expression."""
