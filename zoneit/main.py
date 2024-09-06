from .zone_utils import ZoneFile, SOA, RecordType, RTypeEnum
from dotenv import load_dotenv
from .mk_lease import mktxp_dhcp_lease
from .zt_lease import zt_dhcp_lease
import logging
import asyncio
import os
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)
load_dotenv()


from fastapi import BackgroundTasks, FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)

app = FastAPI()

zones = {}


def gen_zone(domain_name, clients):
    soa = SOA(
        mname="ns.mazenet.org",
        rname="admin.mazenet.org",
    )
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
    prom_url = os.getenv("PROM_URL")
    mkt_node = os.getenv("MKT_NODE")

    zt_token = os.getenv("ZT_TOKEN")
    zt_network = os.getenv("ZT_NETWORK")

    while True:
        zt_clients = await zt_dhcp_lease(zt_token, zt_network)
        zones["zt.mazenet.org"] = gen_zone("zt.mazenet.org", zt_clients)
        mkt_clients = await mktxp_dhcp_lease(prom_url, mkt_node)
        for k, v in mkt_clients.items():
            name = f"{k}.mazenet.org"
            zones[name] = gen_zone(name, v)
        await asyncio.sleep(300)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(zone_update())


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
