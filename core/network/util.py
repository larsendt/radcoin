from typing import Dict

def error_response(msg: str) -> Dict[str, str]:
    return {"error": msg}

def generic_ok_response() -> Dict[str, str]:
    return {"msg": "thanks buddy"}
