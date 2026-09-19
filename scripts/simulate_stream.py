#!/usr/bin/env python3
import os
import sys
import json
import time
import argparse
import httpx

# ANSI Color Codes for terminal logging
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"

SOURCE_MAP = {
    "citizen_call": "citizen",
    "citizen": "citizen",
    "call_center": "call_911",
    "call_911": "call_911",
    "field_team": "field_unit",
    "field_unit": "field_unit",
    "iot_sensor": "iot_sensor",
    "hospital": "hospital",
    "social_media": "social_media"
}


def print_banner(scenario_name: str, base_url: str, speed: float):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}========================================================================{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}         ResQAI Real-Time Emergency Stream Simulator                    {COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}========================================================================{COLOR_RESET}")
    print(f"  {COLOR_BOLD}Scenario:{COLOR_RESET} {scenario_name}")
    print(f"  {COLOR_BOLD}Base URL:{COLOR_RESET} {base_url}")
    print(f"  {COLOR_BOLD}Speed:{COLOR_RESET}    {speed}x")
    print(f"{COLOR_CYAN}------------------------------------------------------------------------{COLOR_RESET}\n", flush=True)


def format_severity(severity: str) -> str:
    sev_upper = str(severity).upper()
    if sev_upper == "CRITICAL":
        return f"{COLOR_BOLD}{COLOR_RED}CRITICAL{COLOR_RESET}"
    elif sev_upper == "HIGH":
        return f"{COLOR_BOLD}{COLOR_YELLOW}HIGH{COLOR_RESET}"
    elif sev_upper == "MEDIUM":
        return f"{COLOR_YELLOW}MEDIUM{COLOR_RESET}"
    else:
        return f"{COLOR_GREEN}LOW{COLOR_RESET}"


def format_merged(merged: bool) -> str:
    if merged:
        return f"{COLOR_BOLD}{COLOR_MAGENTA}[MERGED DUPLICATE]{COLOR_RESET}"
    else:
        return f"{COLOR_GREEN}[NEW INCIDENT]{COLOR_RESET}"


def run_simulation(base_url: str, scenario_name: str, speed: float, count_limit: int | None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenario_path = os.path.join(script_dir, "scenarios", f"{scenario_name}.json")
    if not os.path.exists(scenario_path):
        scenario_path = os.path.join("scripts", "scenarios", f"{scenario_name}.json")

    if not os.path.exists(scenario_path):
        print(f"{COLOR_RED}Error: Scenario file '{scenario_name}.json' not found at '{scenario_path}'.{COLOR_RESET}", flush=True)
        sys.exit(1)

    with open(scenario_path, "r", encoding="utf-8") as f:
        reports = json.load(f)

    if count_limit and count_limit > 0:
        reports = reports[:count_limit]

    print_banner(scenario_name, base_url, speed)

    client = httpx.Client(base_url=base_url, timeout=15.0)

    total_sent = 0
    merged_count = 0
    new_count = 0

    for idx, r_data in enumerate(reports, 1):
        delay = float(r_data.get("delay_sec", 0)) / max(speed, 0.1)
        if delay > 0 and idx > 1:
            time.sleep(delay)

        raw_src = r_data.get("source", "citizen")
        norm_src = SOURCE_MAP.get(raw_src.lower(), "citizen")

        payload = {
            "source": norm_src,
            "reporter": r_data.get("reporter", "Unknown"),
            "text": r_data.get("text", ""),
            "lat": float(r_data["lat"]),
            "lng": float(r_data["lng"]),
            "address": r_data.get("address"),
            "extra": r_data.get("extra")
        }

        try:
            start_t = time.time()
            res = client.post("/api/reports", json=payload)
            elapsed_ms = round((time.time() - start_t) * 1000, 1)

            if res.status_code in [200, 201]:
                data = res.json()
                merged = data.get("merged", False)
                inc_id = data.get("incident_id", "UNKNOWN")
                inc = data.get("incident", {})
                severity = inc.get("severity", "MEDIUM")
                rep_count = inc.get("report_count") or len(inc.get("reports", []))

                total_sent += 1
                if merged:
                    merged_count += 1
                else:
                    new_count += 1

                print(
                    f"{COLOR_BOLD}[Report {idx:02d}/{len(reports):02d}]{COLOR_RESET} "
                    f"Src: {COLOR_BLUE}{payload['source']:<10}{COLOR_RESET} | "
                    f"Status: {format_merged(merged):<25} | "
                    f"IncID: {COLOR_CYAN}{inc_id}{COLOR_RESET} | "
                    f"Reports Merged: {COLOR_BOLD}{rep_count}{COLOR_RESET} | "
                    f"Severity: {format_severity(severity)} | "
                    f"Latency: {elapsed_ms}ms",
                    flush=True
                )
                print(f"  -> \"{payload['text'][:85]}...\"", flush=True)
            else:
                print(f"{COLOR_RED}[Report {idx:02d}] Failed with HTTP {res.status_code}: {res.text}{COLOR_RESET}", flush=True)

        except Exception as err:
            print(f"{COLOR_RED}[Report {idx:02d}] Connection Error: {err}{COLOR_RESET}", flush=True)

    print(f"\n{COLOR_BOLD}{COLOR_CYAN}------------------------------------------------------------------------{COLOR_RESET}", flush=True)
    print(f"{COLOR_BOLD}Simulation Complete!{COLOR_RESET} Total Reports: {total_sent} | New Incidents: {new_count} | Merged Reports: {merged_count}", flush=True)
    print(f"{COLOR_BOLD}{COLOR_CYAN}========================================================================{COLOR_RESET}\n", flush=True)


def main():
    parser = argparse.ArgumentParser(description="ResQAI Realistic Emergency Ingestion Stream Simulator")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for ResQAI backend API")
    parser.add_argument("--scenario", default="factory_fire", help="Scenario name (factory_fire, flood, highway_accident, mixed_chaos)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier (e.g. 2.0 for 2x speed, 5.0 for 5x speed)")
    parser.add_argument("--count", type=int, default=None, help="Limit number of reports to send")

    args = parser.parse_args()
    run_simulation(args.base_url, args.scenario, args.speed, args.count)


if __name__ == "__main__":
    main()
