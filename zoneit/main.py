import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from .config import Ctx, ctx_dependency
from .tasks import zone_update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ctx_dependency.init()
    asyncio.create_task(zone_update())
    yield
    # cleanup resource


app = FastAPI(lifespan=lifespan)


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
        raise HTTPException(status_code=404, detail="Item not found")
    return ctx.zones[name]


# if __name__ == "__main__":
# main()
