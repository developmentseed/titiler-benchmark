
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

curl http://127.0.0.1:8081/geozarr/WebMercatorQuad/tilejson.json?url=https://s3.explorer.eopf.copernicus.eu/esa-zarr-sentinel-explorer-fra/tests-output/sentinel-2-l2a/S2C_MSIL2A_20260810T125031_N0512_R095_T26SMJ_20260810T155917.zarr/measurements/reflectance&variables=b04
```
{
    "tilejson": "3.0.0",
    "version": "1.0.0",
    "scheme": "xyz",
    "tiles": [
        "http://127.0.0.1:8080/geozarr/tiles/WebMercatorQuad/{z}/{x}/{y}?url=https%3A%2F%2Fs3.explorer.eopf.copernicus.eu%2Fesa-zarr-sentinel-explorer-fra%2Ftests-output%2Fsentinel-2-l2a%2FS2C_MSIL2A_20260810T125031_N0512_R095_T26SMJ_20260810T155917.zarr%2Fmeasurements%2Freflectance&variables=b04&rescale=0%2C1&tilesize=256"
    ],
    "minzoom": 9,
    "maxzoom": 14,
    "bounds": [
        -28.167565620738376,
        38.75523942126389,
        -26.886132807443722,
        39.75022284588649
    ],
    "center": [
        -27.52684921409105,
        39.25273113357519,
        9
    ]
}
```

###### Create Urls

```
uv run ../scripts/create_urls.py --bbox -28.167565620738376,38.75523942126389,-26.886132807443722,39.75022284588649 --minzoom 9 --maxzoom 14

Downloading tiles-2026-07-26.txt.xz
 9 |   985 ██████
10 |  1267 ████████
11 |  1250 ████████
12 |  1742 ███████████
13 |  2376 ███████████████
14 |  2376 ███████████████
wrote urls.txt with 10000 requests.
```

Note: File was edited manually to add correct path
