"""Benchmark Mosaic Tiles."""

import httpx2 as httpx
import pytest

tiles = [
    {"tile": "0/0/0", "zoom": 0, "assets": 15},   # 15 Assets
    {"tile": "1/1/1", "zoom": 1, "assets": 6},   # 6 Assets
    {"tile": "2/2/1", "zoom": 2, "assets": 4},   # 4 Assets
    {"tile": "3/5/0", "zoom": 3, "assets": 2},   # 2 Assets 
    {"tile": "4/5/9", "zoom": 4, "assets": 1},   # 1 Asset
    {"tile": "5/16/5", "zoom": 5, "assets": 1},   # 1 Asset
    {"tile": "6/43/31", "zoom": 6, "assets": 1},  # 1 Asset
]

@pytest.mark.parametrize("tile", tiles)
def test_benchmark_async_titiler_stacapi(benchmark, tile):
    """Benchmark async-titiler-stacapi."""
    host = "0.0.0.0"
    port = "8082"

    benchmark.name = "async"
    benchmark.group = f"Zoom {tile['zoom']} - {tile['assets']} Assets"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/collections/world/tiles/WebMercatorQuad/{t}?assets=asset"
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

    benchmark.name = "stacapi"
    benchmark.group = f"Zoom {tile['zoom']} - {tile['assets']} Assets"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/collections/world/tiles/WebMercatorQuad/{t}?assets=asset"
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

    benchmark.name = "pgstac"
    benchmark.group = f"Zoom {tile['zoom']} - {tile['assets']} Assets"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/collections/world/tiles/WebMercatorQuad/{t}?assets=asset"
        )
        assert response.status_code == 200
        return response

    _ = httpx.get(f"http://{host}:{port}/collections/world/info")

    response = benchmark(f, tile)
    assert response.status_code == 200