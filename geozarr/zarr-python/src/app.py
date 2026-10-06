"""titiler.eopf Application."""

from typing import Annotated, Literal
from collections.abc import Callable
from attrs import define
from fastapi import Depends, FastAPI, Query, Path
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware
from titiler.core.dependencies import DefaultDependency, ImageRenderingParams
from titiler.core.factory import BaseFactory
from titiler.core.resources.enums import ImageType
from titiler.core.utils import render_image
from rio_tiler.experimental.zarr import GroupReader
import zarr
from starlette.responses import Response
from pydantic import Field
from morecantile import tms as morecantile_tms
from morecantile.defaults import TileMatrixSets

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

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoint."""

        available_tms = tuple(self.supported_tms.list())

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
        async def tile(
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

