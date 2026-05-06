import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from src.l1_ui.server import app, check_port
from src.l4_data.config import get_config

if __name__ == "__main__":
    import uvicorn

    config = get_config()
    check_port(config.server_port)
    uvicorn.run(app, host=config.server_host, port=config.server_port)
