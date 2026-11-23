
### Start Services
```bash
docker compose up
```

### Single Tile Benchmark

```bash
uv run pytest ./geozarr/benchmarks.py --benchmark-sort name --benchmark-columns 'min, max, mean, median'
```

### Siege

##### Get File Info

docker compose -f docker-compose.geozarr.yml up

curl http://127.0.0.1:8081/geozarr/WebMercatorQuad/tilejson.json?url=https://titiler-benchmark-public.s3.us-east-1.amazonaws.com/geozarrs/S2C_MSIL2A_20260928T095031_N0513_R079_T33TVF_20260928T130916.zarr/measurements/reflectance&variables=b04
```
{
    "tilejson": "3.0.0",
    "version": "1.0.0",
    "scheme": "xyz",
    "tiles": [
        "http://127.0.0.1:8080/geozarr/tiles/WebMercatorQuad/{z}/{x}/{y}?url=https%3A%2F%2Ftitiler-benchmark-public.s3.us-east-1.amazonaws.com%2Fgeozarrs%2FS2C_MSIL2A_20260928T095031_N0513_R079_T33TVF_20260928T130916.zarr%2Fmeasurements%2Freflectance&variables=b04&rescale=0%2C1&tilesize=256"
    ],
    "minzoom": 7,
    "maxzoom": 14,
    "bounds": [
        13.800611666448079,
        40.55675255041855,
        15.116971598590371,
        41.55179960109687
    ],
    "center": [
        14.458791632519225,
        41.05427607575771,
        7
    ]
}
```

###### Create Urls

```
uv run ../scripts/create_urls.py --bbox 13.800611666448079,40.55675255041855,15.116971598590371,41.55179960109687 --minzoom 7 --maxzoom 14

Downloading tiles-2026-07-26.txt.xz
 7 |   623 ████
 8 |   744 █████
 9 |   851 ██████
10 |  1094 ███████
11 |  1079 ███████
12 |  1504 ██████████
13 |  2051 █████████████
14 |  2051 █████████████
wrote urls.txt with 10000 requests.
```

Note: File was edited manually to add correct path
