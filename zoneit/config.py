from ipaddress import ip_network
from typing import Dict, Optional, Tuple, Type
import uuid

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    RedisDsn,
    SecretStr,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class SettingsZt(BaseModel):
    token: str  # = Field(validation_alias="zt_token")
    network: str  # = Field(validation_alias="zt_network")
    api_url: AnyHttpUrl = Field(default="https://ztnet.mazenet.org")
    domain: str


class SettingsTs(BaseModel):
    token: str  # = Field(validation_alias="ts_token")
    network: str  # = Field(validation_alias="ts_network")
    api_url: AnyHttpUrl = Field(default="https://api.tailscale.com")
    domain: str


class SettingsMkt(BaseModel):
    prom_url: str  # AnyHttpUrl
    prom_token: Optional[str]
    node: str  # = Field(validation_alias="mkt_node")
    domain: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_nested_delimiter="__"
    )

    ts: SettingsTs
    zt: SettingsZt
    mkt: SettingsMkt
    bearer_token: str = Field(default=str(uuid.uuid4()))
    redis_url: RedisDsn = Field(
        "redis://localhost:6379/1",
    )
    redis_prefix: str = Field(default="zoneit")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, dotenv_settings, init_settings, file_secret_settings


class Ctx:
    ranges = {
        "10.in-addr.arpa": ip_network("10.0.0.0/8"),
        "168.192.in-addr.arpa": ip_network("192.168.0.0/16"),
    }
    reverse_ptr: dict
    zones: Dict[str, str]
    clients: dict

    def __init__(self) -> None:
        self.reverse_ptr = {k: [] for k, _ in self.ranges.items()}
        self.zones = {}
        self.clients = {}


class CtxDependency:
    ctx: Optional[Ctx] = None

    async def __call__(self) -> Ctx:
        if self.ctx is None:
            await self.init()
        if self.ctx:
            return self.ctx
        else:
            raise Exception("failed to init ctx")

    async def init(self):
        self.ctx = Ctx()


ctx_dependency: CtxDependency = CtxDependency()
