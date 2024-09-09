import asyncio
import logging
from ipaddress import ip_network
from typing import List

from zoneit.clientinfo_provider import MktClientInfo, TsClientInfo, ZtClientInfo
from zoneit.models import ClientInfo

from .config import Settingsv2, settings_dependency
from .zone_utils import SOA, RecordType, RTypeEnum, ZoneFile

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


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

    settings = Settingsv2()  # pyright: ignore

    providers = [
        ZtClientInfo(settings.zt),
        TsClientInfo(settings.ts),
        MktClientInfo(settings.mkt),
    ]

    while True:
        data = {}
        for p in providers:
            try:
                result = await p.get()
                data = {**data, **result}

                for k, v in result.items():
                    logging.info(f"{type(p).__name__} load {k} with {len(v)} entries")
            except Exception as ex:
                # logging.error(f"failed to load {type(p).__name__}")  # , exc_info=ex)
                logging.error(
                    f"failed to load: {type(p).__name__}, {ex.__module__} : {ex}"
                )

        for zone, clients in data.items():
            await process_leases(zone, clients)

        for k, v in conf.reverse_ptr.items():
            conf.zones[k] = gen_zone_reverse(k, v)

        await asyncio.sleep(300)
