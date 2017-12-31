from typing import Dict

def error_response(msg: str) -> Dict[str, str]:
    return {"error": msg}
