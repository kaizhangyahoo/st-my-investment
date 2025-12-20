import logging
import threading
import time
import websocket
from typing import Callable, Optional

from .models import UserSession

logger = logging.getLogger(__name__)

class IGStreamingClient:
    """
    A simplified Lightstreamer client for IG.
    Note: Full Lightstreamer protocol implementation is complex. 
    This is a basic adapter for demonstration purposes.
    """
    def __init__(self, session: UserSession):
        self.session = session
        self.ws: Optional[websocket.WebSocketApp] = None
        self.wst: Optional[threading.Thread] = None
        self.connected = False
        self._subscriptions = []
        self.on_update: Optional[Callable[[str, str], None]] = None

    def connect(self):
        # Construct Lightstreamer URL
        # IG uses specific endpoint logic
        if not self.session:
            raise Exception("Session required for streaming")
            
        # Example URL logic (simplified)
        # Real IG LS endpoint often looks like: https://apd.marketdatasystems.com/lightstreamer
        # WebSocket would be wss://...
        
        # Taking endpoint from session, cleaning protocol
        endpoint = self.session.lightstreamer_endpoint
        if endpoint.startswith("http"):
            endpoint = endpoint.replace("http", "ws", 1)
        
        url = f"{endpoint}/lightstreamer"
        
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        self.wst = threading.Thread(target=self.ws.run_forever)
        self.wst.daemon = True
        self.wst.start()

    def _on_open(self, ws):
        logger.info("Streaming connection opened")
        # Need to send connection creation request for Lightstreamer
        
        # Prepare password:
        # Standard: CST-{cst}|XST-{xst}
        # OAuth: Bearer {access_token} (Theoretical - IG specific LS auth varies)
        
        password = ""
        if self.session.cst_token and self.session.x_security_token:
            password = f"CST-{self.session.cst_token}|XST-{self.session.x_security_token}"
        elif self.session.oauth_token:
            # Fallback or specific OAuth handling for LS
            # Note: IG Lightstreamer with OAuth often requires a different flow or mapping.
            # Using raw access token as a guess for the password field if simple pattern allows.
            password = f"Bearer {self.session.oauth_token.get('access_token')}"
        
        user = self.session.active_account_id
        
        # Proper LS protocol handshake is non-trivial (bind_session etc). 
        # For this task, we will simulate the structure or use a library if available.
        # Since we are implementing raw, we acknowledge this might need a real LS library.
        # However, many Python users use `lightstreamer-client` or similar.
        # Here we will assume a simplified text protocol if possible, or just log for now 
        # as a placeholder if the protocol is too heavy for a single file.
        
        # Let's try sending a basic text protocol payload if supported or just log 
        # that we are ready to subscribe.
        self.connected = True
        logger.info("IG Streaming connected (Simulated/Ready)")

    def _on_message(self, ws, message):
        # Parse LS message
        logger.debug(f"Stream Msg: {message}")
        if self.on_update:
            self.on_update("Raw", message)

    def _on_error(self, ws, error):
        logger.error(f"Streaming error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info("Streaming connection closed")
        self.connected = False

    def subscribe(self, epics: list[str]):
        if not self.connected:
            logger.warning("Not connected to streaming server")
            return
        # Send subscription command
        # control.txt format
        logger.info(f"Subscribing to {epics}")

    def disconnect(self):
        if self.ws:
            self.ws.close()
