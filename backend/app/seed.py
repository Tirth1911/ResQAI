import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from bson import ObjectId

from app.db import (
    ensure_indexes,
    get_alerts_collection,
    get_assignments_collection,
    get_db,
    get_incidents_collection,
    get_notifications_collection,
    get_resources_collection,
    to_geojson,
)
from app.models import (
    AssignmentStatus,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ReportSource,
    ResourceKind,
    ResourceStatus,
    SEVERITY_PRIORITY_MAP,
)

logger = logging.getLogger("resqai.seed")


# 35 Seed Resources around Ahmedabad & Gandhinagar (~30km radius of 23.0225, 72.5714)
SEED_RESOURCES: list[dict[str, Any]] = [
    # 8 Fire Trucks (Capabilities: fire, industrial)
    {
        "name": "Navrangpura Fire Engine 1",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0365,
        "lng": 72.5610,
        "capacity": 6,
        "capabilities": [IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Navrangpura Fire Station",
    },
    {
        "name": "Danapith Central Fire Engine 2",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0245,
        "lng": 72.5875,
        "capacity": 8,
        "capabilities": [IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Danapith Central Fire Station",
    },
    {
        "name": "Memnagar Quick Response Tender",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0510,
        "lng": 72.5350,
        "capacity": 5,
        "capabilities": [IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Memnagar Fire Station",
    },
    {
        "name": "Maninagar Heavy Water Bowzer",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.AVAILABLE,
        "lat": 22.9980,
        "lng": 72.6030,
        "capacity": 6,
        "capabilities": [IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Maninagar Fire Station",
    },
    {
        "name": "Naroda GIDC Chemical Foam Tender",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0720,
        "lng": 72.6640,
        "capacity": 6,
        "capabilities": [IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Naroda GIDC Fire Station",
    },
    {
        "name": "Odhav Industrial Fire Engine",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0280,
        "lng": 72.6510,
        "capacity": 6,
        "capabilities": [IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Odhav Fire Station",
    },
    {
        "name": "Gandhinagar Sector 17 Tender 1",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.2300,
        "lng": 72.6410,
        "capacity": 7,
        "capabilities": [IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Gandhinagar Sector 17 Fire Station",
    },
    {
        "name": "Chandkheda Multi-Purpose Tender",
        "kind": ResourceKind.FIRE_TRUCK,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.1120,
        "lng": 72.5880,
        "capacity": 6,
        "capabilities": [IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Chandkheda Fire Station",
    },

    # 8 Ambulances (Capabilities: medical, accident)
    {
        "name": "108 EMRI ALS Ambulance 01",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0140,
        "lng": 72.5650,
        "capacity": 4,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Paldi Emergency Outpost",
    },
    {
        "name": "108 EMRI ALS Ambulance 02",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0350,
        "lng": 72.5290,
        "capacity": 4,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Vastrapur Emergency Outpost",
    },
    {
        "name": "108 EMRI BLS Ambulance 03",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0530,
        "lng": 72.6040,
        "capacity": 3,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Civil Asarwa EMRI Hub",
    },
    {
        "name": "108 EMRI ALS Ambulance 04",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0770,
        "lng": 72.5230,
        "capacity": 4,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Sola Civil EMRI Hub",
    },
    {
        "name": "108 EMRI BLS Ambulance 05",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "lat": 22.9820,
        "lng": 72.5920,
        "capacity": 3,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Isanpur Emergency Outpost",
    },
    {
        "name": "108 EMRI ALS Ambulance 06",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0360,
        "lng": 72.4680,
        "capacity": 4,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Bopal Circle Health Hub",
    },
    {
        "name": "108 EMRI ALS Ambulance 07",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.2210,
        "lng": 72.6530,
        "capacity": 4,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Gandhinagar Civil EMRI Outpost",
    },
    {
        "name": "108 EMRI BLS Ambulance 08",
        "kind": ResourceKind.AMBULANCE,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0650,
        "lng": 72.6520,
        "capacity": 3,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Naroda Industrial Outpost",
    },

    # 5 Police Units (Capabilities: accident, other)
    {
        "name": "Ahmedabad Police PCR Alpha 1",
        "kind": ResourceKind.POLICE_UNIT,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0380,
        "lng": 72.5560,
        "capacity": 4,
        "capabilities": [IncidentType.ACCIDENT, IncidentType.OTHER],
        "station": "Navrangpura Police Station",
    },
    {
        "name": "Ahmedabad Police PCR Bravo 2",
        "kind": ResourceKind.POLICE_UNIT,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0290,
        "lng": 72.5180,
        "capacity": 4,
        "capabilities": [IncidentType.ACCIDENT, IncidentType.OTHER],
        "station": "Satellite Police Station",
    },
    {
        "name": "Ahmedabad Police PCR Charlie 3",
        "kind": ResourceKind.POLICE_UNIT,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0280,
        "lng": 72.5980,
        "capacity": 4,
        "capabilities": [IncidentType.ACCIDENT, IncidentType.OTHER],
        "station": "Kalupur Police Station",
    },
    {
        "name": "Ahmedabad Police PCR Delta 4",
        "kind": ResourceKind.POLICE_UNIT,
        "status": ResourceStatus.AVAILABLE,
        "lat": 22.9640,
        "lng": 72.6240,
        "capacity": 4,
        "capabilities": [IncidentType.ACCIDENT, IncidentType.OTHER],
        "station": "Vatva Police Station",
    },
    {
        "name": "Gandhinagar Police PCR Echo 5",
        "kind": ResourceKind.POLICE_UNIT,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.1950,
        "lng": 72.6290,
        "capacity": 4,
        "capabilities": [IncidentType.ACCIDENT, IncidentType.OTHER],
        "station": "Infocity Police Station Gandhinagar",
    },

    # 4 Rescue Teams (Capabilities: flood, accident, industrial, fire)
    {
        "name": "NDRF Flood & Swift Water Team 1",
        "kind": ResourceKind.RESCUE_TEAM,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.2350,
        "lng": 72.6600,
        "capacity": 15,
        "capabilities": [IncidentType.FLOOD, IncidentType.ACCIDENT, IncidentType.INDUSTRIAL, IncidentType.FIRE],
        "station": "NDRF Gandhinagar Regional Station",
    },
    {
        "name": "SDRF Water Rescue Unit Sabarmati",
        "kind": ResourceKind.RESCUE_TEAM,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0410,
        "lng": 72.5760,
        "capacity": 12,
        "capabilities": [IncidentType.FLOOD, IncidentType.ACCIDENT, IncidentType.INDUSTRIAL, IncidentType.FIRE],
        "station": "Sabarmati Riverfront Rescue Post",
    },
    {
        "name": "Civil Defence Urban Rescue Unit",
        "kind": ResourceKind.RESCUE_TEAM,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0580,
        "lng": 72.5920,
        "capacity": 10,
        "capabilities": [IncidentType.FLOOD, IncidentType.ACCIDENT, IncidentType.INDUSTRIAL, IncidentType.FIRE],
        "station": "Shahibaug Civil Defence HQ",
    },
    {
        "name": "AMC Disaster Rescue Cell Sarkhej",
        "kind": ResourceKind.RESCUE_TEAM,
        "status": ResourceStatus.AVAILABLE,
        "lat": 22.9890,
        "lng": 72.4980,
        "capacity": 10,
        "capabilities": [IncidentType.FLOOD, IncidentType.ACCIDENT, IncidentType.INDUSTRIAL, IncidentType.FIRE],
        "station": "Sarkhej Municipal Rescue Camp",
    },

    # 2 Disaster Response Teams (Capabilities: flood, fire, industrial)
    {
        "name": "NDRF 6th Battalion Heavy HAZMAT Team",
        "kind": ResourceKind.DISASTER_RESPONSE_TEAM,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.2510,
        "lng": 72.7050,
        "capacity": 25,
        "capabilities": [IncidentType.FLOOD, IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "NDRF Chiloda Battalion Base",
    },
    {
        "name": "Gujarat SDRF Major Incident Battalion",
        "kind": ResourceKind.DISASTER_RESPONSE_TEAM,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.1890,
        "lng": 72.6480,
        "capacity": 20,
        "capabilities": [IncidentType.FLOOD, IncidentType.FIRE, IncidentType.INDUSTRIAL],
        "station": "Gandhinagar SDRF State Headquarters",
    },

    # 4 Hospitals (Capacity = Available Beds)
    {
        "name": "Civil Hospital Ahmedabad",
        "kind": ResourceKind.HOSPITAL,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0528,
        "lng": 72.6035,
        "capacity": 250,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT, IncidentType.INDUSTRIAL],
        "station": "Asarwa Health Campus",
    },
    {
        "name": "GMERS Sola Civil Hospital",
        "kind": ResourceKind.HOSPITAL,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0768,
        "lng": 72.5262,
        "capacity": 140,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "SG Highway Medical Hub",
    },
    {
        "name": "Gandhinagar Civil Hospital",
        "kind": ResourceKind.HOSPITAL,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.2205,
        "lng": 72.6528,
        "capacity": 120,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT],
        "station": "Sector 12 Medical Complex",
    },
    {
        "name": "Sardar Vallabhbhai Patel (SVP) Hospital",
        "kind": ResourceKind.HOSPITAL,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0185,
        "lng": 72.5780,
        "capacity": 180,
        "capabilities": [IncidentType.MEDICAL, IncidentType.ACCIDENT, IncidentType.INDUSTRIAL],
        "station": "Ellisbridge Hospital Complex",
    },

    # 2 Relief Camps (Capacity = Shelter capacity)
    {
        "name": "Kankaria Community Relief Camp",
        "kind": ResourceKind.RELIEF_CAMP,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0060,
        "lng": 72.6010,
        "capacity": 300,
        "capabilities": [IncidentType.FLOOD, IncidentType.FIRE, IncidentType.OTHER],
        "station": "Kankaria Municipal Complex",
    },
    {
        "name": "Mahatma Mandir Disaster Relief Shelter",
        "kind": ResourceKind.RELIEF_CAMP,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.2340,
        "lng": 72.6350,
        "capacity": 500,
        "capabilities": [IncidentType.FLOOD, IncidentType.OTHER],
        "station": "Gandhinagar Convention Grounds",
    },

    # 2 Control Centers (Capacity = Personnel count)
    {
        "name": "Ahmedabad Smart City Command Centre",
        "kind": ResourceKind.CONTROL_CENTER,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.0230,
        "lng": 72.5720,
        "capacity": 45,
        "capabilities": [
            IncidentType.FIRE,
            IncidentType.FLOOD,
            IncidentType.ACCIDENT,
            IncidentType.MEDICAL,
            IncidentType.INDUSTRIAL,
            IncidentType.OTHER,
        ],
        "station": "AMC Civic Center Ashram Road",
    },
    {
        "name": "State Emergency Operation Centre (SEOC)",
        "kind": ResourceKind.CONTROL_CENTER,
        "status": ResourceStatus.AVAILABLE,
        "lat": 23.2180,
        "lng": 72.6510,
        "capacity": 60,
        "capabilities": [
            IncidentType.FIRE,
            IncidentType.FLOOD,
            IncidentType.ACCIDENT,
            IncidentType.MEDICAL,
            IncidentType.INDUSTRIAL,
            IncidentType.OTHER,
        ],
        "station": "Sachivalaya Gandhinagar",
    },
]


# 25 Historical Resolved Incidents Specifications
HISTORICAL_INCIDENTS_SPEC: list[dict[str, Any]] = [
    {
        "title": "Commercial Kitchen Cylinder Fire",
        "description": "LPG cylinder blaze broke out in restaurant kitchen near CG Road.",
        "type": IncidentType.FIRE,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.0315,
        "lng": 72.5580,
        "address": "CG Road, Navrangpura, Ahmedabad",
        "resource_kind": ResourceKind.FIRE_TRUCK,
        "days_ago": 28,
        "response_min": 8.5,
        "resolution_min": 45,
    },
    {
        "title": "Highway Multi-Car Collision",
        "description": "Chain collision involving three cars on SG Highway near Iscon cross road.",
        "type": IncidentType.ACCIDENT,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.0285,
        "lng": 72.5070,
        "address": "SG Highway near Iscon Cross Road, Ahmedabad",
        "resource_kind": ResourceKind.AMBULANCE,
        "days_ago": 27,
        "response_min": 6.2,
        "resolution_min": 35,
    },
    {
        "title": "Severe Flash Waterlogging",
        "description": "Underpass submerged after heavy downpour, trapping minivan.",
        "type": IncidentType.FLOOD,
        "severity": IncidentSeverity.MEDIUM,
        "lat": 23.0110,
        "lng": 72.5540,
        "address": "Parimal Underpass, Paldi, Ahmedabad",
        "resource_kind": ResourceKind.RESCUE_TEAM,
        "days_ago": 26,
        "response_min": 11.0,
        "resolution_min": 50,
    },
    {
        "title": "Industrial Boiler Overheat Alert",
        "description": "Chemical unit boiler pressure valve blew out with thick smoke.",
        "type": IncidentType.INDUSTRIAL,
        "severity": IncidentSeverity.CRITICAL,
        "lat": 23.0780,
        "lng": 72.6710,
        "address": "Phase 2, Naroda GIDC, Ahmedabad",
        "resource_kind": ResourceKind.FIRE_TRUCK,
        "days_ago": 25,
        "response_min": 7.8,
        "resolution_min": 80,
    },
    {
        "title": "Elderly Patient Acute Cardiac Emergency",
        "description": "Senior citizen collapsed at home experiencing chest tightness.",
        "type": IncidentType.MEDICAL,
        "severity": IncidentSeverity.CRITICAL,
        "lat": 23.0420,
        "lng": 72.5310,
        "address": "Judges Bungalow Road, Bodakdev, Ahmedabad",
        "resource_kind": ResourceKind.AMBULANCE,
        "days_ago": 24,
        "response_min": 5.4,
        "resolution_min": 25,
    },
    {
        "title": "Chemical Warehouse Solvent Leak",
        "description": "Volatile solvent vapor detected by perimeter IoT detector.",
        "type": IncidentType.INDUSTRIAL,
        "severity": IncidentSeverity.HIGH,
        "lat": 22.9580,
        "lng": 72.6310,
        "address": "Vatva Industrial Estate Phase 4, Ahmedabad",
        "resource_kind": ResourceKind.DISASTER_RESPONSE_TEAM,
        "days_ago": 23,
        "response_min": 9.3,
        "resolution_min": 65,
    },
    {
        "title": "Two-Wheeler Skidding Incident",
        "description": "Motorcyclist slipped on wet asphalt requiring basic medical care.",
        "type": IncidentType.ACCIDENT,
        "severity": IncidentSeverity.LOW,
        "lat": 23.0030,
        "lng": 72.5990,
        "address": "Maninagar Railway Crossing, Ahmedabad",
        "resource_kind": ResourceKind.POLICE_UNIT,
        "days_ago": 22,
        "response_min": 6.8,
        "resolution_min": 20,
    },
    {
        "title": "Residential Apartment Transformer Spark",
        "description": "Electrical transformer fire threatening nearby parked vehicles.",
        "type": IncidentType.FIRE,
        "severity": IncidentSeverity.MEDIUM,
        "lat": 23.0560,
        "lng": 72.5410,
        "address": "Gurukul Road, Memnagar, Ahmedabad",
        "resource_kind": ResourceKind.FIRE_TRUCK,
        "days_ago": 21,
        "response_min": 7.1,
        "resolution_min": 30,
    },
    {
        "title": "Sabarmati River Canal Breach Overflow",
        "description": "Canal water spill flooding agricultural access road.",
        "type": IncidentType.FLOOD,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.1850,
        "lng": 72.6150,
        "address": "Near Koba Circle, Gandhinagar",
        "resource_kind": ResourceKind.RESCUE_TEAM,
        "days_ago": 20,
        "response_min": 12.4,
        "resolution_min": 70,
    },
    {
        "title": "Pedestrian Hit and Run Incident",
        "description": "Pedestrian struck near bus stop requiring immediate trauma care.",
        "type": IncidentType.ACCIDENT,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.0210,
        "lng": 72.5830,
        "address": "Relief Road, Danapith, Ahmedabad",
        "resource_kind": ResourceKind.AMBULANCE,
        "days_ago": 19,
        "response_min": 5.9,
        "resolution_min": 35,
    },
    {
        "title": "Scrap Yard Plastic Fire",
        "description": "Extensive black smoke from scrap tires and plastics storage.",
        "type": IncidentType.FIRE,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.0330,
        "lng": 72.6580,
        "address": "Odhav Ring Road, Ahmedabad",
        "resource_kind": ResourceKind.FIRE_TRUCK,
        "days_ago": 18,
        "response_min": 8.0,
        "resolution_min": 55,
    },
    {
        "title": "Construction Scaffold Collapse",
        "description": "Scaffold collapsed injuring two workers on commercial site.",
        "type": IncidentType.INDUSTRIAL,
        "severity": IncidentSeverity.CRITICAL,
        "lat": 23.1970,
        "lng": 72.6320,
        "address": "Infocity Road, Sector 9, Gandhinagar",
        "resource_kind": ResourceKind.RESCUE_TEAM,
        "days_ago": 17,
        "response_min": 7.5,
        "resolution_min": 60,
    },
    {
        "title": "Severe Asthmatic Episode in School",
        "description": "Student in severe respiratory distress during sports event.",
        "type": IncidentType.MEDICAL,
        "severity": IncidentSeverity.MEDIUM,
        "lat": 23.1160,
        "lng": 72.5820,
        "address": "Chandkheda Main Road, Ahmedabad",
        "resource_kind": ResourceKind.AMBULANCE,
        "days_ago": 16,
        "response_min": 6.5,
        "resolution_min": 30,
    },
    {
        "title": "Stormwater Drain Jam & Street Submersion",
        "description": "High water levels blocking traffic access to market complex.",
        "type": IncidentType.FLOOD,
        "severity": IncidentSeverity.LOW,
        "lat": 22.9860,
        "lng": 72.5890,
        "address": "Isanpur Cross Road, Ahmedabad",
        "resource_kind": ResourceKind.POLICE_UNIT,
        "days_ago": 15,
        "response_min": 9.0,
        "resolution_min": 40,
    },
    {
        "title": "Roadside Tree Fall on Vehicle",
        "description": "Heavy monsoon winds toppled a banyan tree onto an auto-rickshaw.",
        "type": IncidentType.ACCIDENT,
        "severity": IncidentSeverity.MEDIUM,
        "lat": 23.0510,
        "lng": 72.5890,
        "address": "Shahibaug Underbridge Road, Ahmedabad",
        "resource_kind": ResourceKind.RESCUE_TEAM,
        "days_ago": 14,
        "response_min": 8.2,
        "resolution_min": 45,
    },
    {
        "title": "Government Office Basement Electrical Fire",
        "description": "Server room UPS batteries short-circuited creating toxic smoke.",
        "type": IncidentType.FIRE,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.2240,
        "lng": 72.6450,
        "address": "Sector 10, Gandhinagar",
        "resource_kind": ResourceKind.FIRE_TRUCK,
        "days_ago": 13,
        "response_min": 6.8,
        "resolution_min": 40,
    },
    {
        "title": "Chemical Tanker Valve Leakage",
        "description": "Tanker transporting acetic acid leaking on highway shoulder.",
        "type": IncidentType.INDUSTRIAL,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.2420,
        "lng": 72.6950,
        "address": "Chiloda National Highway Junction, Gandhinagar",
        "resource_kind": ResourceKind.DISASTER_RESPONSE_TEAM,
        "days_ago": 12,
        "response_min": 10.5,
        "resolution_min": 75,
    },
    {
        "title": "Pedestrian Heatstroke Near Bus Terminal",
        "description": "Commuter collapsed unconscious from extreme summer heat.",
        "type": IncidentType.MEDICAL,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.0260,
        "lng": 72.5950,
        "address": "Kalupur Central Bus Station, Ahmedabad",
        "resource_kind": ResourceKind.AMBULANCE,
        "days_ago": 11,
        "response_min": 5.1,
        "resolution_min": 25,
    },
    {
        "title": "Riverfront Walkway Crowd Panic Incident",
        "description": "Minor stampede scare on festival night, crowd control required.",
        "type": IncidentType.OTHER,
        "severity": IncidentSeverity.MEDIUM,
        "lat": 23.0400,
        "lng": 72.5730,
        "address": "Sabarmati Riverfront West Promenade, Ahmedabad",
        "resource_kind": ResourceKind.POLICE_UNIT,
        "days_ago": 10,
        "response_min": 5.5,
        "resolution_min": 35,
    },
    {
        "title": "Residential Balcony Structure Collapse",
        "description": "Old building balcony crumbled onto street below with minor injury.",
        "type": IncidentType.ACCIDENT,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.0170,
        "lng": 72.5730,
        "address": "Ellisbridge Heritage Ward, Ahmedabad",
        "resource_kind": ResourceKind.RESCUE_TEAM,
        "days_ago": 8,
        "response_min": 7.0,
        "resolution_min": 50,
    },
    {
        "title": "Textile Mill Dyeing Unit Fire",
        "description": "Spark caught cotton fabric rolls in drying chamber.",
        "type": IncidentType.FIRE,
        "severity": IncidentSeverity.CRITICAL,
        "lat": 23.0640,
        "lng": 72.6610,
        "address": "Naroda Industrial Zone, Ahmedabad",
        "resource_kind": ResourceKind.FIRE_TRUCK,
        "days_ago": 6,
        "response_min": 6.9,
        "resolution_min": 90,
    },
    {
        "title": "Delivery Van and Bus Collision",
        "description": "Collision near BRTS corridor causing passenger minor fractures.",
        "type": IncidentType.ACCIDENT,
        "severity": IncidentSeverity.MEDIUM,
        "lat": 23.0370,
        "lng": 72.4720,
        "address": "Bopal Ambli BRTS Corridor, Ahmedabad",
        "resource_kind": ResourceKind.AMBULANCE,
        "days_ago": 5,
        "response_min": 6.4,
        "resolution_min": 30,
    },
    {
        "title": "Low-Lying Slum Monsoon Flood Threat",
        "description": "Drainage backup inundating 40 shanties near lake overflow.",
        "type": IncidentType.FLOOD,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.0040,
        "lng": 72.6040,
        "address": "South Kankaria Slum Enclave, Ahmedabad",
        "resource_kind": ResourceKind.RESCUE_TEAM,
        "days_ago": 4,
        "response_min": 10.2,
        "resolution_min": 85,
    },
    {
        "title": "Severe Allergic Shock at Restaurant",
        "description": "Diner went into anaphylaxis following seafood consumption.",
        "type": IncidentType.MEDICAL,
        "severity": IncidentSeverity.HIGH,
        "lat": 23.0340,
        "lng": 72.5320,
        "address": "Vastrapur Lake Commercial Hub, Ahmedabad",
        "resource_kind": ResourceKind.AMBULANCE,
        "days_ago": 2,
        "response_min": 5.0,
        "resolution_min": 25,
    },
    {
        "title": "Suspicious Gas Odor Near Commercial Mall",
        "description": "Pungent smell investigated and traced to cracked LPG feeder line.",
        "type": IncidentType.OTHER,
        "severity": IncidentSeverity.LOW,
        "lat": 23.0750,
        "lng": 72.5280,
        "address": "Near Sola Science City Road, Ahmedabad",
        "resource_kind": ResourceKind.POLICE_UNIT,
        "days_ago": 1,
        "response_min": 7.2,
        "resolution_min": 30,
    },
]


async def seed(db_name: Optional[str] = None, reset: bool = False) -> None:
    """
    Idempotently seeds database with resources, historical resolved incidents,
    and completed assignments.
    """
    db = get_db(db_name)
    resources_col = get_resources_collection(db_name)
    incidents_col = get_incidents_collection(db_name)
    assignments_col = get_assignments_collection(db_name)
    alerts_col = get_alerts_collection(db_name)
    notifications_col = get_notifications_collection(db_name)

    if reset:
        logger.info("Resetting collections in database '%s'...", db.name)
        await resources_col.delete_many({})
        await incidents_col.delete_many({})
        await assignments_col.delete_many({})
        await alerts_col.delete_many({})
        await notifications_col.delete_many({})

    # Ensure indexes are established
    await ensure_indexes(db_name)

    # Idempotency check: if resources already exist and not resetting, skip
    existing_count = await resources_col.count_documents({})
    if existing_count > 0:
        logger.info(
            "Database '%s' already contains %d resources. Skipping seed.",
            db.name,
            existing_count,
        )
        return

    logger.info("Seeding resources in database '%s'...", db.name)
    now = datetime.now(timezone.utc)

    # 1. Insert Resources
    resource_docs: list[dict[str, Any]] = []
    for r in SEED_RESOURCES:
        resource_docs.append({
            "name": r["name"],
            "kind": r["kind"],
            "status": r["status"],
            "location": to_geojson(r["lat"], r["lng"]),
            "capacity": r["capacity"],
            "capabilities": r["capabilities"],
            "station": r["station"],
            "updated_at": now,
        })

    insert_res = await resources_col.insert_many(resource_docs)
    inserted_ids = insert_res.inserted_ids
    logger.info("Inserted %d resources.", len(inserted_ids))

    # Fetch inserted resources mapped by kind for assignment pairing
    cursor = resources_col.find({})
    seeded_by_kind: dict[ResourceKind, list[dict[str, Any]]] = {}
    async for res in cursor:
        k = res["kind"]
        seeded_by_kind.setdefault(k, []).append(res)

    # 2. Insert 25 Historical Resolved Incidents & Completed Assignments
    logger.info("Seeding 25 historical resolved incidents and assignments...")
    incident_docs: list[dict[str, Any]] = []
    assignment_docs: list[dict[str, Any]] = []

    for spec in HISTORICAL_INCIDENTS_SPEC:
        inc_id = ObjectId()
        created_at = now - timedelta(
            days=spec["days_ago"],
            minutes=spec["resolution_min"] + 15,
        )
        resolved_at = created_at + timedelta(minutes=spec["resolution_min"])
        assigned_at = created_at + timedelta(minutes=2)
        reported_at = created_at - timedelta(minutes=1)

        geo = to_geojson(spec["lat"], spec["lng"])

        report = {
            "source": ReportSource.CITIZEN,
            "reporter": "Citizen Witness",
            "raw_text": spec["description"],
            "location": geo,
            "reported_at": reported_at,
        }

        severity = spec["severity"]
        priority = SEVERITY_PRIORITY_MAP[severity]

        incident_doc = {
            "_id": inc_id,
            "title": spec["title"],
            "description": spec["description"],
            "type": spec["type"],
            "severity": severity,
            "priority": priority,
            "status": IncidentStatus.RESOLVED,
            "location": geo,
            "address": spec["address"],
            "source": ReportSource.CITIZEN,
            "report_count": 1,
            "reports": [report],
            "ai_confidence": 0.94,
            "ai_reasoning": "High-confidence extraction matching keywords and caller context.",
            "classified_by": "rules",
            "ai_assist": None,
            "created_at": created_at,
            "updated_at": resolved_at,
            "resolved_at": resolved_at,
        }
        incident_docs.append(incident_doc)

        # Find matching seeded resource
        candidates = seeded_by_kind.get(spec["resource_kind"], [])
        chosen_res = candidates[0] if candidates else list(seeded_by_kind.values())[0][0]

        assignment_doc = {
            "incident_id": inc_id,
            "resource_id": chosen_res["_id"],
            "status": AssignmentStatus.COMPLETED,
            "score": 0.92,
            "distance_km": round(spec["response_min"] * 0.45, 2),
            "eta_min": spec["response_min"],
            "assigned_at": assigned_at,
            "updated_at": resolved_at,
            "completed_at": resolved_at,
        }
        assignment_docs.append(assignment_doc)

    await incidents_col.insert_many(incident_docs)
    await assignments_col.insert_many(assignment_docs)
    logger.info(
        "Inserted %d historical incidents and %d assignments.",
        len(incident_docs),
        len(assignment_docs),
    )


def main() -> None:
    """CLI entry point: python -m app.seed [--reset]"""
    reset = "--reset" in sys.argv
    logging.basicConfig(level=logging.INFO)
    logger.info("Executing ResQAI seed CLI (reset=%s)...", reset)
    asyncio.run(seed(reset=reset))
    logger.info("Seed operation completed.")


if __name__ == "__main__":
    main()
