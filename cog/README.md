
### Start Services
```bash
docker compose up
```

### Single Tile Benchmark

```bash
uv run pytest ./cog/benchmarks.py --benchmark-sort name --benchmark-columns 'min, max, mean, median'
```

### Siege

##### Get File Info

- Get Bounds in WGS84

```
uv run --with rasterio rio bounds https://titiler-benchmark-public.s3.us-east-1.amazonaws.com/cogs/S2C_33TVF_20260928_0_L2A_B04.tif | jq -c '.bbox'

>>> [13.800550898371187,40.55670691139613,15.117031634388356,41.55184463910606]
```
- Get Min/Max Zoom

```
uv run --with rio-cogeo rio cogeo info https://titiler-benchmark-public.s3.us-east-1.amazonaws.com/cogs/S2C_33TVF_20260928_0_L2A_B04.tif --json | jq '.GEO.MinZoom, .GEO.MaxZoom'
8
14
```

###### Create Urls

```
uv run ../scripts/create_urls.py --bbox 13.800550898371187,40.55670691139613,15.117031634388356,41.55184463910606 --minzoom 8 --maxzoom 14
 8 |   794 █████
 9 |   907 ██████
10 |  1166 ███████
11 |  1150 ███████
12 |  1604 ██████████
13 |  2188 ██████████████
14 |  2188 ██████████████
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
