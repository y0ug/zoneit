from typing import List
import httpx

from zoneit.models import ClientInfoTs


# def get_zerotier_clients(api_token: str, network_id: str):
#     if not api_token or not network_id:
#         print("Error: Missing requiredtskey-api-k3YqzuRVtB21CNTRL-viRBUaPF2UQ416of1qaaYQm1ArHQ71iH environment variables ZT_TOKEN and ZT_NETWORK")
#         return None
#
#     headers = {"Authorization": f"Bearer {api_token}"}
#     url = f"https://api.zerotier.com/api/v1/network/{network_id}/member"
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()
#
#     data = response.json()
#
async def get_tailscale_clients(api_token: str, network_id: str):
    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"https://api.tailscale.com/api/v2/tailnet/{network_id}/devices"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    return data


async def ts_dhcp_lease(ts_token, ts_network, domain) -> List[ClientInfoTs]:
    data = await get_tailscale_clients(ts_token, ts_network)
    clients = []
    for device in data["devices"]:
        ips = device["addresses"]
        ip = ips[0] if len(ips) else None
        clients.append(
            ClientInfoTs.model_validate(
                {
                    "hostname": device["name"].split(".")[0],
                    "ip_address": ip,
                    "id": device["nodeId"],
                    "domain": domain,
                    "tshostname": device["name"],
                }
            )
        )

    return clients
