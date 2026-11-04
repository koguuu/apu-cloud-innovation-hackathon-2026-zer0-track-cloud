"""Master Launcher for Campus Wi-Fi Health AIOps Platform.
Usage: python start.py [--port 8080]
"""

import argparse
import sys
import os

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.server import run_server
from backend.config import SERVER_PORT

def main():
    parser = argparse.ArgumentParser(description="Campus Wi-Fi Health AIOps Platform")
    parser.add_argument("--port", type=int, default=SERVER_PORT, help="Port to run server on (default: 8080)")
    args = parser.parse_args()

    run_server(args.port)

if __name__ == "__main__":
    main()
