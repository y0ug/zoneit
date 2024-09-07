import asyncio
import logging
import os
from contextlib import asynccontextmanager
from ipaddress import IPv4Address, IPv4Network, ip_address, ip_network

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from .mk_lease import mktxp_dhcp_lease
from .ts_lease import ts_dhcp_lease
from .zone_utils import SOA, RecordType, RTypeEnum, ZoneFile
from .zt_lease import zt_dhcp_lease

from redis.asyncio import Redis
from .memdb import redis_dependency
from .config import settings_dependency

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

zones = {}
clients = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_dependency.init()
    await settings_dependency.init()
    asyncio.create_task(zone_update())
    yield
    zones.clear()
    clients.clear()


app = FastAPI(lifespan=lifespan)

ranges = {k: ip_network(v) for k, v in ranges.items()}
reverse_ptr = {k: [] for k, _ in ranges.items()}


def reverse_ptr_update(c):
    for k, v in ranges.items():
        for x in c:
            if v.overlaps(ip_network(f'{x["ip_address"]}/24', strict=False)):
                reverse_ptr[k].append(x)
                return


def gen_zone(domain_name, clients):
    soa = SOA(mname="ns.mazenet.org", rname="admin.mazenet.org", refresh=300)
    zone = ZoneFile(domain_name, soa=soa, ttl=300)
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


def gen_zone_reverse(domain_name, clients):
    soa = SOA(mname="ns.mazenet.org", rname="admin.mazenet.org", refresh=300)
    zone = ZoneFile(domain_name, soa=soa, ttl=300)
    for record in clients:
        if not record.get("hostname", None):
            continue

        r = RecordType(
            rtype=RTypeEnum.PTR,
            name=record["ptr"],
            value=f'{record["fqdn"]}.',
            ttl=300,
        )
        zone.add_record(r)
    return zone.generate()


def process_leases(name, c):
    c = [
        {
            **x,
            "fqdn": f"{x['hostname']}.{name}",
            "ptr": f'{'.'.join(x["ip_address"].split('.')[::-1][:3])}',
        }
        for x in c
        if x.get("hostname")
    ]
    clients[name] = c
    zones[name] = gen_zone(name, c)
    reverse_ptr_update(c)
    return c


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
        process_leases(name, c)

        c = await zt_dhcp_lease(zt_token, zt_network)
        name = "zt.mazenet.org"
        process_leases(name, c)

        c = await mktxp_dhcp_lease(prom_url, mkt_node)
        for k, v in c.items():
            name = f"{k}.mazenet.org"
            process_leases(name, v)

        for k, v in reverse_ptr.items():
            zones[k] = gen_zone_reverse(k, v)

        await asyncio.sleep(300)


@app.get("/zone/dump")
async def zone_dump(redis: Redis = Depends(redis_dependency)):
    return clients


@app.get("/zones")
async def zones_dump():
    return [k for k in zones.keys()]


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
