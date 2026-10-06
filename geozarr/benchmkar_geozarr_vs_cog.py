"""Benchmark GeoZARR Tiles."""

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

geozarr_path = "https://s3.explorer.eopf.copernicus.eu/esa-zarr-sentinel-explorer-fra/tests-output/sentinel-2-l2a/S2C_MSIL2A_20260810T125031_N0512_R095_T26SMJ_20260810T155917.zarr/measurements/reflectance"
cog_path = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/26/S/MJ/2026/8/S2C_26SMJ_20260810_0_L2A/B04.tif"

@pytest.mark.parametrize("tile", tiles)
def test_benchmark_async_titiler(benchmark, tile):
    """Benchmark async-titiler."""
    host = "0.0.0.0"
    port = "8081"

    benchmark.name = "async-geozarr (zarr-python)"
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
def test_benchmark_titiler_eopf(benchmark, tile):
    """Benchmark titiler-eopf."""
    host = "0.0.0.0"
    port = "8080"

    benchmark.name = "sync-geozarr (xarray)"
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
def test_benchmark_zarr_python_sync(benchmark, tile):
    """Benchmark titiler with zarr-python sync reader."""
    host = "0.0.0.0"
    port = "8083"

    benchmark.name = "sync-geozarr (zarr-python)"
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
def test_benchmark_sync_cog(benchmark, tile):
    """Benchmark titiler with COG."""
    host = "0.0.0.0"
    port = "8082"

    benchmark.name = "sync-cog (rasterio)"
    benchmark.group = f"Zoom {tile['zoom']}"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/cog/tiles/WebMercatorQuad/{t}.png?url={cog_path}&rescale=0,1",
            timeout=30.0,
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200


@pytest.mark.parametrize("tile", tiles)
def test_benchmark_async_cog(benchmark, tile):
    """Benchmark async-titiler with COG."""
    host = "0.0.0.0"
    port = "8081"

    benchmark.name = "async-cog (async-geotiff)"
    benchmark.group = f"Zoom {tile['zoom']}"

    def f(input_tile: dict):
        t = input_tile["tile"]
        response = httpx.get(
            f"http://{host}:{port}/geotiff/tiles/WebMercatorQuad/{t}.png?url={cog_path}&rescale=0,1",
            timeout=30.0,
        )
        assert response.status_code == 200
        return response

    response = benchmark(f, tile)
    assert response.status_code == 200