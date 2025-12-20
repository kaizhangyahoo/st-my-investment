from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class IGConfig:
    username: str
    password: str
    api_key: str
    acc_type: str = "LIVE"  # DEMO or LIVE

@dataclass
class UserSession:
    client_id: str
    account_id: str
    lightstreamer_endpoint: str
    active_account_id: str
    cst_token: Optional[str] = None
    x_security_token: Optional[str] = None
    oauth_token: Optional[Dict[str, Any]] = None

@dataclass
class MarketData:
    epic: str
    bid: Optional[float] = None
    offer: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    market_status: str = "UNKNOWN"

@dataclass
class Position:
    deal_id: str
    epic: str
    size: float
    level: float
    direction: str  # BUY or SELL
    currency: str
