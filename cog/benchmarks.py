"""Benchmark Mosaic Tiles."""

import httpx2 as httpx
import pytest

tiles = [
    {"tile": "9/216/195", "zoom": 9},
    {"tile": "10/432/391", "zoom": 10},
    {"tile": "11/867/783", "zoom": 11},
    {"tile": "12/1736/1567", "zoom": 12},
    {"tile": "13/3475/3136", "zoom": 13},
    {"tile": "14/6917/6257", "zoom": 14},
]

cog_path = "https://titiler-benchmark-public.s3.us-east-1.amazonaws.com/cogs/S2C_26SMJ_20260810_0_L2A_B04.tif"


@pytest.mark.parametrize("tile", tiles)
def test_benchmark_async_titiler(benchmark, tile):
    """Benchmark async-titiler."""
    host = "0.0.0.0"
    port = "8081"

    benchmark.name = "async"
    benchmark.group = f"Zoom {tile['zoom']}"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/geotiff/tiles/WebMercatorQuad/{t}?url={cog_path}&rescale=0,1"
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200


@pytest.mark.parametrize("tile", tiles)
def test_benchmark_titiler(benchmark, tile):
    """Benchmark titiler."""
    host = "0.0.0.0"
    port = "8080"

    benchmark.name = "sync"
    benchmark.group = f"Zoom {tile['zoom']}"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/cog/tiles/WebMercatorQuad/{t}?url={cog_path}&rescale=0,1"
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200