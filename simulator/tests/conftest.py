import sys
from pathlib import Path

SIM = Path(__file__).resolve().parents[1]
BACKEND = SIM.parent / "backend"

sys.path.insert(0, str(SIM))      # so tests can import campus, settings, client, run
sys.path.append(str(BACKEND))     # so tests can use the backend's own models (optional)
