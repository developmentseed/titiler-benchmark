"""Benchmark Mosaic Tiles."""

import httpx2 as httpx
import pytest

tiles = [
    {"tile": "3/1/2", "zoom": 3},
    {"tile": "4/2/7", "zoom": 4},
    {"tile": "5/4/12", "zoom": 5},
    {"tile": "6/15/21", "zoom": 6},
    {"tile": "7/25/51", "zoom": 7},
    {"tile": "8/77/95", "zoom": 8},
    {"tile": "9/133/191", "zoom": 9},
    {"tile": "10/309/378", "zoom": 10},
    {"tile": "11/362/696", "zoom": 11},
    {"tile": "12/1169/1566", "zoom": 12},
]

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
            f"http://{host}:{port}/geotiff/tiles/WebMercatorQuad/{t}?url=https://s3.us-east-1.amazonaws.com/ds-deck.gl-raster-public/cog/Annual_NLCD_LndCov_2024_CU_C1V1.tif"
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

    benchmark.name = "titiler"
    benchmark.group = f"Zoom {tile['zoom']}"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/cog/tiles/WebMercatorQuad/{t}?url=https://s3.us-east-1.amazonaws.com/ds-deck.gl-raster-public/cog/Annual_NLCD_LndCov_2024_CU_C1V1.tif"
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200