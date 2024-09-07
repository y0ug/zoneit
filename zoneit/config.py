import os
from typing import Set, Any, Optional

class Settings:
    ranges = {
        "10.in-addr.arpa": "10.0.0.0/8",
        "168.192.in-addr.arpa": "192.168.0.0/16"
    }
    reverse_ptr: dict
    def __init__(self) -> None:
        self.ranges = {k: ip_network(v) for k, v in self.ranges.items()}
        self.reverse_ptr = {k: [] for k, _ in self..ranges.items()}

class SettingsDependency:
    ctx: Optional[Settings] = None

    async def __call__(self):
        if self.ctx is None:
            await self.init()
        return self.ctx

    async def init(self):
        self.ctx = Settings()


settings_dependency: SettingsDependency = SettingsDependency()
