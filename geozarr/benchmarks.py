"""Benchmark GeoZARR Tiles."""

import httpx2 as httpx
import pytest

tiles = [
    {"tile": "9/276/191", "zoom": 9},
    {"tile": "10/553/383", "zoom": 10},
    {"tile": "11/1106/767", "zoom": 11},
    {"tile": "12/2212/1534", "zoom": 12},
    {"tile": "13/4424/3069", "zoom": 13},
    {"tile": "14/8849/6139", "zoom": 14},
]

geozarr_path = "https://titiler-benchmark-public.s3.us-east-1.amazonaws.com/geozarrs/S2C_MSIL2A_20260928T095031_N0513_R079_T33TVF_20260928T130916.zarr/measurements/reflectance"


@pytest.mark.parametrize("tile", tiles)
@pytest.mark.benchmark(
    min_rounds=10,
    warmup=True,
    warmup_iterations=1
)
def test_benchmark_async_titiler(benchmark, tile):
    """Benchmark async-titiler."""
    host = "0.0.0.0"
    port = "8081"

    benchmark.name = "async (zarr-python)"
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
@pytest.mark.benchmark(
    min_rounds=10,
    warmup=True,
    warmup_iterations=1
)
def test_benchmark_titiler_zarr_python(benchmark, tile):
    """Benchmark titiler with zarr-python sync reader."""
    host = "0.0.0.0"
    port = "8083"

    benchmark.name = "sync (zarr-python)"
    benchmark.group = f"Zoom {tile['zoom']}"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/tiles/WebMercatorQuad/{t}.png?url={geozarr_path}&variables=b04&rescale=0,1",
            timeout=30.0,
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200


@pytest.mark.parametrize("tile", tiles)
@pytest.mark.benchmark(
    min_rounds=10,
    warmup=True,
    warmup_iterations=1
)
def test_benchmark_titiler_eopf(benchmark, tile):
    """Benchmark titiler-eopf."""
    host = "0.0.0.0"
    port = "8080"

    benchmark.name = "sync (xarray)"
    benchmark.group = f"Zoom {tile['zoom']}"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/tiles/WebMercatorQuad/{t}.png?url={geozarr_path}&variables=b04&rescale=0,1",
            timeout=30.0,
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200