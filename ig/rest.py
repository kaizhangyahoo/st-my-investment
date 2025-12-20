import requests
import json
import logging
from typing import Dict, Any, Optional

from .models import IGConfig, UserSession, Position

logger = logging.getLogger(__name__)

class IGRestClient:
    # BASE_URL_DEMO = "https://demo-api.ig.com/gateway/deal"
    BASE_URL_LIVE = "https://api.ig.com/gateway/deal"
    

    def __init__(self, config: IGConfig):
        self.config = config
        self.base_url = self.BASE_URL_LIVE
        self.session: Optional[UserSession] = None
        self._http = requests.Session()
        self._http.headers.update({
            "Content-Type": "application/json, charset=UTF-8",
            "Accept": "application/json; charset=UTF-8",
            "X-IG-API-KEY": config.api_key
        })

    def login(self) -> UserSession:
        url = f"{self.base_url}/session"
        payload = {
            "identifier": self.config.username,
            "password": self.config.password
        }
        # Version 2 or 3 is typically recommended
        self._http.headers.update({
            "Version": "3"
        })
        # headers = {"Version": "3"} 
        response = self._http.post(url, json=payload, headers=self._http.headers)
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code} {response.text}")
        data = response.json()
        
        # Extract headers (Legacy/V2)
        cst = response.headers.get("CST")
        x_security_token = response.headers.get("X-SECURITY-TOKEN")
        
        # Extract OAuth (V3)
        oauth_token = data.get("oauthToken")

        if not (cst and x_security_token) and not oauth_token:
             raise Exception("Authentication tokens (CST/XST or OAuth) missing from response")

        self.session = UserSession(
            client_id=data.get("clientId"),
            account_id=data.get("accountId"),
            # account_id="QX2B3",
            lightstreamer_endpoint=data.get("lightstreamerEndpoint"),
            cst_token=cst,
            x_security_token=x_security_token,
            active_account_id=data.get("currentAccountId") or data.get("accountId"), # Fallback if currentAccountId missing
            oauth_token=oauth_token
        )
        
        # Update session headers for future requests
        if self.session.oauth_token:
            access_token = self.session.oauth_token.get("access_token")
            self._http.headers.update({
                "Authorization": f"Bearer {access_token}",
                "IG-ACCOUNT-ID": self.session.account_id
            })
        
        if self.session.cst_token:
            self._http.headers.update({"CST": self.session.cst_token})
        if self.session.x_security_token:
            self._http.headers.update({"X-SECURITY-TOKEN": self.session.x_security_token})
        
        logger.info(f"Logged in as {self.config.username}, Account: {self.session.account_id}")
        return self.session

    def logout(self):
        if not self.session:
            return
        url = f"{self.base_url}/session"
        self._http.delete(url)
        self.session = None
        logger.info("Logged out")

    def get_positions(self) -> list[Position]:
        url = f"{self.base_url}/positions"
        response = self._http.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to get positions: {response.text}")
            return []
            
        data = response.json()
        positions = []
        for p in data.get("positions", []):
            market = p.get("market", {})
            pos_data = p.get("position", {})
            positions.append(Position(
                deal_id=pos_data.get("dealId"),
                epic=market.get("epic"),
                size=pos_data.get("size"),
                level=pos_data.get("level"),
                direction=pos_data.get("direction"),
                currency=pos_data.get("currency")
            ))
        return positions

    def get_completed_trades(self, trade_id: str):
        # Example to fetch confirmation
        url = f"{self.base_url}/confirms/{trade_id}"
        return self._http.get(url).json()
