"""titiler.eopf Application."""

from typing import Annotated, Literal

from collections.abc import Callable
import jinja2
from fastapi import FastAPI, Query
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette_cramjam.middleware import CompressionMiddleware
from starlette.templating import Jinja2Templates

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import CacheControlMiddleware
from titiler.core.models.OGC import Conformance, Landing
from titiler.core.resources.enums import MediaType
from titiler.core.utils import accept_media_type, create_html_response, update_openapi
from titiler.core.dependencies import DatasetPathParams

from titiler.eopf.reader import GeoZarrReader

from titiler.eopf.factory import TilerFactory
from titiler.eopf.settings import ApiSettings

import attr
from functools import lru_cache
import obstore
import xarray
from zarr.storage import ObjectStore
from rio_tiler.constants import WEB_MERCATOR_TMS
from morecantile import TileMatrixSet

settings = ApiSettings(_env_prefix="TITILER_API_")


@lru_cache(maxsize=10)
def open_dataset(src_path: str) -> xarray.DataTree:
    store = obstore.store.from_url(src_path)
    zarr_store = ObjectStore(store=store, read_only=True)
    return xarray.open_datatree(
        zarr_store,
        decode_times=True,
        decode_coords="all",
        create_default_indexes=False,
        # By default xarray will try to load the consolidated metadata
        # consolidated=True,
        # See https://github.com/pydata/xarray/issues/11361
        # use_zarr_fill_value_as_mask=True,
        zarr_format=3,
        engine="zarr",
    )



@attr.s
class CustomReader(GeoZarrReader):
    """Zarr dataset Reader.

    Attributes:
        input (str): dataset path.
        datatree (xarray.DataTree): Xarray datatree.
        tms (morecantile.TileMatrixSet): TileMatrixSet grid definition. Defaults to `WebMercatorQuad`.
        opener (Callable): Xarray datatree opener. Defaults to `open_dataset`.
        opener_options (dict): Options to forward to the opener callable.

    Examples:
        >>> with GeoZarrReader("geo-zarr-v1",) as src:
                print(src)

    """

    input: str = attr.ib()
    datatree: xarray.DataTree = attr.ib(default=None)

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    minzoom: int = attr.ib(default=None)
    maxzoom: int = attr.ib(default=None)

    opener: Callable[..., xarray.DataTree] = attr.ib(default=open_dataset)
    opener_options: dict = attr.ib(factory=dict)

    groups: list[str] = attr.ib(init=False)
    variables: list[str] = attr.ib(init=False)


# HTML templates
templates = Jinja2Templates(
    env=jinja2.Environment(
        autoescape=jinja2.select_autoescape(["html", "xml"]),
        loader=jinja2.ChoiceLoader(
            [
                jinja2.PackageLoader("titiler.eopf", "templates"),
                jinja2.PackageLoader("titiler.core", "templates"),
            ]
        ),
    ),
)


app = FastAPI(
    title=settings.name,
    openapi_url="/api",
    docs_url="/api.html",
)

update_openapi(app)

TITILER_CONFORMS_TO = {
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
}


md = TilerFactory(
    path_dependency=DatasetPathParams,
    reader=CustomReader,
    router_prefix="/geozarr",
    templates=templates,
)
app.include_router(md.router, prefix="/geozarr")

TITILER_CONFORMS_TO.update(md.conforms_to)

add_exception_handlers(app, DEFAULT_STATUS_CODES)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods,
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

app.add_middleware(
    CacheControlMiddleware,
    cachecontrol=settings.cachecontrol,
    exclude_path={r"/_mgmt*"},
)


@app.get(
    "/",
    response_model=Landing,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "text/html": {},
                "application/json": {},
            }
        },
    },
    tags=["OGC Common"],
)
def landing(
    request: Request,
    f: Annotated[
        Literal["html", "json"] | None,
        Query(
            description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
        ),
    ] = None,
):
    """Landing page."""
    data = {
        "title": settings.name,
        "links": [
            {
                "title": "Landing page",
                "href": str(request.url_for("landing")),
                "type": "text/html",
                "rel": "self",
            },
            {
                "title": "The API definition (JSON)",
                "href": str(request.url_for("openapi")),
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "rel": "service-desc",
            },
            {
                "title": "The API documentation",
                "href": str(request.url_for("swagger_ui_html")),
                "type": "text/html",
                "rel": "service-doc",
            },
            {
                "title": "Conformance Declaration",
                "href": str(request.url_for("conformance")),
                "type": "text/html",
                "rel": "http://www.opengis.net/def/rel/ogc/1.0/conformance",
            },
        ],
    }

    if f:
        output_type = MediaType[f]
    else:
        accepted_media = [MediaType.html, MediaType.json]
        output_type = (
            accept_media_type(request.headers.get("accept", ""), accepted_media)
            or MediaType.json
        )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data,
            title="TiTiler-EOPF",
            template_name="landing",
            templates=templates,
        )

    return data


@app.get(
    "/conformance",
    response_model=Conformance,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "text/html": {},
                "application/json": {},
            }
        },
    },
    tags=["OGC Common"],
)
def conformance(
    request: Request,
    f: Annotated[
        Literal["html", "json"] | None,
        Query(
            description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
        ),
    ] = None,
):
    """Conformance classes.

    Called with `GET /conformance`.

    Returns:
        Conformance classes which the server conforms to.

    """
    data = {"conformsTo": sorted(TITILER_CONFORMS_TO)}

    if f:
        output_type = MediaType[f]
    else:
        accepted_media = [MediaType.html, MediaType.json]
        output_type = (
            accept_media_type(request.headers.get("accept", ""), accepted_media)
            or MediaType.json
        )

    if output_type == MediaType.html:
        return create_html_response(
            request,
            data,
            title="Conformance",
            template_name="conformance",
            templates=templates,
        )

    return data
