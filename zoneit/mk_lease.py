import httpx


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


# def query_victoria_metrics(server_url, node):
#     query = f'mktxp_dhcp_lease_info{{routerboard_name="{node}"}}'
#     headers = {"Content-Type": "text/plain"}
#     response = requests.get(server_url, params={"query": query}, headers=headers)
#     response.raise_for_status()
#     data = response.json()
#     return data


def mktxp_dhcp_lease_parser(data):
    out = {}
    for point in data["data"]["result"]:
        e = {
            "server": point["metric"]["server"],
            "ip_address": point["metric"]["active_address"],
            "mac_address": point["metric"]["active_mac_address"],
            "hostname": point["metric"].get("host_name", None),
        }
        out.setdefault(e["server"], []).append(e)

    return out


async def mktxp_dhcp_lease(server_url, node):
    data = await query_victoria_metrics(server_url, node)
    return mktxp_dhcp_lease_parser(data)

    # for k, v in formatted_data.items():
    # name = f"{k}.mazenet.org"
    # zone = get_zone(name, v)
    # with open(f"zones/{name}.zone", "w") as fp:
    #     fp.write(zone)
