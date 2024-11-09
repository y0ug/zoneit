import asyncio
import logging
from contextlib import asynccontextmanager
from importlib import metadata

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Ctx, Settings, ctx_dependency
from .tasks import zone_update

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s; %(name)s; %(levelname)s; %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger(__name__)

auth_scheme = HTTPBearer()
settings = Settings()  # pyright: ignore

# TODO package need to be installed for this to work correctly
package_name = __package__ or "zoneit"
__version__ = metadata.version(package_name)

logger.info(f"starting {package_name} v{__version__}")
logger.info(f"auth bearer: {settings.bearer_token}")


def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    if credentials.credentials != settings.bearer_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unautorized",
        )
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ctx_dependency.init()
    asyncio.create_task(zone_update())
    yield
    # cleanup resource


app = FastAPI(
    lifespan=lifespan,
    dependencies=[Depends(verify_bearer_token)],
)


@app.get("/zone/dump")
async def get_zone_dump(
    ctx: Ctx = Depends(ctx_dependency),
):
    return ctx.clients


@app.get("/zones")
async def get_zones(
    ctx: Ctx = Depends(ctx_dependency),
):
    return [k for k in ctx.zones.keys()]


@app.get(
    "/zone/{name}.zone",
    response_class=PlainTextResponse,
)
async def get_zone(
    name: str,
    ctx: Ctx = Depends(ctx_dependency),
):
    if name not in ctx.zones:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return ctx.zones[name]


# if __name__ == "__main__":
# main()
