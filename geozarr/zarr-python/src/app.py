"""titiler.eopf Application."""

from typing import Annotated, Any, Literal
from collections.abc import Callable
from attrs import define
from fastapi import Depends, FastAPI, Query, Path
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware
from titiler.core.dependencies import DefaultDependency, ImageRenderingParams, CoordCRSParams
from titiler.core.factory import BaseFactory
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image
from rio_tiler.experimental.zarr import GroupReader
from rio_tiler.constants import WGS84_CRS
import zarr
from starlette.responses import HTMLResponse, Response
from starlette.requests import Request
from pydantic import Field
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets
from urllib.parse import urlencode
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.responses import Point
from titiler.core.resources.responses import JSONResponse

from .dependencies import GeoZARRPathParams, VariablesParams

@define(kw_only=True)
class TilerFactory(BaseFactory):
    """Tiler Factory."""

    # Default reader is set to rio_tiler.io.Reader
    reader: type[GroupReader] = GroupReader

    # Path Dependency
    path_dependency: Callable[..., zarr.Group] = GeoZARRPathParams

    # Indexes/Expression Dependencies
    layer_dependency: type[DefaultDependency] = VariablesParams

    render_dependency: type[DefaultDependency] = ImageRenderingParams

    # TileMatrixSet dependency
    supported_tms: TileMatrixSets = morecantile_tms

    render_func: Callable[..., tuple[bytes, str]] = render_image

    def register_routes(self):
        self.tile()
        self.tilejson()
        self.point()
        self.map_viewer()

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoint."""

        available_tms = tuple(self.supported_tms.list())
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}",
            operation_id=f"{self.operation_prefix}getTile",
            responses={
                200: {
                    "content": {
                        "image/png": {},
                        "image/jpeg": {},
                        "image/jpg": {},
                        "image/webp": {},
                        "image/jp2": {},
                        "image/tiff; application=geotiff": {},
                        "application/x-binary": {},
                    },
                    "description": "Return an image.",
                }
            },
            response_class=Response,
        )
        @self.router.get(
            "/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
            operation_id=f"{self.operation_prefix}getTileWithFormat",
            responses={
                200: {
                    "content": {
                        "image/png": {},
                        "image/jpeg": {},
                        "image/jpg": {},
                        "image/webp": {},
                        "image/jp2": {},
                        "image/tiff; application=geotiff": {},
                        "application/x-binary": {},
                    },
                    "description": "Return an image.",
                }
            },
            response_class=Response,
        )
        def tile(
            z: Annotated[
                int,
                Path(
                    description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
                ),
            ],
            x: Annotated[
                int,
                Path(
                    description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
                ),
            ],
            y: Annotated[
                int,
                Path(
                    description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
                ),
            ],
            tileMatrixSetId: Annotated[
                Literal[available_tms],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            format: Annotated[
                ImageType | None,
                Field(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
                ),
            ] = None,
            tilesize: Annotated[
                int | None,
                Query(gt=0, description="Tilesize in pixels."),
            ] = None,
            dataset=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            render_params=Depends(self.render_dependency),
        ):
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)

            with self.reader(input=dataset, tms=tms) as src_dst:
                image = src_dst.tile(
                    x,
                    y,
                    z,
                    tilesize=tilesize,
                    **layer_params.as_dict(),
                )

            content, media_type = self.render_func(
                image,
                output_format=format,
                **render_params.as_dict(),
            )

            return Response(content, media_type=media_type)

    def tilejson(self):  # noqa: C901
        """Register /tilejson.json endpoint."""

        @self.router.get(
            "/{tileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
            operation_id=f"{self.operation_prefix}getTileJSON",
        )
        def tilejson(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            tilesize: Annotated[
                int | None,
                Query(gt=0, description="Tilesize in pixels. Default to 512."),
            ] = 512,
            tile_format: Annotated[
                ImageType | None,
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            minzoom: Annotated[
                int | None,
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                int | None,
                Query(description="Overwrite default maxzoom."),
            ] = None,
            dataset=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            render_params=Depends(self.render_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "tileMatrixSetId": tileMatrixSetId,
            }
            if tile_format:
                route_params["format"] = tile_format.value
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "minzoom",
                "maxzoom",
            ]
            qs: list[tuple[str, Any]] = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if "tilesize" not in request.query_params:
                qs.append(("tilesize", str(tilesize)))
            tiles_url += f"?{urlencode(qs)}"

            tms = self.supported_tms.get(tileMatrixSetId)
            with self.reader(dataset, tms=tms) as src_dst:
                body = {
                    "bounds": src_dst.get_geographic_bounds(tms.rasterio_geographic_crs),
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "tiles": [tiles_url],
                    "attribution": "titiler with zarr-python",
                }

                # Custom TiTiler tilejson fields
                info = src_dst.info()
                body["band_descriptions"] = getattr(info, "band_descriptions", None)
                body["data_type"] = getattr(info, "dtype", None)
                body["minmax"] = getattr(info, "minmax", None)

            return body

    ############################################################################
    # /point
    ############################################################################
    def point(self):
        """Register /point endpoints."""

        @self.router.get(
            "/point/{lon},{lat}",
            response_model=Point,
            response_class=JSONResponse,
            responses={200: {"description": "Return a value for a point"}},
            operation_id=f"{self.operation_prefix}getDataForPoint",
        )
        def point(
            lon: Annotated[float, Path(description="Longitude")],
            lat: Annotated[float, Path(description="Latitude")],
            dataset=Depends(self.path_dependency),
            coord_crs=Depends(CoordCRSParams),
            layer_params=Depends(self.layer_dependency),
        ):
            """Get Point value for a dataset."""
            with self.reader(dataset) as src_dst:
                pts = src_dst.point(
                    lon,
                    lat,
                    coord_crs=coord_crs or WGS84_CRS,
                    **layer_params.as_dict(),
                )

            return {
                "coordinates": [lon, lat],
                "values": pts.array.tolist(),
                "band_names": pts.band_names,
                "band_descriptions": pts.band_descriptions,
            }


    def map_viewer(self):  # noqa: C901
        """Register /map.html endpoint."""

        @self.router.get(
            "/{tileMatrixSetId}/map.html",
            response_class=HTMLResponse,
            operation_id=f"{self.operation_prefix}getMapViewer",
        )
        def map_viewer(
            request: Request,
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(
                    description="Identifier selecting one of the TileMatrixSetId supported."
                ),
            ],
            tile_format: Annotated[
                ImageType | None,
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tilesize: Annotated[
                int,
                Query(gt=0, description="Tilesize in pixels. Default to 256."),
            ] = 256,
            minzoom: Annotated[
                int | None,
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                int | None,
                Query(description="Overwrite default maxzoom."),
            ] = None,
            dataset=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            render_params=Depends(self.render_dependency),
        ):
            """Return TileJSON document for a dataset."""
            tilejson_url = self.url_for(
                request, "tilejson", tileMatrixSetId=tileMatrixSetId
            )

            qs = list(request.query_params._list)
            if "tilesize" not in request.query_params:
                qs.append(("tilesize", tilesize))
            tilejson_url += f"?{urlencode(qs)}"

            point_url = self.url_for(request, "point", lon="{lon}", lat="{lat}")
            if request.query_params._list:
                qs_key_to_remove = [
                    "tilesize",
                    "tile_format",
                    "minzoom",
                    "maxzoom",
                    "buffer",
                    "padding",
                    "colormap",
                    "colormap_name",
                ]
                qs = [
                    (key, value)
                    for (key, value) in request.query_params._list
                    if key.lower() not in qs_key_to_remove
                ]
                point_url += f"?{urlencode(qs)}"

            tms = self.supported_tms.get(tileMatrixSetId)
            return self.templates.TemplateResponse(
                request,
                name="map.html",
                context={
                    "tilejson_endpoint": tilejson_url,
                    "point_endpoint": point_url,
                    "tms": tms,
                    "resolutions": [matrix.cellSize for matrix in tms],
                },
                media_type="text/html",
            )


app = FastAPI(
    openapi_url="/api",
    docs_url="/api.html",
)

md = TilerFactory()
app.include_router(md.router)


# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_middleware(
    CompressionMiddleware,
    minimum_size=0,
    exclude_mediatype={
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/jp2",
        "image/webp",
    },
    compression_level=6,
)

