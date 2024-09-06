import httpx
import requests


# def get_zerotier_clients(api_token: str, network_id: str):
#     if not api_token or not network_id:
#         print("Error: Missing required environment variables ZT_TOKEN and ZT_NETWORK")
#         return None
#
#     headers = {"Authorization": f"Bearer {api_token}"}
#     url = f"https://api.zerotier.com/api/v1/network/{network_id}/member"
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()
#
#     data = response.json()
#
async def get_zerotier_clients(api_token: str, network_id: str):
    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"https://api.zerotier.com/api/v1/network/{network_id}/member"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    return data


async def get_ztnet_clients(api_token: str, network_id: str):
    headers = {"x-ztnet-auth": f"{api_token}"}
    url = f"https://ztnet.mazenet.org/api/v1/network/{network_id}/member/"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    return data


async def zt_dhcp_lease_original(zt_token, zt_network):
    # Format the output as per your requirements
    data = await get_ztnet_clients(zt_token, zt_network)
    clients = []
    for device in data:
        ips = device["config"]["ipAssignments"]
        ip = ips[0] if len(ips) else None
        client = {
            "hostname": device.get("name", None),
            "ip_address": ip,
            "id": device["config"]["address"],
        }
        if client["hostname"]:
            clients.append(client)

    return clients


async def zt_dhcp_lease(zt_token, zt_network):
    # Format the output as per your requirements
    data = await get_ztnet_clients(zt_token, zt_network)
    clients = []
    for device in data:
        ips = device["ipAssignments"]
        ip = ips[0] if len(ips) else None
        client = {
            "hostname": device.get("name", None),
            "ip_address": ip,
            "id": device["address"],
        }
        if client["hostname"]:
            clients.append(client)

    return clients
