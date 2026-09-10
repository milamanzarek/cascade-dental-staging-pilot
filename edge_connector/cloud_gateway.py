"""
Cloud WebSocket RPC Gateway for Lane 3 Clinic Edge Connectors.

Maintains persistent, authenticated outbound-initiated WebSocket tunnels from
clinic edge daemons, enabling cloud-native agents to query local practice databases
and lock schedule slots with zero open firewall ports.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Query
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger("edge_gateway")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class ClinicConnection:
    """Represents an active outbound-connected clinic edge daemon."""
    def __init__(self, clinic_id: str, websocket: WebSocket, metadata: Optional[Dict[str, Any]] = None):
        self.clinic_id = clinic_id
        self.websocket = websocket
        self.metadata = metadata or {}
        self.connected_at = time.time()
        self.last_heartbeat = time.time()
        self.latency_ms = 0.0
        self.pending_requests: Dict[str, asyncio.Future] = {}


class CloudGateway:
    """
    Central RPC Gateway connecting Cloud AI Agents to On-Premise Clinic Daemons.
    """
    def __init__(self, auth_token: str = "cascade_edge_secret_token_2026"):
        self.auth_token = auth_token
        self.active_clinics: Dict[str, ClinicConnection] = {}
        self.app = FastAPI(
            title="Lane 3 Zero-Port Edge Cloud Gateway",
            description="Secure Reverse-Tunnel RPC Gateway for On-Premise Practice Management Systems",
            version="1.0.0"
        )
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "active_clinics_count": len(self.active_clinics),
                "connected_clinics": list(self.active_clinics.keys())
            }

        @self.app.websocket("/ws/v1/edge/{clinic_id}")
        async def websocket_endpoint(websocket: WebSocket, clinic_id: str, token: Optional[str] = Query(None)):
            await websocket.accept()
            # Authentication verification
            if token != self.auth_token:
                logger.warning(f"[AUTH REJECTED] Clinic {clinic_id} provided invalid token.")
                await websocket.send_json({"type": "ERROR", "error": "Unauthorized: Invalid edge token"})
                await websocket.close(code=1008)
                return

            connection = ClinicConnection(clinic_id, websocket)
            self.active_clinics[clinic_id] = connection
            logger.info(f"[EDGE CONNECTED] Clinic {clinic_id} established outbound tunnel.")

            try:
                # Send welcome configuration
                await websocket.send_json({
                    "type": "CONFIG",
                    "heartbeat_interval_sec": 15,
                    "server_time": time.time()
                })

                while True:
                    data = await websocket.receive_text()
                    try:
                        msg = json.loads(data)
                        await self._handle_inbound_message(connection, msg)
                    except json.JSONDecodeError:
                        logger.error(f"Malformed JSON from clinic {clinic_id}: {data}")

            except WebSocketDisconnect:
                logger.info(f"[EDGE DISCONNECTED] Clinic {clinic_id} tunnel closed.")
            finally:
                if clinic_id in self.active_clinics:
                    del self.active_clinics[clinic_id]

        @self.app.get("/api/v1/edge/status/{clinic_id}")
        async def get_clinic_status(clinic_id: str):
            conn = self.active_clinics.get(clinic_id)
            if not conn:
                return JSONResponse(status_code=404, content={"status": "OFFLINE", "clinic_id": clinic_id})
            return {
                "status": "ONLINE",
                "clinic_id": clinic_id,
                "connected_duration_sec": round(time.time() - conn.connected_at, 2),
                "latency_ms": round(conn.latency_ms, 2),
                "last_heartbeat_sec_ago": round(time.time() - conn.last_heartbeat, 2),
                "metadata": conn.metadata
            }

        @self.app.post("/api/v1/edge/query/{clinic_id}")
        async def execute_query_api(clinic_id: str, payload: Dict[str, Any]):
            sql = payload.get("sql")
            params = payload.get("params", [])
            if not sql:
                raise HTTPException(status_code=400, detail="Missing 'sql' in payload")
            try:
                result = await self.execute_query(clinic_id, sql, params, timeout=payload.get("timeout", 5.0))
                return result
            except TimeoutError:
                raise HTTPException(status_code=504, detail="Edge daemon query timed out")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/edge/claim-slot/{clinic_id}")
        async def claim_slot_api(clinic_id: str, payload: Dict[str, Any]):
            apt_num = payload.get("apt_num")
            pat_num = payload.get("pat_num")
            note = payload.get("note", "Claimed via Lane 3 Agent Cloud")
            if not apt_num or not pat_num:
                raise HTTPException(status_code=400, detail="Missing apt_num or pat_num")
            try:
                result = await self.claim_slot(clinic_id, apt_num, pat_num, note)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def _handle_inbound_message(self, connection: ClinicConnection, msg: Dict[str, Any]):
        msg_type = msg.get("type")
        request_id = msg.get("request_id")

        if msg_type == "HEARTBEAT":
            client_time = msg.get("client_time", time.time())
            connection.last_heartbeat = time.time()
            connection.latency_ms = max(0.1, (time.time() - client_time) * 1000)
            if "metadata" in msg:
                connection.metadata.update(msg["metadata"])
            await connection.websocket.send_json({"type": "HEARTBEAT_ACK", "server_time": time.time()})

        elif msg_type == "RPC_RESPONSE" and request_id:
            fut = connection.pending_requests.pop(request_id, None)
            if fut and not fut.done():
                if msg.get("status") == "SUCCESS":
                    fut.set_result(msg.get("result"))
                else:
                    fut.set_exception(RuntimeError(msg.get("error", "Unknown RPC error")))

    async def send_command(self, clinic_id: str, command: str, payload: Dict[str, Any], timeout: float = 5.0) -> Any:
        """Sends an RPC command over the outbound tunnel and awaits the result."""
        connection = self.active_clinics.get(clinic_id)
        if not connection:
            raise ConnectionError(f"Clinic '{clinic_id}' is not currently connected to the edge gateway.")

        req_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        connection.pending_requests[req_id] = future

        message = {
            "type": "RPC_REQUEST",
            "request_id": req_id,
            "command": command,
            "payload": payload,
            "dispatched_at": time.time()
        }

        await connection.websocket.send_json(message)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            connection.pending_requests.pop(req_id, None)
            raise TimeoutError(f"RPC command '{command}' to clinic '{clinic_id}' timed out after {timeout}s.")

    async def execute_query(self, clinic_id: str, sql: str, params: Optional[List[Any]] = None, timeout: float = 5.0) -> Dict[str, Any]:
        """Execute a sanitized read query on the clinic's local database."""
        return await self.send_command(
            clinic_id=clinic_id,
            command="SQL_QUERY",
            payload={"sql": sql, "params": params or []},
            timeout=timeout
        )

    async def claim_slot(self, clinic_id: str, apt_num: int, pat_num: int, note: str = "") -> Dict[str, Any]:
        """Atomically claim a broken appointment slot in the local clinic database."""
        return await self.send_command(
            clinic_id=clinic_id,
            command="CLAIM_SLOT",
            payload={"apt_num": apt_num, "pat_num": pat_num, "note": note},
            timeout=5.0
        )
