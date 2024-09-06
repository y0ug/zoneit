import logging
import asyncio
import os

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from .mk_lease import mktxp_dhcp_lease
from .zt_lease import zt_dhcp_lease
from .ts_lease import ts_dhcp_lease
from .zone_utils import ZoneFile, SOA, RecordType, RTypeEnum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

zones = {}
clients = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(zone_update())
    yield
    zones.clear()
    clients.clear()


app = FastAPI(lifespan=lifespan)


def gen_zone(domain_name, clients):
    soa = SOA(mname="ns.mazenet.org", rname="admin.mazenet.org", refresh=300)
    zone = ZoneFile(domain_name, soa=soa)
    for record in clients:
        if not record.get("hostname", None):
            continue
        r = RecordType(
            rtype=RTypeEnum.A,
            name=record["hostname"],
            value=record["ip_address"],
            ttl=300,
        )
        zone.add_record(r)
    return zone.generate()


async def zone_update():
    global clients
    prom_url = os.getenv("PROM_URL")
    mkt_node = os.getenv("MKT_NODE")

    zt_token = os.getenv("ZT_TOKEN")
    zt_network = os.getenv("ZT_NETWORK")

    ts_token = os.getenv("TS_TOKEN")
    ts_network = os.getenv("TS_NETWORK")

    while True:
        clients = {}

        c = await ts_dhcp_lease(ts_token, ts_network)
        name = "ts.mazenet.org"
        clients[name] = c
        zones[name] = gen_zone(name, c)

        c = await zt_dhcp_lease(zt_token, zt_network)
        name = "zt.mazenet.org"
        clients[name] = c
        zones[name] = gen_zone(name, c)

        c = await mktxp_dhcp_lease(prom_url, mkt_node)
        for k, v in c.items():
            name = f"{k}.mazenet.org"
            clients[name] = v
            zones[name] = gen_zone(name, v)

        await asyncio.sleep(300)


@app.get("/zone/dump")
async def zone_dump():
    return clients


@app.get(
    "/zone/{name}.zone",
    response_class=PlainTextResponse,
)
async def zone(name: str):
    if name not in zones:
        raise HTTPException(status_code=404, detail="Item not found")
    return zones[name]


# def write_zone(name, clients):
#     logger.info(f"building {name}")
#     zone = get_zone(name, clients)
#     logger.info(zone)
#     with open(f"zones/{name}.zone", "w") as fp:
#         fp.write(zone)


# if __name__ == "__main__":
# main()
