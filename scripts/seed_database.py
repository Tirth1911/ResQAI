"""
ResQAI - Complete MongoDB Database Seeder
Populates realistic Gujarat/India emergency demonstration data:
- 20+ Emergency Incidents (Fire, Flood, Road Crash, Hazmat, Medical, etc.)
- 16+ Multi-Agency Response Units (Ambulances, Fire Trucks, Police, Rescue Boats, Hazmat)
- 8+ Specialized Teams (NDRF, SDRF, Trauma, Quick Response, Hazmat)
- 8+ Multi-Speciality Emergency Hospitals with live ICU & bed capacities
- 8+ Emergency Broadcast Notifications
- Users and Initial System Analytics

Usage:
    python scripts/seed_database.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017"
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE") or os.getenv("MONGODB_DB_NAME") or "resqai"

NOW = datetime.utcnow()

# =============================================================================
# 1. REALISTIC INCIDENTS (21 Items across Gujarat Locations)
# =============================================================================
SAMPLE_INCIDENTS = [
    {
        "incident_id": "INC-1001",
        "source": "call_center",
        "type": "fire",
        "title": "Major Industrial Chemical Fire in GIDC Vatva",
        "description": "Explosion in solvent distillation plant. Dense black smoke plume visible across SP Ring Road. Multiple casualties suspected.",
        "severity": "CRITICAL",
        "priority": "P1",
        "status": "DISPATCHED",
        "location": {"type": "Point", "coordinates": [72.6324, 22.9568]},
        "address": "Phase IV, Vatva GIDC, Ahmedabad, Gujarat 382445",
        "reported_at": NOW - timedelta(minutes=15),
        "updated_at": NOW - timedelta(minutes=10),
        "ai_analysis": {
            "confidence": 0.96,
            "detected_hazards": ["Chemical explosion", "Toxic vapor cloud", "Thermal radiation"],
            "evacuation_radius_meters": 800,
            "required_units": ["FIRE_TRUCK", "AMBULANCE", "HAZMAT_TEAM"]
        },
        "duplicate_of": None,
        "confidence": 0.96,
        "assigned_resources": ["RES-2001", "RES-2002", "RES-2005"],
        "timeline": [
            {"timestamp": NOW - timedelta(minutes=15), "action": "Report Received", "actor": "Call Center (108)", "details": "Caller reported massive explosion"},
            {"timestamp": NOW - timedelta(minutes=13), "action": "AI Triage Completed", "actor": "AI Engine", "details": "Triaged as CRITICAL / P1"},
            {"timestamp": NOW - timedelta(minutes=10), "action": "Units Dispatched", "actor": "Dispatcher", "details": "Assigned RES-2001, RES-2002, RES-2005"}
        ]
    },
    {
        "incident_id": "INC-1002",
        "source": "iot",
        "type": "gas_leak",
        "title": "LPG Pipeline Pressure Drop & High Gas Concentration",
        "description": "IoT Gas Sensor telemetry triggered level-4 alarm in industrial cluster near SG Highway.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "VERIFIED",
        "location": {"type": "Point", "coordinates": [72.5074, 23.0338]},
        "address": "SG Highway near Iscon Cross Road, Ahmedabad, Gujarat 380015",
        "reported_at": NOW - timedelta(minutes=25),
        "updated_at": NOW - timedelta(minutes=20),
        "ai_analysis": {"confidence": 0.91, "gas_type": "LPG/Propane", "plume_direction": "North-East"},
        "duplicate_of": None,
        "confidence": 0.91,
        "assigned_resources": ["RES-2006"],
        "timeline": [
            {"timestamp": NOW - timedelta(minutes=25), "action": "IoT Sensor Alert", "actor": "Gas Grid Sensor #88", "details": "Threshold exceeded 500ppm"}
        ]
    },
    {
        "incident_id": "INC-1003",
        "source": "citizen",
        "type": "road_accident",
        "title": "Bus and Multi-Car Collision on NE-1 Expressway",
        "description": "State transport bus overturned following tire blowout. 4 passenger cars involved with multiple entrapped passengers.",
        "severity": "CRITICAL",
        "priority": "P1",
        "status": "IN_PROGRESS",
        "location": {"type": "Point", "coordinates": [72.7842, 22.7540]},
        "address": "Ahmedabad-Vadodara Expressway (NE-1) Km 42, Nadiad Bypass, Gujarat",
        "reported_at": NOW - timedelta(minutes=40),
        "updated_at": NOW - timedelta(minutes=5),
        "ai_analysis": {"confidence": 0.98, "casualties_estimated": 12, "extrication_required": True},
        "duplicate_of": None,
        "confidence": 0.98,
        "assigned_resources": ["RES-2003", "RES-2004", "RES-2007"],
        "timeline": [
            {"timestamp": NOW - timedelta(minutes=40), "action": "Citizen Report", "actor": "Citizen (Mobile App)", "details": "Distress call with live GPS"},
            {"timestamp": NOW - timedelta(minutes=35), "action": "First Responders Arrived", "actor": "Ambulance Team", "details": "Triage zone established"}
        ]
    },
    {
        "incident_id": "INC-1004",
        "source": "citizen",
        "type": "flood",
        "title": "Flash Flooding & Vishwamitri River Inundation",
        "description": "Heavy water release from Ajwa Dam flooded low-lying colonies. 200+ citizens stranded on rooftops.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "IN_PROGRESS",
        "location": {"type": "Point", "coordinates": [73.1812, 22.3072]},
        "address": "Sayajiganj & Fatehgunj riverside, Vadodara, Gujarat 390002",
        "reported_at": NOW - timedelta(hours=2),
        "updated_at": NOW - timedelta(minutes=30),
        "ai_analysis": {"confidence": 0.94, "water_level_m": 1.8, "recommended_units": ["RESCUE_TEAM", "RESCUE_BOAT"]},
        "duplicate_of": None,
        "confidence": 0.94,
        "assigned_resources": ["RES-2008", "RES-2009"],
        "timeline": []
    },
    {
        "incident_id": "INC-1005",
        "source": "citizen",
        "type": "building_collapse",
        "title": "Commercial Complex Balcony Collapse during Renovation",
        "description": "Old commercial structure partially collapsed into pedestrian market street. Several persons trapped under debris.",
        "severity": "CRITICAL",
        "priority": "P1",
        "status": "DISPATCHED",
        "location": {"type": "Point", "coordinates": [72.8311, 21.1702]},
        "address": "Ring Road Textile Market, Surat, Gujarat 395002",
        "reported_at": NOW - timedelta(minutes=50),
        "updated_at": NOW - timedelta(minutes=15),
        "ai_analysis": {"confidence": 0.95, "search_canines_needed": True, "heavy_crane_required": True},
        "duplicate_of": None,
        "confidence": 0.95,
        "assigned_resources": ["RES-2010", "RES-2011"],
        "timeline": []
    },
    {
        "incident_id": "INC-1006",
        "source": "field_team",
        "type": "medical_emergency",
        "title": "Mass Heat Exhaustion at Public Gathering",
        "description": "Multiple elderly citizens collapsed due to severe heat index during open-air rally.",
        "severity": "MEDIUM",
        "priority": "P3",
        "status": "IN_PROGRESS",
        "location": {"type": "Point", "coordinates": [72.6369, 23.2156]},
        "address": "Sector 11 Exhibition Grounds, Gandhinagar, Gujarat 382010",
        "reported_at": NOW - timedelta(minutes=70),
        "updated_at": NOW - timedelta(minutes=25),
        "ai_analysis": {"confidence": 0.89, "patients_count": 8, "triage_level": "Yellow"},
        "duplicate_of": None,
        "confidence": 0.89,
        "assigned_resources": ["RES-2012"],
        "timeline": []
    },
    {
        "incident_id": "INC-1007",
        "source": "iot",
        "type": "industrial_hazard",
        "title": "Petrochemical Pipeline Valve Rupture at Dahej PCPIR",
        "description": "Benzene vapor release detected in petrochemical zone storage farm.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "REPORTED",
        "location": {"type": "Point", "coordinates": [72.5833, 21.7000]},
        "address": "Dahej PCPIR Industrial Zone, Bharuch District, Gujarat 392130",
        "reported_at": NOW - timedelta(minutes=10),
        "updated_at": NOW - timedelta(minutes=10),
        "ai_analysis": {"confidence": 0.93, "chemical": "Benzene", "hazardous_zone_radius_km": 1.2},
        "duplicate_of": None,
        "confidence": 0.93,
        "assigned_resources": [],
        "timeline": []
    },
    {
        "incident_id": "INC-1008",
        "source": "citizen",
        "type": "fire",
        "title": "High-Rise Apartment Fire on 11th Floor",
        "description": "Flames shooting out of kitchen window in residential tower. Smoke spreading through central staircase.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "DISPATCHED",
        "location": {"type": "Point", "coordinates": [72.5293, 23.0525]},
        "address": "Bodakdev, Vastrapur Lake Road, Ahmedabad, Gujarat 380054",
        "reported_at": NOW - timedelta(minutes=35),
        "updated_at": NOW - timedelta(minutes=12),
        "ai_analysis": {"confidence": 0.97, "hydraulic_ladder_needed": True},
        "duplicate_of": None,
        "confidence": 0.97,
        "assigned_resources": ["RES-2001"],
        "timeline": []
    },
    {
        "incident_id": "INC-1009",
        "source": "call_center",
        "type": "road_accident",
        "title": "Tanker Overturned on NH-48 Highway",
        "description": "Diesel fuel tanker overturned, blocking south-bound lane. Fuel spilling on asphalt.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "VERIFIED",
        "location": {"type": "Point", "coordinates": [72.9342, 20.9467]},
        "address": "NH-48 Navsari Highway Junction, Gujarat 396445",
        "reported_at": NOW - timedelta(minutes=60),
        "updated_at": NOW - timedelta(minutes=30),
        "ai_analysis": {"confidence": 0.92, "fire_risk": "VERY_HIGH"},
        "duplicate_of": None,
        "confidence": 0.92,
        "assigned_resources": ["RES-2013"],
        "timeline": []
    },
    {
        "incident_id": "INC-1010",
        "source": "government",
        "type": "earthquake",
        "title": "Magnitude 4.2 Tremor Felt across Kutch Region",
        "description": "Seismic activity centered near Bhuj. Cracks reported in older masonry structures.",
        "severity": "MEDIUM",
        "priority": "P3",
        "status": "IN_PROGRESS",
        "location": {"type": "Point", "coordinates": [69.6667, 23.2500]},
        "address": "Bhuj City Center & Anjar Taluka, Kutch, Gujarat 370001",
        "reported_at": NOW - timedelta(hours=3),
        "updated_at": NOW - timedelta(hours=1),
        "ai_analysis": {"confidence": 0.99, "magnitude": 4.2, "aftershocks_possible": True},
        "duplicate_of": None,
        "confidence": 0.99,
        "assigned_resources": ["RES-2014"],
        "timeline": []
    },
    {
        "incident_id": "INC-1011",
        "source": "citizen",
        "type": "medical_emergency",
        "title": "Cardiac Arrest at Ahmedabad Railway Station",
        "description": "55-year old passenger collapsed on Platform 3. CPR in progress by RPF personnel.",
        "severity": "CRITICAL",
        "priority": "P1",
        "status": "IN_PROGRESS",
        "location": {"type": "Point", "coordinates": [72.6006, 23.0232]},
        "address": "Kalupur Railway Station, Ahmedabad, Gujarat 380002",
        "reported_at": NOW - timedelta(minutes=18),
        "updated_at": NOW - timedelta(minutes=8),
        "ai_analysis": {"confidence": 0.95, "aed_required": True, "golden_hour_critical": True},
        "duplicate_of": None,
        "confidence": 0.95,
        "assigned_resources": ["RES-2003"],
        "timeline": []
    },
    {
        "incident_id": "INC-1012",
        "source": "citizen",
        "type": "fire",
        "title": "Commercial Timber Yard Fire near Port Road",
        "description": "Stack of seasoned timber caught fire. High wind causing sparks toward adjacent godowns.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "DISPATCHED",
        "location": {"type": "Point", "coordinates": [72.1519, 21.7645]},
        "address": "Chitra GIDC, Bhavnagar, Gujarat 364004",
        "reported_at": NOW - timedelta(minutes=45),
        "updated_at": NOW - timedelta(minutes=15),
        "ai_analysis": {"confidence": 0.91, "water_bowsers_required": 4},
        "duplicate_of": None,
        "confidence": 0.91,
        "assigned_resources": ["RES-2015"],
        "timeline": []
    },
    {
        "incident_id": "INC-1013",
        "source": "simulation",
        "type": "road_accident",
        "title": "Simulation: 3-Vehicle Pileup in GIFT City Underpass",
        "description": "Simulated multi-vehicle incident for emergency response verification and drill assessment.",
        "severity": "MEDIUM",
        "priority": "P3",
        "status": "REPORTED",
        "location": {"type": "Point", "coordinates": [72.6842, 23.1593]},
        "address": "GIFT City Boulevard, Gandhinagar, Gujarat 382355",
        "reported_at": NOW - timedelta(minutes=5),
        "updated_at": NOW - timedelta(minutes=5),
        "ai_analysis": {"confidence": 0.99, "simulation_flag": True},
        "duplicate_of": None,
        "confidence": 0.99,
        "assigned_resources": [],
        "timeline": []
    },
    {
        "incident_id": "INC-1014",
        "source": "citizen",
        "type": "flood",
        "title": "Submerged Underpass Trapping 2 Cars during Monsoon Surge",
        "description": "Akhbarnagar underpass filled with 6 feet stormwater. Occupants climbed onto car roofs.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "IN_PROGRESS",
        "location": {"type": "Point", "coordinates": [72.5631, 23.0645]},
        "address": "Akhbarnagar Underpass, Nava Vadaj, Ahmedabad, Gujarat 380013",
        "reported_at": NOW - timedelta(minutes=30),
        "updated_at": NOW - timedelta(minutes=10),
        "ai_analysis": {"confidence": 0.94, "inflatable_boat_needed": True},
        "duplicate_of": None,
        "confidence": 0.94,
        "assigned_resources": ["RES-2008"],
        "timeline": []
    },
    {
        "incident_id": "INC-1015",
        "source": "field_team",
        "type": "medical_emergency",
        "title": "Severe Trauma at Construction Site",
        "description": "Construction worker fell from 3rd floor scaffolding. Severe head and spinal trauma.",
        "severity": "CRITICAL",
        "priority": "P1",
        "status": "DISPATCHED",
        "location": {"type": "Point", "coordinates": [70.8022, 22.3039]},
        "address": "Kalawad Road Construction Site, Rajkot, Gujarat 360005",
        "reported_at": NOW - timedelta(minutes=22),
        "updated_at": NOW - timedelta(minutes=10),
        "ai_analysis": {"confidence": 0.96, "als_ambulance_required": True},
        "duplicate_of": None,
        "confidence": 0.96,
        "assigned_resources": ["RES-2016"],
        "timeline": []
    },
    {
        "incident_id": "INC-1016",
        "source": "citizen",
        "type": "gas_leak",
        "title": "Domestic Gas Pipeline Damage by Earthmover",
        "description": "Excavator severed piped natural gas line in residential society. Loud hiss and gas odor.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "VERIFIED",
        "location": {"type": "Point", "coordinates": [72.5152, 23.0118]},
        "address": "Prahlad Nagar Garden Road, Ahmedabad, Gujarat 380015",
        "reported_at": NOW - timedelta(minutes=28),
        "updated_at": NOW - timedelta(minutes=14),
        "ai_analysis": {"confidence": 0.93, "evacuation_zone_meters": 300},
        "duplicate_of": None,
        "confidence": 0.93,
        "assigned_resources": ["RES-2006"],
        "timeline": []
    },
    {
        "incident_id": "INC-1017",
        "source": "iot",
        "type": "fire",
        "title": "Transformer Sparking and Oil Fire in Substation",
        "description": "Grid substation transformer failure ignited cooling oil. Local power cut initiated.",
        "severity": "HIGH",
        "priority": "P2",
        "status": "REPORTED",
        "location": {"type": "Point", "coordinates": [70.0667, 22.4707]},
        "address": "GIDC Phase 2, Jamnagar, Gujarat 361004",
        "reported_at": NOW - timedelta(minutes=12),
        "updated_at": NOW - timedelta(minutes=12),
        "ai_analysis": {"confidence": 0.92, "co2_extinguisher_needed": True},
        "duplicate_of": None,
        "confidence": 0.92,
        "assigned_resources": [],
        "timeline": []
    },
    {
        "incident_id": "INC-1018",
        "source": "call_center",
        "type": "road_accident",
        "title": "Motorcycle Skidded on Wet Flyover",
        "description": "Single rider skidded on Sabarmati Riverfront flyover. Conscious with fracture.",
        "severity": "LOW",
        "priority": "P4",
        "status": "RESOLVED",
        "location": {"type": "Point", "coordinates": [72.5760, 23.0330]},
        "address": "Riverfront East Flyover, Ahmedabad, Gujarat 380009",
        "reported_at": NOW - timedelta(hours=4),
        "updated_at": NOW - timedelta(hours=2),
        "ai_analysis": {"confidence": 0.90},
        "duplicate_of": None,
        "confidence": 0.90,
        "assigned_resources": [],
        "timeline": []
    },
    {
        "incident_id": "INC-1019",
        "source": "citizen",
        "type": "fire",
        "title": "Scrap Yard Fire near Sanand GIDC",
        "description": "Plastics and rubber scrap heap burning with intense heat near automobile vendor park.",
        "severity": "MEDIUM",
        "priority": "P3",
        "status": "VERIFIED",
        "location": {"type": "Point", "coordinates": [72.3812, 22.9867]},
        "address": "Sanand GIDC Gate 2, Sanand, Gujarat 382110",
        "reported_at": NOW - timedelta(minutes=55),
        "updated_at": NOW - timedelta(minutes=30),
        "ai_analysis": {"confidence": 0.88},
        "duplicate_of": None,
        "confidence": 0.88,
        "assigned_resources": [],
        "timeline": []
    },
    {
        "incident_id": "INC-1020",
        "source": "hospital",
        "type": "medical_emergency",
        "title": "Organ Transport Green Corridor Request",
        "description": "Live donor heart transfer from Civil Hospital Ahmedabad to KD Hospital requires green corridor.",
        "severity": "HIGH",
        "priority": "P1",
        "status": "IN_PROGRESS",
        "location": {"type": "Point", "coordinates": [72.5972, 23.0528]},
        "address": "Civil Hospital Trauma Center, Asarwa, Ahmedabad, Gujarat 380016",
        "reported_at": NOW - timedelta(minutes=20),
        "updated_at": NOW - timedelta(minutes=10),
        "ai_analysis": {"confidence": 0.99, "corridor_eta_minutes": 14},
        "duplicate_of": None,
        "confidence": 0.99,
        "assigned_resources": ["RES-2004", "RES-2007"],
        "timeline": []
    },
    {
        "incident_id": "INC-1021",
        "source": "citizen",
        "type": "building_collapse",
        "title": "Heritage Pol House Structural Wall Failure",
        "description": "Centuries-old wooden and brick structure wall collapsed after sustained monsoon seepage.",
        "severity": "MEDIUM",
        "priority": "P3",
        "status": "CLOSED",
        "location": {"type": "Point", "coordinates": [72.5890, 23.0245]},
        "address": "Dhal ni Pol, Khadia, Old City, Ahmedabad, Gujarat 380001",
        "reported_at": NOW - timedelta(days=1),
        "updated_at": NOW - timedelta(hours=18),
        "ai_analysis": {"confidence": 0.92},
        "duplicate_of": None,
        "confidence": 0.92,
        "assigned_resources": [],
        "timeline": []
    }
]

# =============================================================================
# 2. REALISTIC RESPONSE RESOURCES (16 Items)
# =============================================================================
SAMPLE_RESOURCES = [
    {
        "resource_id": "RES-2001",
        "name": "Ahmedabad Fire Tender 01 (Foam Bowser)",
        "category": "FIRE_TRUCK",
        "capabilities": ["Industrial Chemical Foam", "Hydraulic Platform 42m", "Thermal Imaging"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.6300, 22.9550]},
        "capacity": 6,
        "current_incident_id": "INC-1001",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2002",
        "name": "108 Advanced Life Support Ambulance #14",
        "category": "AMBULANCE",
        "capabilities": ["Ventilator", "Defibrillator / AED", "Trauma Kit", "Telemetry"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.6330, 22.9580]},
        "capacity": 2,
        "current_incident_id": "INC-1001",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2003",
        "name": "108 Emergency Ambulance #09 (Kalupur Hub)",
        "category": "AMBULANCE",
        "capabilities": ["Basic Life Support", "Spine Board", "Oxygen Support"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.6006, 23.0232]},
        "capacity": 2,
        "current_incident_id": "INC-1011",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2004",
        "name": "Expressway Highway Patrol Squad 03",
        "category": "POLICE",
        "capabilities": ["Traffic Diversion", "Hydraulic Cutters", "First Aid", "Speed Radar"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.7800, 22.7500]},
        "capacity": 4,
        "current_incident_id": "INC-1003",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2005",
        "name": "Hazmat Quick Response Unit (GIDC Hub)",
        "category": "DISASTER_TEAM",
        "capabilities": ["Chemical Neutralization", "Self-Contained Breathing App (SCBA)", "Gas Detection"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.6320, 22.9560]},
        "capacity": 4,
        "current_incident_id": "INC-1001",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2006",
        "name": "Gas Leak Mitigation Tender (Adani Gas)",
        "category": "DISASTER_TEAM",
        "capabilities": ["Pipeline Clamping", "Infrared Methane Camera", "Explosion Proof Gear"],
        "status": "EN_ROUTE",
        "location": {"type": "Point", "coordinates": [72.5100, 23.0300]},
        "capacity": 3,
        "current_incident_id": "INC-1002",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2007",
        "name": "Nadiad Trauma Resuscitation Mobile",
        "category": "MEDICAL_TEAM",
        "capabilities": ["Emergency Physician Onboard", "Blood Transfusion Kit", "Portable X-Ray"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.7842, 22.7540]},
        "capacity": 3,
        "current_incident_id": "INC-1003",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2008",
        "name": "SDRF Motorized Inflatable Rescue Boat 02",
        "category": "RESCUE_TEAM",
        "capabilities": ["40HP Outboard Motor", "Night Searchlight", "12 Life Jackets", "Sonar"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [73.1800, 22.3050]},
        "capacity": 8,
        "current_incident_id": "INC-1004",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2009",
        "name": "NDRF Flood Rescue Column Vadodara",
        "category": "DISASTER_TEAM",
        "capabilities": ["Deep Diving Gear", "Tree Cutters", "Rope Rescue Systems"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [73.1830, 22.3100]},
        "capacity": 10,
        "current_incident_id": "INC-1004",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2010",
        "name": "Surat Fire Brigade Heavy Rescue Tender",
        "category": "FIRE_TRUCK",
        "capabilities": ["50-ton Hydraulic Crane", "Pneumatic Lifting Bags", "Diamond Blade Cutters"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.8311, 21.1702]},
        "capacity": 6,
        "current_incident_id": "INC-1005",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2011",
        "name": "Surat Urban Search & Rescue Canine Unit",
        "category": "RESCUE_TEAM",
        "capabilities": ["Trained Scent Dogs", "Acoustic Listening Devices", "Fiber-optic Snake Cam"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.8300, 21.1720]},
        "capacity": 4,
        "current_incident_id": "INC-1005",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2012",
        "name": "Gandhinagar Rapid Heat Stress Clinic Bus",
        "category": "MEDICAL_TEAM",
        "capabilities": ["Cooling Misting Units", "Electrolyte Infusion", "Patient Cots"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.6369, 23.2156]},
        "capacity": 6,
        "current_incident_id": "INC-1006",
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2013",
        "name": "Navsari Fire Service Chemical Bowser",
        "category": "FIRE_TRUCK",
        "capabilities": ["Dry Chemical Powder (DCP)", "Foam Cannons", "Hazmat Barrier Tape"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [72.9342, 20.9467]},
        "capacity": 5,
        "current_incident_id": None,
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2014",
        "name": "Kutch SDRF Structural Assessment Team",
        "category": "DISASTER_TEAM",
        "capabilities": ["Laser Crack Monitoring", "Emergency Shoring Props", "Drone Aerial Recon"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [69.6667, 23.2500]},
        "capacity": 8,
        "current_incident_id": None,
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2015",
        "name": "Bhavnagar Port Fire Unit 04",
        "category": "FIRE_TRUCK",
        "capabilities": ["High Volume Monitor 6000 LPM", "Saltwater Ingestion Pump"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [72.1519, 21.7645]},
        "capacity": 6,
        "current_incident_id": None,
        "updated_at": NOW
    },
    {
        "resource_id": "RES-2016",
        "name": "Rajkot 108 ALS Ambulance #03",
        "category": "AMBULANCE",
        "capabilities": ["Advanced Cardiac Life Support", "Spine Immobilization"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [70.8022, 22.3039]},
        "capacity": 2,
        "current_incident_id": None,
        "updated_at": NOW
    }
]

# =============================================================================
# 3. REALISTIC EMERGENCY TEAMS (8 Teams)
# =============================================================================
SAMPLE_TEAMS = [
    {
        "team_id": "TEAM-3001",
        "name": "6th Battalion NDRF Quick Response Force",
        "type": "National Disaster Response",
        "members": [
            {"member_id": "MEM-01", "name": "Cmdr. Rajesh Rathod", "role": "Incident Commander", "contact": "+91-9825001101"},
            {"member_id": "MEM-02", "name": "Inspector Amit Solanki", "role": "Hazmat Specialist", "contact": "+91-9825001102"},
            {"member_id": "MEM-03", "name": "Sub-Insp. Vijay Parmar", "role": "Rope & Collapse Specialist", "contact": "+91-9825001103"}
        ],
        "capabilities": ["CBRN Defense", "Deep Flood Rescue", "Earthquake SAR", "Heavy Extrication"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [72.6842, 23.1593]}
    },
    {
        "team_id": "TEAM-3002",
        "name": "Ahmedabad Municipal Fire & Rescue Special Squad",
        "type": "Urban Fire & Rescue",
        "members": [
            {"member_id": "MEM-04", "name": "Chief Fire Officer Jayesh Patel", "role": "Team Lead", "contact": "+91-9825001104"},
            {"member_id": "MEM-05", "name": "Station Officer Rahul Trivedi", "role": "Hydraulic Operator", "contact": "+91-9825001105"}
        ],
        "capabilities": ["High-Rise Firefighting", "Chemical Foam Blanketing", "Thermal Search"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.5800, 23.0300]}
    },
    {
        "team_id": "TEAM-3003",
        "name": "Gujarat GVK-EMRI 108 Critical Care Paramedic Team",
        "type": "Emergency Medical Services",
        "members": [
            {"member_id": "MEM-06", "name": "Dr. Sneha Desai", "role": "Emergency Physician", "contact": "+91-9825001106"},
            {"member_id": "MEM-07", "name": "Paramedic Manish Joshi", "role": "ALS Specialist", "contact": "+91-9825001107"}
        ],
        "capabilities": ["Triage & Resuscitation", "Intubation", "Trauma Stabilization"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [72.6369, 23.2156]}
    },
    {
        "team_id": "TEAM-3004",
        "name": "Vadodara Flood & Aquatic Rescue Strike Team",
        "type": "Aquatic Rescue",
        "members": [
            {"member_id": "MEM-08", "name": "Diver Captain Nilesh Varma", "role": "Lead Diver", "contact": "+91-9825001108"},
            {"member_id": "MEM-09", "name": "Operator Chetan Gohil", "role": "Boat Master", "contact": "+91-9825001109"}
        ],
        "capabilities": ["Flood Inundation Evacuation", "Underwater Sonar Search", "Raft Operations"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [73.1812, 22.3072]}
    },
    {
        "team_id": "TEAM-3005",
        "name": "Surat Hazmat Disaster Response Division",
        "type": "Hazardous Materials Response",
        "members": [
            {"member_id": "MEM-10", "name": "Officer Pradeep Dave", "role": "Chemical Safety Officer", "contact": "+91-9825001110"}
        ],
        "capabilities": ["Toxic Plume Neutralization", "Level A Hazmat Suit Operations", "Decontamination"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [72.8311, 21.1702]}
    },
    {
        "team_id": "TEAM-3006",
        "name": "Gujarat Highway Emergency Golden Hour Patrol",
        "type": "Highway Traffic & Extrication",
        "members": [
            {"member_id": "MEM-11", "name": "Inspector Harish Zala", "role": "Patrol Commander", "contact": "+91-9825001111"}
        ],
        "capabilities": ["Heavy Vehicle Extrication", "High-Speed Corridor Clearing", "Air Ambulance Staging"],
        "status": "BUSY",
        "location": {"type": "Point", "coordinates": [72.7842, 22.7540]}
    },
    {
        "team_id": "TEAM-3007",
        "name": "Kutch Border & Seismic Quick Reaction Team",
        "type": "Seismic & Remote Rescue",
        "members": [
            {"member_id": "MEM-12", "name": "Captain Arvind Jadeja", "role": "Field Commander", "contact": "+91-9825001112"}
        ],
        "capabilities": ["Desert SAR", "Earthquake Rubble Extraction", "Satellite Communication Hub"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [69.6667, 23.2500]}
    },
    {
        "team_id": "TEAM-3008",
        "name": "Rajkot Multi-Agency Aerial Drone Recon Unit",
        "type": "Drone Surveillance & Recon",
        "members": [
            {"member_id": "MEM-13", "name": "Pilot Sanjay Barot", "role": "Chief Drone Operator", "contact": "+91-9825001113"}
        ],
        "capabilities": ["Thermal Mapping", "Live Video Streaming", "Payload Drop (Medical Supplies)"],
        "status": "AVAILABLE",
        "location": {"type": "Point", "coordinates": [70.8022, 22.3039]}
    }
]

# =============================================================================
# 4. REALISTIC EMERGENCY HOSPITALS (8 Hospitals)
# =============================================================================
SAMPLE_HOSPITALS = [
    {
        "hospital_id": "HOS-4001",
        "name": "Ahmedabad Civil Hospital & Trauma Centre",
        "location": {"type": "Point", "coordinates": [72.5972, 23.0528]},
        "beds_available": 142,
        "icu_available": 38,
        "emergency_capacity": 60,
        "status": "OPEN"
    },
    {
        "hospital_id": "HOS-4002",
        "name": "SVP Institute of Medical Sciences & Research (VS Hospital)",
        "location": {"type": "Point", "coordinates": [72.5714, 23.0225]},
        "beds_available": 85,
        "icu_available": 24,
        "emergency_capacity": 40,
        "status": "OPEN"
    },
    {
        "hospital_id": "HOS-4003",
        "name": "KD Multi-Speciality Hospital, SG Highway",
        "location": {"type": "Point", "coordinates": [72.5350, 23.1150]},
        "beds_available": 60,
        "icu_available": 18,
        "emergency_capacity": 30,
        "status": "OPEN"
    },
    {
        "hospital_id": "HOS-4004",
        "name": "Zydus Hospital & Trauma Unit, Thaltej",
        "location": {"type": "Point", "coordinates": [72.5180, 23.0640]},
        "beds_available": 45,
        "icu_available": 12,
        "emergency_capacity": 25,
        "status": "OPEN"
    },
    {
        "hospital_id": "HOS-4005",
        "name": "SSG Government Hospital, Vadodara",
        "location": {"type": "Point", "coordinates": [73.1890, 22.3050]},
        "beds_available": 72,
        "icu_available": 16,
        "emergency_capacity": 35,
        "status": "OPEN"
    },
    {
        "hospital_id": "HOS-4006",
        "name": "New Civil Hospital & Trauma Wing, Surat",
        "location": {"type": "Point", "coordinates": [72.8250, 21.1750]},
        "beds_available": 90,
        "icu_available": 28,
        "emergency_capacity": 45,
        "status": "OPEN"
    },
    {
        "hospital_id": "HOS-4007",
        "name": "AIIMS Rajkot Emergency Department",
        "location": {"type": "Point", "coordinates": [70.8200, 22.3400]},
        "beds_available": 110,
        "icu_available": 32,
        "emergency_capacity": 50,
        "status": "OPEN"
    },
    {
        "hospital_id": "HOS-4008",
        "name": "Sir Takhtsinhji General Hospital, Bhavnagar",
        "location": {"type": "Point", "coordinates": [72.1450, 21.7700]},
        "beds_available": 35,
        "icu_available": 8,
        "emergency_capacity": 20,
        "status": "LIMITED"
    }
]

# =============================================================================
# 5. SAMPLE NOTIFICATIONS (8 Items)
# =============================================================================
SAMPLE_NOTIFICATIONS = [
    {
        "notification_id": "NOTIF-5001",
        "title": "RED ALERT: GIDC Vatva Industrial Fire",
        "message": "Critical chemical explosion reported. Foam tender and hazmat containment units active. Evacuate 800m perimeter.",
        "type": "DISASTER_ALERT",
        "severity": "CRITICAL",
        "target_role": "ALL",
        "incident_id": "INC-1001",
        "created_at": NOW - timedelta(minutes=14),
        "read": False
    },
    {
        "notification_id": "NOTIF-5002",
        "title": "TRAFFIC DIVERSION: NE-1 Expressway Blocked",
        "message": "Major pileup near Nadiad bypass. South-bound traffic diverted via National Highway 48.",
        "type": "TRAFFIC_ALERT",
        "severity": "HIGH",
        "target_role": "DISPATCHER",
        "incident_id": "INC-1003",
        "created_at": NOW - timedelta(minutes=38),
        "read": False
    },
    {
        "notification_id": "NOTIF-5003",
        "title": "FLOOD WARNING: Vishwamitri River Spillover",
        "message": "Water release from Ajwa reservoir. Sayajiganj rescue boats deployed.",
        "type": "FLOOD_ALERT",
        "severity": "HIGH",
        "target_role": "ALL",
        "incident_id": "INC-1004",
        "created_at": NOW - timedelta(hours=2),
        "read": True
    },
    {
        "notification_id": "NOTIF-5004",
        "title": "RESOURCE DISPATCHED: RES-2001 & RES-2002",
        "message": "Ahmedabad Fire Tender and 108 ALS Ambulance dispatched to GIDC Vatva site.",
        "type": "DISPATCH_UPDATE",
        "severity": "MEDIUM",
        "target_role": "FIRST_RESPONDER",
        "incident_id": "INC-1001",
        "created_at": NOW - timedelta(minutes=10),
        "read": False
    },
    {
        "notification_id": "NOTIF-5005",
        "title": "GREEN CORRIDOR ACTIVE: Live Donor Transport",
        "message": "Green corridor enabled from Civil Hospital Asarwa to KD Hospital. Route clearance in effect.",
        "type": "MEDICAL_ALERT",
        "severity": "HIGH",
        "target_role": "DISPATCHER",
        "incident_id": "INC-1020",
        "created_at": NOW - timedelta(minutes=18),
        "read": False
    },
    {
        "notification_id": "NOTIF-5006",
        "title": "HOSPITAL ADVISORY: SSG Vadodara Trauma Surge",
        "message": "SSG Hospital has 16 ICU beds remaining. Standby triage team assigned for flood casualties.",
        "type": "HOSPITAL_STATUS",
        "severity": "MEDIUM",
        "target_role": "COMMANDER",
        "incident_id": "INC-1004",
        "created_at": NOW - timedelta(minutes=45),
        "read": True
    },
    {
        "notification_id": "NOTIF-5007",
        "title": "AI TRIAGE SUMMARY GENERATED",
        "message": "AI categorized INC-1005 (Surat Collapse) with 95% confidence. Heavy hydraulic crane required.",
        "type": "AI_INSIGHT",
        "severity": "HIGH",
        "target_role": "DISPATCHER",
        "incident_id": "INC-1005",
        "created_at": NOW - timedelta(minutes=48),
        "read": True
    },
    {
        "notification_id": "NOTIF-5008",
        "title": "SIMULATION SCENARIO READY: GIFT City Drill",
        "message": "Simulated multi-vehicle crash scenario INC-1013 injected for operator drill testing.",
        "type": "SYSTEM_NOTICE",
        "severity": "LOW",
        "target_role": "COMMANDER",
        "incident_id": "INC-1013",
        "created_at": NOW - timedelta(minutes=5),
        "read": False
    }
]

# =============================================================================
# 6. USERS & OPERATORS
# =============================================================================
SAMPLE_USERS = [
    {
        "user_id": "USR-6001",
        "name": "State Disaster Operations Chief",
        "email": "chief.ops@resqai.gujarat.gov.in",
        "role": "COMMANDER",
        "department": "Gujarat State Disaster Management Authority (GSDMA)",
        "phone": "+91-7923259901",
        "status": "ACTIVE",
        "created_at": NOW - timedelta(days=30)
    },
    {
        "user_id": "USR-6002",
        "name": "Senior Dispatch Officer - Central Hub",
        "email": "dispatch.central@resqai.gujarat.gov.in",
        "role": "DISPATCHER",
        "department": "Emergency Response Center (108/112)",
        "phone": "+91-7923259902",
        "status": "ACTIVE",
        "created_at": NOW - timedelta(days=30)
    }
]


async def seed_database():
    print("=" * 70)
    print(" ResQAI MongoDB Database Seeder (Gujarat Emergency Demonstration)")
    print("=" * 70)
    print(f"Connecting to: {MONGODB_URI}")
    print(f"Database:      {MONGODB_DATABASE}\n")

    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGODB_DATABASE]

    try:
        # 1. Ping connection test
        await client.admin.command("ping")
        print("[OK] Connected to MongoDB successfully.\n")

        # 2. Setup 2dsphere and unique query indexes across all collections
        print("Ensuring 2dsphere and query indexes on collections...")
        
        # incidents indexes
        await db.incidents.create_index([("location", "2dsphere")])
        await db.incidents.create_index([("incident_id", 1)], unique=True)
        await db.incidents.create_index([("status", 1)])
        await db.incidents.create_index([("severity", 1)])
        await db.incidents.create_index([("priority", 1)])
        await db.incidents.create_index([("type", 1)])
        await db.incidents.create_index([("reported_at", -1)])

        # resources indexes
        await db.resources.create_index([("location", "2dsphere")])
        await db.resources.create_index([("resource_id", 1)], unique=True)
        await db.resources.create_index([("status", 1)])
        await db.resources.create_index([("category", 1)])

        # teams indexes
        await db.teams.create_index([("location", "2dsphere")])
        await db.teams.create_index([("team_id", 1)], unique=True)
        await db.teams.create_index([("status", 1)])

        # hospitals indexes
        await db.hospitals.create_index([("location", "2dsphere")])
        await db.hospitals.create_index([("hospital_id", 1)], unique=True)
        await db.hospitals.create_index([("status", 1)])

        # notifications indexes
        await db.notifications.create_index([("notification_id", 1)], unique=True)
        await db.notifications.create_index([("created_at", -1)])

        # users indexes
        await db.users.create_index([("user_id", 1)], unique=True)
        await db.users.create_index([("email", 1)], unique=True)

        # incident_updates indexes
        await db.incident_updates.create_index([("update_id", 1)], unique=True)
        await db.incident_updates.create_index([("incident_id", 1), ("created_at", -1)])

        # analytics indexes
        await db.analytics.create_index([("timestamp", -1)])
        print("[OK] All 2dsphere and query indexes created.\n")

        # 3. Seed Incidents
        print(f"Seeding {len(SAMPLE_INCIDENTS)} Incidents...")
        for inc in SAMPLE_INCIDENTS:
            await db.incidents.update_one(
                {"incident_id": inc["incident_id"]},
                {"$set": inc},
                upsert=True
            )
        print(f"[OK] {len(SAMPLE_INCIDENTS)} Incidents seeded.")

        # 4. Seed Resources
        print(f"Seeding {len(SAMPLE_RESOURCES)} Emergency Resources...")
        for res in SAMPLE_RESOURCES:
            await db.resources.update_one(
                {"resource_id": res["resource_id"]},
                {"$set": res},
                upsert=True
            )
        print(f"[OK] {len(SAMPLE_RESOURCES)} Resources seeded.")

        # 5. Seed Teams
        print(f"Seeding {len(SAMPLE_TEAMS)} Emergency Teams...")
        for team in SAMPLE_TEAMS:
            await db.teams.update_one(
                {"team_id": team["team_id"]},
                {"$set": team},
                upsert=True
            )
        print(f"[OK] {len(SAMPLE_TEAMS)} Teams seeded.")

        # 6. Seed Hospitals
        print(f"Seeding {len(SAMPLE_HOSPITALS)} Emergency Hospitals...")
        for hosp in SAMPLE_HOSPITALS:
            await db.hospitals.update_one(
                {"hospital_id": hosp["hospital_id"]},
                {"$set": hosp},
                upsert=True
            )
        print(f"[OK] {len(SAMPLE_HOSPITALS)} Hospitals seeded.")

        # 7. Seed Notifications
        print(f"Seeding {len(SAMPLE_NOTIFICATIONS)} Notifications...")
        for notif in SAMPLE_NOTIFICATIONS:
            await db.notifications.update_one(
                {"notification_id": notif["notification_id"]},
                {"$set": notif},
                upsert=True
            )
        print(f"[OK] {len(SAMPLE_NOTIFICATIONS)} Notifications seeded.")

        # 8. Seed Users
        print(f"Seeding {len(SAMPLE_USERS)} Users...")
        for user in SAMPLE_USERS:
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": user},
                upsert=True
            )
        print(f"[OK] {len(SAMPLE_USERS)} Users seeded.")

        # 9. Seed Initial Analytics Snapshot
        print("Generating initial Analytics snapshot...")
        total_inc = await db.incidents.count_documents({})
        active_inc = await db.incidents.count_documents({"status": {"$in": ["REPORTED", "VERIFIED", "DISPATCHED", "IN_PROGRESS"]}})
        resolved_inc = await db.incidents.count_documents({"status": {"$in": ["RESOLVED", "CLOSED"]}})
        crit_inc = await db.incidents.count_documents({"severity": "CRITICAL"})
        avail_res = await db.resources.count_documents({"status": "AVAILABLE"})
        busy_res = await db.resources.count_documents({"status": {"$in": ["BUSY", "EN_ROUTE"]}})

        await db.analytics.insert_one({
            "timestamp": datetime.utcnow(),
            "total_incidents": total_inc,
            "active_incidents": active_inc,
            "resolved_incidents": resolved_inc,
            "critical_incidents": crit_inc,
            "resources_available": avail_res,
            "resources_busy": busy_res
        })
        print("[OK] Analytics snapshot recorded.")

        print("\n" + "=" * 70)
        print(" ResQAI MongoDB Database Seeding Completed Successfully!")
        print("=" * 70)
        print(f" Collections Seeded:")
        print(f"  * incidents:        {total_inc} documents")
        print(f"  * resources:        {await db.resources.count_documents({})} documents")
        print(f"  * teams:            {await db.teams.count_documents({})} documents")
        print(f"  * hospitals:        {await db.hospitals.count_documents({})} documents")
        print(f"  * notifications:    {await db.notifications.count_documents({})} documents")
        print(f"  * users:            {await db.users.count_documents({})} documents")
        print(f"  * analytics:        {await db.analytics.count_documents({})} documents")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Error during MongoDB seeding: {e}")
        print("Please check that MongoDB is running or MONGODB_URI is correctly configured in .env")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
