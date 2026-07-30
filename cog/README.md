
### Start Services
```bash
docker compose up
```

### Single Tile Benchmark

```bash
uv run pytest benchmarks.py --benchmark-columns 'min, max, mean, median' --benchmark-sort name
```

### Siege

##### Get File Info

- Get Bounds in WGS84

```
uv run --with rasterio rio bounds https://s3.us-east-1.amazonaws.com/ds-deck.gl-raster-public/cog/Annual_NLCD_LndCov_2024_CU_C1V1.tif | jq -c '.bbox'

>>> [-129.27731989810937,21.80509522554448,-63.11842952142922,52.92171973385814]
```
- Get Min/Max Zoom

```
uv run --with rio-cogeo rio cogeo info https://s3.us-east-1.amazonaws.com/ds-deck.gl-raster-public/cog/Annual_NLCD_LndCov_2024_CU_C1V1.tif --json | jq '.GEO.MinZoom, .GEO.MaxZoom'
warning: `VIRTUAL_ENV=/Users/vincentsarago/Dev/venv/python3.14` does not match the project environment path `/Users/vincentsarago/Dev/Devseed/titiler-benchmark/.venv` and will be ignored; use `--active` to target the active environment instead
3
12
```

###### Create Urls

```
uv run ../scripts/create_urls.py --bbox -129.27731989810937,21.80509522554448,-63.11842952142922,52.92171973385814 --minzoom 3 --maxzoom 12
 3 |   249 ██
 4 |   332 ██
 5 |   561 ████
 6 |   790 █████
 7 |   852 ██████
 8 |  1018 ███████
 9 |  1164 ███████
10 |  1496 █████████
11 |  1476 █████████
12 |  2058 █████████████
wrote urls.txt with 10000 requests.
```

Note: File was edited manually to add correct path

```
# 10 concurrents / repeat 200 times (2000 tiles)

# TiTiler
$ URLPATH=cog/tiles/WebMercatorQuad/ PORT=8080 HOST=127.0.0.1 siege --file urls.txt -b -c 10 -r 200 

Transactions:                2000    hits
Availability:                 100.00 %
Elapsed time:                  87.10 secs
Data transferred:              41.70 MB
Response time:                309.08 ms
Transaction rate:              22.96 trans/sec
Throughput:                     0.48 MB/sec
Concurrency:                    7.10
Successful transactions:     1845
Failed transactions:            0
Longest transaction:         1390.00 ms
Shortest transaction:           0.00 ms
 
# Async-TiTiler
$ URLPATH=geotiff/tiles/WebMercatorQuad/ PORT=8081 HOST=127.0.0.1 siege --file urls.txt -b -c 10 -r 200

Transactions:                2000    hits
Availability:                 100.00 %
Elapsed time:                  80.95 secs
Data transferred:              40.15 MB
Response time:                360.60 ms
Transaction rate:              24.71 trans/sec
Throughput:                     0.50 MB/sec
Concurrency:                    8.91
Successful transactions:     1845
Failed transactions:            0
Longest transaction:         3780.00 ms
Shortest transaction:           0.00 ms
```
