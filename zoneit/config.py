import os
from typing import List, Set, Any, Optional
from ipaddress import ip_network


class Settings:
    ranges = {
        "10.in-addr.arpa": ip_network("10.0.0.0/8"),
        "168.192.in-addr.arpa": ip_network("192.168.0.0/16"),
    }
    reverse_ptr: dict
    zones: dict
    clients: dict

    def __init__(self) -> None:
        self.reverse_ptr = {k: [] for k, _ in self.ranges.items()}
        self.zones = {}
        self.clients = {}


class SettingsDependency:
    ctx: Optional[Settings] = None

    async def __call__(self) -> Settings:
        if self.ctx is None:
            await self.init()
        if self.ctx:
            return self.ctx
        else:
            raise Exception("failed to init settings")

    async def init(self):
        self.ctx = Settings()


settings_dependency: SettingsDependency = SettingsDependency()
