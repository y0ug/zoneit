from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SOA(BaseModel):
    mname: str = Field()  # primary nameserver
    rname: str = Field()  # admin email with dot instead of @
    serial: int = Field(default=int(datetime.utcnow().timestamp()))
    refresh: int = Field(default=60 * 60)
    retry: int = Field(default=10 * 60)
    expire: int = Field(default=24 * 60 * 60)
    min_ttl: int = Field(default=300)


class RTypeEnum(str, Enum):
    A = "A"
    PTR = "PTR"


class RecordType(BaseModel):
    name: str = Field()
    rtype: RTypeEnum = Field(default=RTypeEnum.A)
    value: str = Field()
    ttl: int = Field(default=3600)


class ZoneFile:
    records = [RecordType]

    def __init__(self, name: str, soa: SOA, ttl: int = 3600):
        self.name = name
        self.ttl = ttl
        self.soa = soa
        self.records = []

    def add_record(self, record: RecordType):
        self.records.append(record)

    def generate(self):
        last_ttl = self.ttl
        zone_str = f"""$ORIGIN {self.name}.
$TTL {self.ttl}
{self.name}. IN SOA  {self.soa.mname}. {self.soa.rname}. (
    {self.soa.serial} ; serial
    {self.soa.refresh}; refresh
    {self.soa.retry}; retry
    {self.soa.expire} ; expire
    {self.soa.min_ttl}; minimum 
    )
$ORIGIN {self.name}.
"""
        # NS  {self.soa[0]}

        for record in self.records:
            # if record.rtype == RTypeEnum.A:
            if last_ttl != record.ttl:
                zone_str += f"$TTL {record.ttl}\n"
                last_ttl = record.ttl
            zone_str += f"{record.name} {record.rtype.value} {record.value}\n"
        return zone_str
