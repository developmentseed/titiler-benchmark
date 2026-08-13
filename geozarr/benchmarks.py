"""Benchmark Mosaic Tiles."""

import httpx2 as httpx
import pytest

tiles = [
    {"tile": "10/538/388", "zoom": 10},
    {"tile": "11/1079/780", "zoom": 11},
    {"tile": "12/2155/1561", "zoom": 12},
    {"tile": "13/4308/3126", "zoom": 13},
    {"tile": "14/8608/6245", "zoom": 14},
]

geozarr_path = "https://s3.explorer.eopf.copernicus.eu/esa-zarr-sentinel-explorer-fra/tests-output/sentinel-2-l2a/S2B_MSIL2A_20260522T101019_N0512_R022_T32SNJ_20260522T143353.zarr/measurements/reflectance"


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
            f"http://{host}:{port}/geozarr/tiles/WebMercatorQuad/{t}.png?url={geozarr_path}&variables=b04&rescale=0,1",
            timeout=30.0,
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
            f"http://{host}:{port}/geozarr/tiles/WebMercatorQuad/{t}.png?url={geozarr_path}&variables=b04&rescale=0,1",
            timeout=30.0,
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200