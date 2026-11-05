"""One command to run the whole simulation.

    python simulator/run.py              normal campus; type fault commands while it runs
    python simulator/run.py --demo       same, plus a scripted fault timeline (about 3 minutes)
    python simulator/run.py --dry-run    print one tick of events as JSON and exit (no backend needed)

Type `help` while it runs to see the fault commands.
"""
from __future__ import annotations

import argparse
import json
import queue
import random
import sys
import threading
import time
from typing import List, Optional

from campus import Campus
from client import ApiError, BackendUnreachable, Client
from settings import load_settings

MAX_BATCH = 500      # the backend accepts at most 500 events per /events/batch call
STATUS_EVERY = 5     # print a status line every N ticks (changes are always printed)

# (seconds after start, command). Edit this to change the demo story.
DEMO = [
    (10, "kill-ap ap-b-02"),
    (30, "recover"),
    (40, "iot-fault reader-net-01"),
    (60, "recover"),
    (70, "congestion block-a"),
    (90, "recover"),
    (100, "lab-down lab-network"),
    (120, "recover"),
    (130, "uplink"),
    (155, "recover"),
]

HELP = """commands (arguments are optional):
  kill-ap [ap-id]            one AP dies                    default ap-b-02
  degrade-block [block]      every AP in a block degrades   default block-b
  lab-down [lab]             a lab network goes down        default lab-network
  congestion [block]         a block gets overloaded        default block-a
  uplink                     the whole campus loses internet
  iot-fault [device-id]      an IoT device reports down     default reader-net-01
  recover [target]           fix everything, or one AP / device / location
  reset                      clear the backend and restart the simulation state
  status                     show what is currently faulty
  help, quit"""


class Quit(Exception):
    pass


def parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Campus Health simulator")
    p.add_argument("--url", help="backend URL (default: BACKEND_URL or http://localhost:8000)")
    p.add_argument("--tick", type=float, help="seconds between readings (default 2)")
    p.add_argument("--seed", type=int, help="random seed, for repeatable runs")
    p.add_argument("--demo", action="store_true", help="run the scripted fault timeline")
    p.add_argument("--no-reset", action="store_true", help="do not clear the backend at start")
    p.add_argument("--no-interactive", action="store_true", help="do not read commands from the keyboard")
    p.add_argument("--ticks", type=int, help="stop after this many ticks")
    p.add_argument("--dry-run", action="store_true", help="print events instead of sending them")
    return p.parse_args(argv)


def run_command(line: str, campus: Campus, client: Optional[Client]) -> str:
    parts = line.replace("_", "-").split()
    name, arg = parts[0].lower(), (parts[1] if len(parts) > 1 else None)
    if name == "kill-ap":
        return campus.kill_ap(arg or "ap-b-02")
    if name == "degrade-block":
        return campus.degrade_block(arg or "block-b")
    if name == "lab-down":
        return campus.lab_down(arg or "lab-network")
    if name == "congestion":
        return campus.congest(arg or "block-a")
    if name == "uplink":
        return campus.uplink_outage()
    if name == "iot-fault":
        return campus.iot_fault(arg or "reader-net-01")
    if name == "recover":
        return campus.recover(arg)
    if name == "reset":
        if client is not None:
            client.reset()
        campus.reset()
        return "backend cleared and simulator restarted"
    if name == "status":
        return ", ".join(campus.faults()) or "everything healthy"
    if name == "help":
        return HELP
    if name in ("quit", "exit"):
        raise Quit()
    raise ValueError(f"unknown command '{name}'. Type help.")


def send(client: Client, events: List[dict]) -> dict:
    total = {"accepted": 0, "duplicates": 0, "rejected": [], "tickets_opened": [], "tickets_resolved": []}
    for i in range(0, len(events), MAX_BATCH):
        result = client.send_batch(events[i:i + MAX_BATCH])
        total["accepted"] += result.get("accepted", 0)
        total["duplicates"] += result.get("duplicates", 0)
        total["rejected"] += result.get("rejected", [])
        total["tickets_opened"] += result.get("tickets_opened", [])
        total["tickets_resolved"] += result.get("tickets_resolved", [])
    return total


def report(tick: int, campus: Campus, sent: int, result: dict) -> None:
    changed = result["tickets_opened"] or result["tickets_resolved"] or result["rejected"]
    if not changed and tick % STATUS_EVERY:
        return
    hour = campus.sim_hour()
    faults = campus.faults()
    if len(faults) > 6:
        faults_text = f"{len(faults)} faulty ({', '.join(faults[:3])}, ...)"
    else:
        faults_text = ", ".join(faults) or "none"
    line = f"tick {tick:04d} | sim {int(hour):02d}:{int((hour % 1) * 60):02d} | sent {sent} | faults: {faults_text}"
    if result["tickets_opened"]:
        line += " | OPENED " + ", ".join(result["tickets_opened"])
    if result["tickets_resolved"]:
        line += " | RESOLVED " + ", ".join(result["tickets_resolved"])
    print(line, flush=True)
    for bad in result["rejected"]:
        print(f"   REJECTED event {bad.get('index')}: {bad.get('error')} {bad.get('details') or bad.get('keys')}", flush=True)


def _read_stdin(commands: "queue.Queue[str]") -> None:
    for line in sys.stdin:
        line = line.strip()
        if line:
            commands.put(line)


def wait_for_backend(client: Client, attempts: int = 5) -> bool:
    for attempt in range(1, attempts + 1):
        try:
            client.health()
            return True
        except BackendUnreachable as exc:
            print(f"backend not reachable ({exc}). Attempt {attempt}/{attempts}...", flush=True)
            time.sleep(2)
    return False


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    settings = load_settings()
    url = (args.url or settings.backend_url).rstrip("/")
    tick_seconds = args.tick or settings.tick_seconds
    seed = args.seed if args.seed is not None else settings.seed
    max_ticks = args.ticks if args.ticks is not None else (1 if args.dry_run else None)

    campus = Campus(random.Random(seed), settings.day_seconds, settings.start_hour, settings.blip_prob)
    client = None if args.dry_run else Client(url, settings.api_key)

    if client is not None:
        if not wait_for_backend(client):
            print(f"Could not reach the backend at {url}. Start it first:  cd backend && uvicorn app.main:app --port 8000")
            return 1
        if not args.no_reset:
            try:
                client.reset()
            except ApiError as exc:
                print(f"Reset refused ({exc}). Check INGEST_API_KEY.")
                return 1
        print(f"Simulating against {url}  (tick {tick_seconds}s). Type 'help' for fault commands, Ctrl+C to stop.", flush=True)

    commands: "queue.Queue[str]" = queue.Queue()
    if not args.no_interactive and not args.dry_run:
        threading.Thread(target=_read_stdin, args=(commands,), daemon=True).start()
    scripted = list(DEMO) if args.demo else []

    start = time.monotonic()
    failures = 0
    tick = 0
    try:
        while max_ticks is None or tick < max_ticks:
            began = time.monotonic()
            while scripted and scripted[0][0] <= began - start:
                commands.put(scripted.pop(0)[1])
            while True:
                try:
                    line = commands.get_nowait()
                except queue.Empty:
                    break
                try:
                    message = run_command(line, campus, client)
                except Quit:
                    print("bye")
                    return 0
                except ValueError as exc:
                    message = f"! {exc}"
                except (ApiError, BackendUnreachable) as exc:
                    message = f"! backend error: {exc}"
                print(f">> {line}\n   {message}", flush=True)

            events = campus.tick_events(tick)
            if client is None:
                for event in events:
                    print(json.dumps(event))
            else:
                try:
                    result = send(client, events)
                    failures = 0
                    report(tick, campus, len(events), result)
                except (ApiError, BackendUnreachable) as exc:
                    failures += 1
                    if failures == 1 or failures % 10 == 0:
                        print(f"tick {tick:04d} | send failed ({failures} in a row): {exc}", flush=True)
            tick += 1
            time.sleep(max(0.0, tick_seconds - (time.monotonic() - began)))
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
