
### Start Services
```bash
docker compose up
```

### Add items/collections to the db

```bash
uv run pypgstac load collections stac/collection.json --dsn postgresql://username:password@127.0.0.1:5439/postgis --method upsert
uv run pypgstac load items stac/items.json --dsn postgresql://username:password@127.0.0.1:5439/postgis --method upsert
```

### Single Tile Benchmark

```bash
uv run pytest benchmarks.py --benchmark-only --benchmark-columns 'min, max, mean, median'

------------------------------------------------- benchmark '0/0/0': 3 tests -------------------------------------------------
Name (time in ms)                                    Min                 Max                Mean              Median          
------------------------------------------------------------------------------------------------------------------------------
test_benchmark_titiler_stacapi[0/0/0]            64.1632 (1.0)       83.2989 (1.0)       71.7486 (1.0)       69.6973 (1.0)    
test_benchmark_titiler_pgstac[0/0/0]             71.3222 (1.11)     124.7646 (1.50)      93.7399 (1.31)      91.7501 (1.32)   
test_benchmark_async_titiler_stacapi[0/0/0]     318.8755 (4.97)     341.9364 (4.10)     331.8354 (4.62)     334.1255 (4.79)   
------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------- benchmark '1/1/1': 3 tests -------------------------------------------------
Name (time in ms)                                    Min                 Max                Mean              Median          
------------------------------------------------------------------------------------------------------------------------------
test_benchmark_titiler_pgstac[1/1/1]             29.6972 (1.0)       41.1590 (1.07)      31.9634 (1.0)       31.1920 (1.0)    
test_benchmark_titiler_stacapi[1/1/1]            30.7090 (1.03)      38.6351 (1.0)       33.1223 (1.04)      32.9485 (1.06)   
test_benchmark_async_titiler_stacapi[1/1/1]     263.5338 (8.87)     282.6375 (7.32)     273.6179 (8.56)     272.2148 (8.73)   
------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------- benchmark '2/2/1': 3 tests -------------------------------------------------
Name (time in ms)                                    Min                 Max                Mean              Median          
------------------------------------------------------------------------------------------------------------------------------
test_benchmark_async_titiler_stacapi[2/2/1]     266.0495 (1.0)      287.4706 (1.0)      274.2716 (1.0)      273.4683 (1.0)    
test_benchmark_titiler_pgstac[2/2/1]            847.5375 (3.19)     880.3944 (3.06)     868.1266 (3.17)     875.3892 (3.20)   
test_benchmark_titiler_stacapi[2/2/1]           854.5350 (3.21)     898.7240 (3.13)     873.1273 (3.18)     862.1720 (3.15)   
------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------- benchmark '3/5/0': 3 tests -------------------------------------------------
Name (time in ms)                                    Min                 Max                Mean              Median          
------------------------------------------------------------------------------------------------------------------------------
test_benchmark_titiler_pgstac[3/5/0]             14.1279 (1.0)       30.1204 (1.0)       19.2145 (1.0)       16.8826 (1.0)    
test_benchmark_titiler_stacapi[3/5/0]            16.6356 (1.18)      31.2987 (1.04)      20.7091 (1.08)      17.5456 (1.04)   
test_benchmark_async_titiler_stacapi[3/5/0]     243.0845 (17.21)    265.3738 (8.81)     251.0332 (13.06)    246.6472 (14.61)  
------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------- benchmark '4/5/9': 3 tests -------------------------------------------------
Name (time in ms)                                    Min                 Max                Mean              Median          
------------------------------------------------------------------------------------------------------------------------------
test_benchmark_async_titiler_stacapi[4/5/9]     281.6508 (1.0)      295.2731 (1.0)      286.8887 (1.0)      284.3375 (1.0)    
test_benchmark_titiler_pgstac[4/5/9]            627.2938 (2.23)     662.6028 (2.24)     640.0514 (2.23)     638.5174 (2.25)   
test_benchmark_titiler_stacapi[4/5/9]           632.8369 (2.25)     646.2678 (2.19)     637.1334 (2.22)     635.8749 (2.24)   
------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------- benchmark '5/16/5': 3 tests -------------------------------------------------
Name (time in ms)                                     Min                 Max                Mean              Median          
-------------------------------------------------------------------------------------------------------------------------------
test_benchmark_titiler_stacapi[5/16/5]            12.7852 (1.0)       37.3820 (1.55)      18.3430 (1.06)      13.7278 (1.0)    
test_benchmark_titiler_pgstac[5/16/5]             13.6565 (1.07)      24.0522 (1.0)       17.3714 (1.0)       17.5528 (1.28)   
test_benchmark_async_titiler_stacapi[5/16/5]     244.6688 (19.14)    248.9292 (10.35)    247.2971 (14.24)    247.6630 (18.04)  
-------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------- benchmark '6/43/31': 3 tests -------------------------------------------------
Name (time in ms)                                      Min                 Max                Mean              Median          
--------------------------------------------------------------------------------------------------------------------------------
test_benchmark_titiler_stacapi[6/43/31]            11.9514 (1.0)       25.8760 (1.0)       16.7842 (1.0)       15.0856 (1.0)    
test_benchmark_titiler_pgstac[6/43/31]             13.2171 (1.11)      35.0983 (1.36)      21.2652 (1.27)      19.5410 (1.30)   
test_benchmark_async_titiler_stacapi[6/43/31]     272.5744 (22.81)    360.0397 (13.91)    309.0282 (18.41)    278.0677 (18.43)  
--------------------------------------------------------------------------------------------------------------------------------
```

### Siege
```
# 50 concurrents / repeat 10 times (500 tiles)
$ siege --file urls.txt -b -c 50 -r 10

Transactions:                 500    hits
Availability:                 100.00 %
Elapsed time:                   7.83 secs
Data transferred:               5.84 MB
Response time:                764.02 ms
Transaction rate:              63.86 trans/sec
Throughput:                     0.75 MB/sec
Concurrency:                   48.79
Successful transactions:      500
Failed transactions:            0
Longest transaction:         1110.00 ms
Shortest transaction:         400.00 ms


# 10 concurrents / repeat 100 times (1000 tiles)
$ siege --file urls.txt -b -c 10 -r 100

Transactions:                1000    hits
Availability:                 100.00 %
Elapsed time:                  20.12 secs
Data transferred:              11.46 MB
Response time:                196.11 ms
Transaction rate:              49.70 trans/sec
Throughput:                     0.57 MB/sec
Concurrency:                    9.75
Successful transactions:     1000
Failed transactions:            0
Longest transaction:          420.00 ms
Shortest transaction:          80.00 ms


# 200 concurrents / repeat 1 time (200 tiles)
$ siege --file urls.txt -b -c 200 -r 1

Transactions:                 200    hits
Availability:                 100.00 %
Elapsed time:                   3.18 secs
Data transferred:               2.16 MB
Response time:               2285.35 ms
Transaction rate:              62.89 trans/sec
Throughput:                     0.68 MB/sec
Concurrency:                  143.73
Successful transactions:      200
Failed transactions:            0
Longest transaction:         3180.00 ms
Shortest transaction:         820.00 ms
```
