import logging
from datetime import datetime, timezone
from typing import Any

from app.models import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ReportSource,
    SEVERITY_PRIORITY_MAP,
)
from app.schemas import ReportIn

logger = logging.getLogger("resqai.ingest")


def normalize_text(text: str) -> str:
    """Strip extraneous whitespace and truncate text to 2000 characters."""
    if not text:
        return ""
    cleaned = " ".join(text.strip().split())
    return cleaned[:2000]


def normalize_report(report: ReportIn) -> tuple[str, str]:
    """
    Normalizes report payload into a tuple: (title, cleaned_text).
    Source-specific logic:
    - iot_sensor: builds or enriches text from extra (e.g. sensor type, value, unit).
    - hospital: formats bed shortages, mass-casualty surge, or casualty counts.
    - others: clean, normalize whitespace, truncate to 2000 chars.
    """
    source = report.source
    extra = report.extra or {}
    raw_text = normalize_text(report.text)
    loc_desc = report.address or f"coordinates [{report.lat:.4f}, {report.lng:.4f}]"

    if source == ReportSource.IOT_SENSOR:
        sensor = extra.get("sensor") or extra.get("sensor_type") or "telemetry"
        value = extra.get("value", "")
        unit = extra.get("unit", "")
        reading_str = f"{value} {unit}".strip() if value != "" else ""

        if reading_str:
            sensor_text = f"IoT {sensor} sensor reading {reading_str} at {loc_desc}."
        else:
            sensor_text = f"IoT {sensor} sensor trigger at {loc_desc}."

        final_text = f"{sensor_text} {raw_text}".strip() if raw_text else sensor_text
        title = f"IoT Alert: {sensor.capitalize()} Detection"
        return title, final_text[:2000]

    if source == ReportSource.HOSPITAL:
        casualties = extra.get("incoming_casualties") or extra.get("casualties")
        beds_available = extra.get("beds_available")
        shortage = extra.get("bed_shortage")

        phrases: list[str] = []
        if casualties:
            phrases.append(f"Incoming mass casualties: {casualties}")
        if shortage or beds_available == 0:
            phrases.append("Critical bed shortage reported")
        elif beds_available is not None:
            phrases.append(f"Available emergency beds: {beds_available}")

        extra_text = ". ".join(phrases)
        if extra_text:
            final_text = f"Hospital Notice at {loc_desc}: {extra_text}. {raw_text}".strip()
            title = f"Hospital Emergency Surge: {loc_desc}"
        else:
            final_text = f"Hospital Notice at {loc_desc}: {raw_text}".strip()
            title = f"Hospital Report: {loc_desc}"
        return title, final_text[:2000]

    # citizen, call_center, field_team, government
    title_prefix_map = {
        ReportSource.CITIZEN: "Citizen Incident Report",
        ReportSource.CALL_CENTER: "Helpline Emergency Call",
        ReportSource.FIELD_TEAM: "Field Responder Dispatch Report",
        ReportSource.GOVERNMENT: "Official Emergency Directive",
    }
    prefix = title_prefix_map.get(source, "Incident Report")
    title = f"{prefix} at {loc_desc}"
    return title, raw_text
