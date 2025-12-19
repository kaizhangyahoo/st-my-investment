import base64
import logging

logger = logging.getLogger(__name__)

def encrypt_password(password: str, encryption_key: str, time_stamp: str) -> str:
    """
    Simulates encryption if required. 
    Note: Real IG implementations often use RSA encryption for passwords 
    if not using the simpler V2 authentication. 
    For V2/V3 simple session creation, plain password in body is often supported over HTTPS 
    or specific encryption headers. 
    
    This placeholder ensures we have a spot for it if needed.
    """
    # Placeholder: In a real scenario, this would use RSADomestic or similar libraries 
    # to encrypt the password with the provided public key.
    # For now, we assume standard HTTPS transport security is sufficient for the simplified sample 
    # unless we hit specific API constraints.
    return password

def format_price(price: float) -> str:
    return f"{price:.2f}"
