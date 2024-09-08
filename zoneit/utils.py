import httpx


async def query_victoria_metrics(server_url, query):
    headers = {"Content-Type": "text/plain"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            server_url, params={"query": query}, headers=headers
        )
        response.raise_for_status()
        data = response.json()

    return data


async def query_api_json(url: str, headers: dict):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    return data


async def get_tailscale_clients(api_url: str, api_token: str, network_id: str):
    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"{api_url}/api/v2/tailnet/{network_id}/devices"
    return await query_api_json(url, headers)


async def get_ztnet_clients(api_url, api_token: str, network_id: str):
    headers = {"x-ztnet-auth": f"{api_token}"}
    url = f"{api_url}/api/v1/network/{network_id}/member/"
    return await query_api_json(url, headers)
