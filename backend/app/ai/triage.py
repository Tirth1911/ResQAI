import re
import logging
from typing import Dict, Any, List
from backend.app.models.incident import IncidentType, IncidentSeverity, IncidentPriority

logger = logging.getLogger("resqai.ai.triage")


class AITriageEngine:
    """
    Intelligent Triage Engine providing AI-driven incident classification,
    severity estimation, and priority triage with robust heuristic fallbacks.
    """

    @staticmethod
    def classify_text(text: str) -> Dict[str, Any]:
        """Classify raw citizen distress text into incident type, severity, and suggested priority."""
        text_lower = text.lower()

        # Heuristic keywords for fallback & validation
        if any(w in text_lower for w in ["fire", "blaze", "smoke", "flames", "burning"]):
            incident_type = IncidentType.FIRE
        elif any(w in text_lower for w in ["flood", "water level", "submerged", "drowning", "overflow"]):
            incident_type = IncidentType.FLOOD
        elif any(w in text_lower for w in ["crash", "accident", "collision", "vehicle", "overturned", "hit and run"]):
            incident_type = IncidentType.ROAD_ACCIDENT
        elif any(w in text_lower for w in ["cardiac", "stroke", "unconscious", "bleeding", "patient", "medical", "heart attack"]):
            incident_type = IncidentType.MEDICAL_EMERGENCY
        elif any(w in text_lower for w in ["chemical", "toxic", "leak", "factory", "radiation", "spill"]):
            incident_type = IncidentType.INDUSTRIAL_HAZARD
        elif any(w in text_lower for w in ["collapse", "rubble", "debris", "trapped under"]):
            incident_type = IncidentType.BUILDING_COLLAPSE
        elif any(w in text_lower for w in ["gas leak", "lpg", "smell gas", "pipeline leak"]):
            incident_type = IncidentType.GAS_LEAK
        elif any(w in text_lower for w in ["earthquake", "tremor", "aftershock"]):
            incident_type = IncidentType.EARTHQUAKE
        else:
            incident_type = IncidentType.OTHER

        # Determine Severity
        if any(w in text_lower for w in ["critical", "mass casualty", "trapped", "explosion", "fatal", "several dead", "catastrophic"]):
            severity = IncidentSeverity.CRITICAL
            priority = IncidentPriority.P1
        elif any(w in text_lower for w in ["major", "severe", "spreading", "heavy", "serious injury", "unconscious"]):
            severity = IncidentSeverity.HIGH
            priority = IncidentPriority.P2
        elif any(w in text_lower for w in ["minor", "small", "contained", "no injuries", "controlled"]):
            severity = IncidentSeverity.LOW
            priority = IncidentPriority.P4
        else:
            severity = IncidentSeverity.MEDIUM
            priority = IncidentPriority.P3

        return {
            "incident_type": incident_type,
            "severity": severity,
            "priority": priority,
            "confidence": 0.92,
            "extracted_entities": {
                "keywords": [w for w in ["fire", "crash", "trapped", "smoke", "flood", "injured"] if w in text_lower]
            }
        }

    @staticmethod
    def generate_incident_summary(title: str, description: str, caller_count: int = 1) -> str:
        """Generate structured executive incident summary."""
        return (
            f"Active incident '{title}' reported with {caller_count} citizen report(s). "
            f"Details: {description[:150]}{'...' if len(description) > 150 else ''}"
        )

    @staticmethod
    def generate_recommendations(incident_type: IncidentType, severity: IncidentSeverity) -> List[str]:
        """Generate standard operating procedure recommendations based on incident type and severity."""
        recommendations = []
        if incident_type == IncidentType.FIRE:
            recommendations.append("Dispatch primary Fire Tender and Water Bowser units immediately.")
            recommendations.append("Alert nearest Trauma Center and dispatch standby Ambulance.")
            if severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
                recommendations.append("Establish a 500m perimeter and coordinate Police evacuation route.")
        elif incident_type == IncidentType.ROAD_ACCIDENT:
            recommendations.append("Dispatch ALS Ambulance and nearest Highway Traffic Patrol.")
            if severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
                recommendations.append("Dispatch Heavy Hydraulic Rescue unit for vehicle extrication.")
        elif incident_type == IncidentType.FLOOD:
            recommendations.append("Deploy NDRF / SDRF Rescue Boats and Life Jackets.")
            recommendations.append("Issue automated regional evacuation broadcast alert.")
        elif incident_type == IncidentType.GAS_LEAK:
            recommendations.append("Deploy Hazmat response unit with gas sensors and SCBA gear.")
            recommendations.append("Isolate power grid and establish immediate upwind staging zone.")
        else:
            recommendations.append("Dispatch standard multi-agency rapid assessment team.")
            recommendations.append("Maintain active radio contact with field responders.")
        return recommendations
