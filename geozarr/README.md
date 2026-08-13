
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

curl http://127.0.0.1:8081/geozarr/WebMercatorQuad/tilejson.json?url=https://s3.explorer.eopf.copernicus.eu/esa-zarr-sentinel-explorer-fra/tests-output/sentinel-2-l2a/S2B_MSIL2A_20260522T101019_N0512_R022_T32SNJ_20260522T143353.zarr/measurements/reflectance&variables=b04
```
{
  "tilejson": "3.0.0",
  "version": "1.0.0",
  "scheme": "xyz",
  "tiles": [
    "http://127.0.0.1:8081/geozarr/tiles/WebMercatorQuad/{z}/{x}/{y}?url=https%3A%2F%2Fs3.explorer.eopf.copernicus.eu%2Fesa-zarr-sentinel-explorer-fra%2Ftests-output%2Fsentinel-2-l2a%2FS2B_MSIL2A_20260522T101019_N0512_R022_T32SNJ_20260522T143353.zarr%2Fmeasurements%2Freflectance&variables=b04&tilesize=512"
  ],
  "minzoom": 11,
  "maxzoom": 14,
  "bounds": [
    8.999824909331108,
    38.75408171737615,
    10.281221171405749,
    39.75022287570616
  ],
  "center": [
    9.640523040368429,
    39.252152296541155,
    11
  ]
}
```

###### Create Urls

```
 uv run ../scripts/create_urls.py --bbox 8.999824909331108,38.75408171737615,10.281221171405749,39.75022287570616 --minzoom 10 --maxzoom 14

Downloading tiles-2026-07-26.txt.xz
10 |  1406 █████████
11 |  1386 █████████
12 |  1933 ████████████
13 |  2636 ████████████████
14 |  2636 ████████████████
wrote urls.txt with 10000 requests.
```

Note: File was edited manually to add correct path
