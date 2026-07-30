"""Benchmark items."""

import os

import httpx2 as httpx
import pytest

tiles = [
    "0/0/0",
    "1/1/1",
    "2/2/1",
    "3/5/0",
    "4/5/9",
    "5/16/5",
    "6/43/31",
]

@pytest.mark.parametrize("tile", tiles)
def test_benchmark_async_titiler_stacapi(benchmark, tile):
    """Benchmark async-titiler-stacapi."""
    host = "0.0.0.0"
    port = "8082"

    benchmark.group = tile

    def f(input_tile):
        response = httpx.get(
            f"http://{host}:{port}/collections/world/tiles/WebMercatorQuad/{input_tile}?assets=asset"
        )
        assert response.status_code == 200
        return response

    _ = httpx.get(f"http://{host}:{port}/collections/world/info")

    response = benchmark(f, tile)
    assert response.status_code == 200


@pytest.mark.parametrize("tile", tiles)
def test_benchmark_titiler_stacapi(benchmark, tile):
    """Benchmark titiler-stacapi."""
    host = "0.0.0.0"
    port = "8081"

    benchmark.group = tile

    def f(input_tile):
        response = httpx.get(
            f"http://{host}:{port}/collections/world/tiles/WebMercatorQuad/{input_tile}?assets=asset"
        )
        assert response.status_code == 200
        return response

    _ = httpx.get(f"http://{host}:{port}/collections/world/info")

    response = benchmark(f, tile)
    assert response.status_code == 200


@pytest.mark.parametrize("tile", tiles)
def test_benchmark_titiler_pgstac(benchmark, tile):
    """Benchmark titiler-pgstac."""
    host = "0.0.0.0"
    port = "8080"

    benchmark.group = tile

    def f(input_tile):
        response = httpx.get(
            f"http://{host}:{port}/collections/world/tiles/WebMercatorQuad/{input_tile}?assets=asset"
        )
        assert response.status_code == 200
        return response

    _ = httpx.get(f"http://{host}:{port}/collections/world/info")

    response = benchmark(f, tile)
    assert response.status_code == 200