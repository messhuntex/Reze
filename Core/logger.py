"""logger.py — Shared logger for Reze."""
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            "/data/data/com.termux/files/home/reze/logs/reze.log",
            mode="a", delay=True
        )
    ]
)
log = logging.getLogger("reze")
