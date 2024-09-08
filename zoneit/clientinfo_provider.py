from abc import ABC, abstractmethod
from typing import Dict, List

from zoneit.utils import query_api_json, query_victoria_metrics

from .config import SettingsMkt, SettingsTs, SettingsZt
from .models import ClientInfo, ClientInfoMkt, ClientInfoTs, ClientInfoZt


class ClientInfoProvider(ABC):
    @abstractmethod
    async def get(self) -> Dict[str, List[ClientInfo]]:
        """get current clients of the ClientInfoProvider"""


class TsClientInfo(ClientInfoProvider):
    def __init__(self, conf: SettingsTs) -> None:
        self.conf = conf

    async def get(self) -> Dict[str, List[ClientInfo]]:
        headers = {"Authorization": f"Bearer {self.conf.token}"}
        url = f"{self.conf.api_url}/api/v2/tailnet/{self.conf.network}/devices"
        data = await query_api_json(url, headers)

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
                        "domain": self.conf.domain,
                        "tshostname": device["name"],
                    }
                )
            )

        return {self.conf.domain: clients}


class ZtClientInfo(ClientInfoProvider):
    def __init__(self, conf: SettingsZt) -> None:
        self.conf = conf

    async def get(self) -> Dict[str, List[ClientInfo]]:
        headers = {"x-ztnet-auth": f"{self.conf.token}"}
        url = f"{self.conf.api_url}/api/v1/network/{self.conf.network}/member/"
        data = await query_api_json(url, headers)
        clients = []
        for device in data:
            ips = device["ipAssignments"]
            ip = ips[0] if len(ips) else None
            clients.append(
                ClientInfoZt.model_validate(
                    {
                        "hostname": device.get("name", None),
                        "ip_address": ip,
                        "id": device["address"],
                        "domain": self.conf.domain,
                    }
                )
            )

        return {self.conf.domain: clients}


class MktClientInfo(ClientInfoProvider):
    def __init__(self, conf: SettingsMkt) -> None:
        self.conf = conf

    async def get(self) -> Dict[str, List[ClientInfo]]:
        query = f'mktxp_dhcp_lease_info{{routerboard_name="{self.conf.node}"}}'
        data = await query_victoria_metrics(self.conf.prom_url, query)
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
                    "domain": f'{point["server"]}.{self.conf.domain}',
                }
            )
            out.setdefault(e.domain, []).append(e)
        return out
