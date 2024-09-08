import httpx

from zoneit.models import ClientInfo, ClientInfoMkt


async def query_victoria_metrics(server_url, node):
    query = f'mktxp_dhcp_lease_info{{routerboard_name="{node}"}}'
    headers = {"Content-Type": "text/plain"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            server_url, params={"query": query}, headers=headers
        )
        response.raise_for_status()
        data = response.json()

    return data


def mktxp_dhcp_lease_parser(data, sufix_domain) -> dict[str, ClientInfoMkt]:
    out = {}
    for point in data["data"]["result"]:
        point = point["metric"]
        hostname = point.get("host_name") or point["active_mac_address"].replace(
            ":", ""
        )
        if not hostname:
            hostname = point["active_mac_address"].replace(":", "")
        e = ClientInfoMkt.model_validate(
            {
                "server": point["server"],
                "ip_address": point["active_address"],
                "mac_address": point["active_mac_address"],
                "hostname": hostname,
                "domain": f'{point["server"]}.{sufix_domain}',
            }
        )
        out.setdefault(e.server, []).append(e)

    return out


async def mktxp_dhcp_lease(server_url, node, sufix_domain) -> dict[str, ClientInfoMkt]:
    data = await query_victoria_metrics(server_url, node)
    return mktxp_dhcp_lease_parser(data, sufix_domain)
