from typing import Optional

from pydantic import BaseModel, ValidationInfo, computed_field, field_validator


class ClientInfo(BaseModel):
    hostname: str
    ip_address: str
    domain: str
    # ptr: Optional[str]
    # fqdn: Optional[str]

    @computed_field
    @property
    def ptr(self) -> str:
        return ".".join(self.ip_address.split(".")[::-1]) + ".in-addr.arpa"

    @computed_field
    @property
    def fqdn(self) -> str:
        return f"{self.hostname}.{self.domain}"


class ClientInfoTs(ClientInfo):
    tshostname: str
    id: str


class ClientInfoZt(ClientInfo):
    id: str


class ClientInfoMkt(ClientInfo):
    mac_address: str
    server: str
