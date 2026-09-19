from typing import Optional, Dict, Any


def normalize_report_text(
    source: str,
    text: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    address: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> str:
    """Source-specific normalizers turning raw payload into a clean text description."""
    loc_str = address if address else f"Lat: {lat}, Lng: {lng}" if (lat is not None and lng is not None) else "location"
    source_str = str(source).lower()
    extra_dict = extra or {}

    if source_str in ["iot_sensor", "sensor", "iot"]:
        sensor = extra_dict.get("sensor", extra_dict.get("type", "sensor"))
        val = extra_dict.get("value", "N/A")
        unit = extra_dict.get("unit", "")
        unit_str = f" {unit}" if unit else ""
        norm_text = f"IoT {sensor} sensor reading {val}{unit_str} at {loc_str}."
        if text and text.strip():
            norm_text += f" {text.strip()}"
        return norm_text.strip()[:2000]

    elif source_str in ["hospital"]:
        event = extra_dict.get("event", "incident")
        casualties = extra_dict.get("casualty_count", extra_dict.get("casualties"))
        beds = extra_dict.get("beds_needed", extra_dict.get("beds"))

        phrases = []
        if casualties is not None:
            phrases.append(f"mass-casualty event with {casualties} casualties")
        if beds is not None:
            phrases.append(f"bed-shortage alert with {beds} beds needed")
        if not phrases:
            if extra_dict.get("type") == "bed_shortage" or extra_dict.get("alert") == "bed_shortage":
                phrases.append("bed-shortage alert")
            else:
                phrases.append(f"mass-casualty event: {event}")

        phrase_str = " and ".join(phrases)
        norm_text = f"Hospital report: {phrase_str} at {loc_str}."
        if text and text.strip():
            norm_text += f" {text.strip()}"
        return norm_text.strip()[:2000]

    else:
        # others: pass text through, strip whitespace, truncate to 2000 chars
        raw = (text or "").strip()
        if not raw:
            raw = f"Emergency report received from {source_str} at {loc_str}."
        return raw[:2000]
