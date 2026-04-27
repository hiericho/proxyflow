from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ProxyBase(BaseModel):
    url: str
    protocol: Optional[str] = None
    latency: Optional[float] = None
    status: str = "unknown" # active, dead, unknown
    last_check: Optional[datetime] = None

class ProxyCreate(ProxyBase):
    pass

class ProxyInDB(ProxyBase):
    id: int

    class Config:
        from_attributes = True

class HealthCheckTarget(BaseModel):
    name: str = "google"
    url: str = "https://www.google.com"
    expected_status: int = 200
    timeout: int = 10

class DashboardStats(BaseModel):
    total: int
    active: int
    dead: int
    unknown: int
    avg_latency: float
    last_cycle_at: Optional[datetime]
    fastest_proxies: List[Dict]
