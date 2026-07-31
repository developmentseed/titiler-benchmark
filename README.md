# titiler-benchmark

Benchmarks comparing [TiTiler](https://github.com/developmentseed/titiler)-based dynamic tiling services: request latency (via `pytest-benchmark`) and load/throughput (via `siege`).

Two scenarios are covered:

- [`cog/`](cog) — tiling a single Cloud-Optimized GeoTIFF, comparing `titiler` vs `async-titiler`.
- [`mosaic/`](mosaic) — tiling a mosaic backed by a STAC search, comparing `titiler-pgstac`, `titiler-stacapi`, and `async-titiler-stacapi`.

Each scenario has its own `docker-compose` stack, benchmark suite, and `siege` URL list — see the READMEs in [`cog/`](cog/README.md) and [`mosaic/`](mosaic/README.md) for how to run them locally.

## CI & results

On every push to `main`, [`benchmark-cog.yml`](.github/workflows/benchmark-cog.yml) and [`benchmark-mosaic.yml`](.github/workflows/benchmark-mosaic.yml) run both benchmark suites and `siege` load tests, then publish results to the [`gh-benchmarks`](https://github.com/developmentseed/titiler-benchmark/tree/gh-benchmarks) branch. On pull requests, the same workflows run to validate the change without publishing results.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Docker / Docker Compose
- [siege](https://www.joedog.org/siege-home/) for load testing

## Setup

```bash
uv sync
```
