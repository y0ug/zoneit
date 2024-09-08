import os  # noqa: I001
import asyncio
from ipaddress import ip_network
from typing import List

from pydantic import (
    BaseModel,
    ValidationInfo,
    field_validator,
    model_validator,
    validator,
)

from zoneit.models import ClientInfo

from .config import settings_dependency
from .mk_lease import mktxp_dhcp_lease
from .ts_lease import ts_dhcp_lease
from .zone_utils import SOA, RecordType, RTypeEnum, ZoneFile
from .zt_lease import zt_dhcp_lease


async def reverse_ptr_update(c):
    conf = await settings_dependency()

    for k, v in conf.ranges.items():
        for x in c:
            if v.overlaps(ip_network(f"{x.ip_address}/24", strict=False)):
                conf.reverse_ptr[k].append(x)
                return


def gen_zone(domain_name, clients: List[ClientInfo]):
    soa = SOA(mname="ns.mazenet.org", rname="admin.mazenet.org", refresh=300)
    zone = ZoneFile(domain_name, soa=soa, ttl=300)
    for record in clients:
        r = RecordType(
            rtype=RTypeEnum.A,
            name=record.hostname,
            value=record.ip_address,
            ttl=300,
        )
        zone.add_record(r)
    return zone.generate()


def gen_zone_reverse(domain_name, clients):
    soa = SOA(mname="ns.mazenet.org", rname="admin.mazenet.org", refresh=300)
    zone = ZoneFile(domain_name, soa=soa, ttl=300)
    for record in clients:
        r = RecordType(
            rtype=RTypeEnum.PTR,
            name=record.ptr,
            value=f"{record.fqdn}.",
            ttl=300,
        )
        zone.add_record(r)
    return zone.generate()


async def process_leases(name, c):
    conf = await settings_dependency()
    conf.clients[name] = c
    conf.zones[name] = gen_zone(name, c)
    await reverse_ptr_update(c)
    return c


async def zone_update():
    conf = await settings_dependency()

    prom_url = os.getenv("PROM_URL")
    mkt_node = os.getenv("MKT_NODE")

    zt_token = os.getenv("ZT_TOKEN")
    zt_network = os.getenv("ZT_NETWORK")

    ts_token = os.getenv("TS_TOKEN")
    ts_network = os.getenv("TS_NETWORK")

    while True:
        name = "ts.mazenet.org"
        c = await ts_dhcp_lease(ts_token, ts_network, name)
        await process_leases(name, c)

        name = "zt.mazenet.org"
        c = await zt_dhcp_lease(zt_token, zt_network, name)
        await process_leases(name, c)

        name = "mazenet.org"
        c = await mktxp_dhcp_lease(prom_url, mkt_node, name)
        for k, v in c.items():
            name = f"{k}.mazenet.org"
            await process_leases(name, v)

        for k, v in conf.reverse_ptr.items():
            conf.zones[k] = gen_zone_reverse(k, v)

        await asyncio.sleep(300)
