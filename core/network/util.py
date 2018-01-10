import os
import requests
from typing import Dict, Optional

def error_response(msg: str) -> Dict[str, str]:
    return {"error": msg}

def generic_ok_response(msg: Optional[str] = None) -> Dict[str, str]:
    resp_msg = "thanks buddy"
    if msg:
        resp_msg += ", " + msg
    return {"msg": resp_msg}

def resolve_external_address() -> str:
    r = requests.get("http://ipv4.larsendt.com")
    return r.text
