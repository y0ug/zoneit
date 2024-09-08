import asyncio
import logging
from contextlib import asynccontextmanager

# from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from redis.asyncio import Redis

from .config import Settings, settings_dependency
from .memdb import redis_dependency
from .tasks import zone_update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_dependency.init()
    await settings_dependency.init()
    asyncio.create_task(zone_update())
    yield
    # cleanup resource


app = FastAPI(lifespan=lifespan)


@app.get("/zone/dump")
async def get_zone_dump(
    redis: Redis = Depends(redis_dependency),
    conf: Settings = Depends(settings_dependency),
):
    return conf.clients


@app.get("/zones")
async def get_zones(
    redis: Redis = Depends(redis_dependency),
    conf: Settings = Depends(settings_dependency),
):
    return [k for k in conf.zones.keys()]


@app.get(
    "/zone/{name}.zone",
    response_class=PlainTextResponse,
)
async def get_zone(
    name: str,
    redis: Redis = Depends(redis_dependency),
    conf: Settings = Depends(settings_dependency),
):
    if name not in conf.zones:
        raise HTTPException(status_code=404, detail="Item not found")
    return conf.zones[name]


# if __name__ == "__main__":
# main()
