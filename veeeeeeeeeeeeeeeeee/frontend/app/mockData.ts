import { Incident, Resource, Alert } from './types';

export const INITIAL_RESOURCES: Resource[] = [
  // Fire Engines
  {
    id: 'res-fire-1',
    name: 'Navrangpura Fire Engine 1',
    kind: 'fire_truck',
    status: 'available',
    lat: 23.0365,
    lng: 72.5610,
    capacity: 6,
    capabilities: ['fire', 'industrial'],
    station: 'Navrangpura Fire Station',
    updated_at: new Date().toISOString()
  },
  {
    id: 'res-fire-2',
    name: 'Danapith Central Water Tender 2',
    kind: 'fire_truck',
    status: 'dispatched',
    lat: 23.0245,
    lng: 72.5875,
    capacity: 8,
    capabilities: ['fire', 'industrial', 'collapse'],
    station: 'Danapith Central Fire Station',
    updated_at: new Date().toISOString()
  },
  {
    id: 'res-fire-3',
    name: 'Naroda GIDC Chemical Foam Tender',
    kind: 'fire_truck',
    status: 'available',
    lat: 23.0720,
    lng: 72.6640,
    capacity: 6,
    capabilities: ['fire', 'industrial'],
    station: 'Naroda GIDC Fire Station',
    updated_at: new Date().toISOString()
  },
  {
    id: 'res-hazmat-1',
    name: 'Vatva GIDC HAZMAT Decon Unit 1',
    kind: 'hazmat_unit',
    status: 'available',
    lat: 22.9610,
    lng: 72.6240,
    capacity: 4,
    capabilities: ['industrial'],
    station: 'Vatva Hazmat Depot',
    updated_at: new Date().toISOString()
  },

  // Ambulances (108 Emergency Network)
  {
    id: 'res-amb-1',
    name: '108 ALS Ambulance - Civil Hospital',
    kind: 'ambulance',
    status: 'available',
    lat: 23.0530,
    lng: 72.5910,
    capacity: 3,
    capabilities: ['medical', 'accident', 'fire'],
    station: 'Ahmedabad Civil Hospital',
    updated_at: new Date().toISOString()
  },
  {
    id: 'res-amb-2',
    name: '108 ALS Ambulance - SVP Hospital',
    kind: 'ambulance',
    status: 'dispatched',
    lat: 23.0180,
    lng: 72.5690,
    capacity: 3,
    capabilities: ['medical', 'accident', 'collapse'],
    station: 'SVP Hospital Ellisbridge',
    updated_at: new Date().toISOString()
  },
  {
    id: 'res-amb-3',
    name: '108 Trauma Unit - Sola Civil',
    kind: 'ambulance',
    status: 'available',
    lat: 23.0750,
    lng: 72.5270,
    capacity: 4,
    capabilities: ['medical', 'accident'],
    station: 'Sola Civil Hospital',
    updated_at: new Date().toISOString()
  },

  // Police PCR Vans
  {
    id: 'res-pol-1',
    name: 'PCR Interceptor Van 04 - SG Highway',
    kind: 'police_van',
    status: 'available',
    lat: 23.0410,
    lng: 72.5180,
    capacity: 4,
    capabilities: ['accident', 'industrial', 'other'],
    station: 'Vastrapur Police Station',
    updated_at: new Date().toISOString()
  },
  {
    id: 'res-pol-2',
    name: 'PCR Rapid Patrol 12 - Kalupur',
    kind: 'police_van',
    status: 'available',
    lat: 23.0300,
    lng: 72.5990,
    capacity: 4,
    capabilities: ['accident', 'collapse'],
    station: 'Kalupur Station Command',
    updated_at: new Date().toISOString()
  },

  // NDRF & Rescue Boats
  {
    id: 'res-ndrf-1',
    name: '6th Battalion NDRF Heavy Rescue Unit',
    kind: 'ndrf_team',
    status: 'available',
    lat: 23.2150,
    lng: 72.6360,
    capacity: 12,
    capabilities: ['flood', 'collapse', 'industrial'],
    station: 'Gandhinagar NDRF Base',
    updated_at: new Date().toISOString()
  },
  {
    id: 'res-boat-1',
    name: 'Sabarmati Riverfront Rescue Boat 01',
    kind: 'rescue_boat',
    status: 'available',
    lat: 23.0380,
    lng: 72.5780,
    capacity: 8,
    capabilities: ['flood'],
    station: 'Riverfront Rescue Station',
    updated_at: new Date().toISOString()
  },

  // Drones
  {
    id: 'res-drone-1',
    name: 'ResQ-Recon Thermal Drone Alpha',
    kind: 'drone',
    status: 'available',
    lat: 23.0320,
    lng: 72.5590,
    capacity: 1,
    capabilities: ['fire', 'flood', 'industrial', 'collapse'],
    station: 'Command HQ Helipad',
    updated_at: new Date().toISOString()
  }
];

export const INITIAL_INCIDENTS: Incident[] = [
  {
    id: 'inc-001',
    title: 'Major Chemical Storage Tanker Fire & Gas Leak',
    description: 'Chlorine gas cylinder ruptured following a collision at Odhav Industrial Estate. Dense toxic white smoke spreading near residential pockets. Multiple factory workers reporting breathing distress.',
    type: 'industrial',
    severity: 'critical',
    priority: 100,
    status: 'dispatched',
    lat: 23.0280,
    lng: 72.6510,
    address: 'Phase 3, Odhav GIDC Industrial Estate, Ahmedabad',
    source: 'hotline',
    report_count: 5,
    reports: [
      {
        id: 'rep-1',
        source: 'hotline',
        reporter: 'Control Room Operator #41',
        raw_text: 'Chemical leak reported near Odhav GIDC phase 3. Strong chlorine smell, workers collapsing.',
        lat: 23.0280,
        lng: 72.6510,
        reported_at: new Date(Date.now() - 1800000).toISOString()
      },
      {
        id: 'rep-2',
        source: 'citizen',
        reporter: 'Ramesh Patel',
        raw_text: 'Thick smoke coming out of chemical factory near Odhav circle! Send fire engines immediately.',
        lat: 23.0282,
        lng: 72.6515,
        reported_at: new Date(Date.now() - 1650000).toISOString()
      },
      {
        id: 'rep-3',
        source: 'iot_sensor',
        reporter: 'IoT Hazmat Sensor #ODH-409',
        raw_text: 'ALERT: Chlorine concentration > 45 ppm detected at sensor ODH-409.',
        lat: 23.0278,
        lng: 72.6508,
        reported_at: new Date(Date.now() - 1500000).toISOString()
      }
    ],
    ai_confidence: 0.96,
    ai_reasoning: 'Extracted high risk of hazardous chemical cloud spread, structural fire, and 10+ potential casualties. Classified as Critical Industrial HAZMAT event requiring foam tender + decon unit + 108 ALS.',
    classified_by: 'ai',
    created_at: new Date(Date.now() - 1800000).toISOString(),
    updated_at: new Date(Date.now() - 600000).toISOString(),
    assignments: [
      {
        id: 'asgn-1',
        incident_id: 'inc-001',
        resource_id: 'res-fire-2',
        resource_name: 'Danapith Central Water Tender 2',
        resource_kind: 'fire_truck',
        status: 'en_route',
        score: 94.2,
        distance_km: 6.4,
        eta_min: 11,
        assigned_at: new Date(Date.now() - 1200000).toISOString()
      },
      {
        id: 'asgn-2',
        incident_id: 'inc-001',
        resource_id: 'res-amb-2',
        resource_name: '108 ALS Ambulance - SVP Hospital',
        resource_kind: 'ambulance',
        status: 'en_route',
        score: 91.0,
        distance_km: 8.8,
        eta_min: 15,
        assigned_at: new Date(Date.now() - 1100000).toISOString()
      }
    ]
  },
  {
    id: 'inc-002',
    title: 'Multi-Vehicle Highway Pileup on SG Highway',
    description: '3 car collision involving a passenger bus near Iskcon Flyover. 2 vehicles overturned, traffic gridlocked. 4 injured passengers trapped inside vehicle.',
    type: 'accident',
    severity: 'high',
    priority: 85,
    status: 'open',
    lat: 23.0260,
    lng: 72.5070,
    address: 'SG Highway, Near Iskcon Flyover, Vastrapur',
    source: 'citizen',
    report_count: 3,
    reports: [
      {
        id: 'rep-10',
        source: 'citizen',
        reporter: 'Anuj Sharma',
        raw_text: 'Big crash on SG Highway near Iskcon flyover. Bus hit cars. People trapped.',
        lat: 23.0260,
        lng: 72.5070,
        reported_at: new Date(Date.now() - 900000).toISOString()
      }
    ],
    ai_confidence: 0.92,
    ai_reasoning: 'Extracted high priority vehicular accident with trapped victims. Requires PCR highway patrol for traffic diversion and hydraulic cutter equipped response unit + ambulance.',
    classified_by: 'ai',
    created_at: new Date(Date.now() - 900000).toISOString(),
    updated_at: new Date(Date.now() - 900000).toISOString(),
    assignments: []
  },
  {
    id: 'inc-003',
    title: 'Commercial Building Electrical Short-Circuit Fire',
    description: 'Electrical transformer caught fire in 4th floor duct of CG Road commercial complex. Heavy smoke trapped 15 office employees on terrace.',
    type: 'fire',
    severity: 'high',
    priority: 80,
    status: 'open',
    lat: 23.0340,
    lng: 72.5570,
    address: 'CG Road, Opp Municipal Market, Navrangpura',
    source: 'citizen',
    report_count: 4,
    reports: [
      {
        id: 'rep-20',
        source: 'citizen',
        reporter: 'Pooja Mehta',
        raw_text: 'Fire broken out in our building on CG Road! Smoke everywhere in stairwell, people on roof!',
        lat: 23.0340,
        lng: 72.5570,
        reported_at: new Date(Date.now() - 600000).toISOString()
      }
    ],
    ai_confidence: 0.94,
    ai_reasoning: 'Commercial fire with rooftop trapped victims. High priority dispatch of aerial ladder turntable fire engine + emergency medical response.',
    classified_by: 'ai',
    created_at: new Date(Date.now() - 600000).toISOString(),
    updated_at: new Date(Date.now() - 600000).toISOString(),
    assignments: []
  },
  {
    id: 'inc-004',
    title: 'Sabarmati Riverfront Flash Surge & Waterlogging',
    description: 'Heavy upstream release from Dharoi dam caused sudden water level rise near Subhash Bridge. 3 construction workers stranded on low-lying mud bank.',
    type: 'flood',
    severity: 'medium',
    priority: 65,
    status: 'open',
    lat: 23.0600,
    lng: 72.5800,
    address: 'Near Subhash Bridge Riverfront Bank, Ahmedabad',
    source: 'field_officer',
    report_count: 2,
    reports: [
      {
        id: 'rep-30',
        source: 'field_officer',
        reporter: 'Officer K. Jadeja',
        raw_text: 'Sabarmati water level rising fast near Subhash bridge. 3 workers stuck on mudbank.',
        lat: 23.0600,
        lng: 72.5800,
        reported_at: new Date(Date.now() - 1200000).toISOString()
      }
    ],
    ai_confidence: 0.88,
    ai_reasoning: 'Water rescue required. Recommended dispatch of Sabarmati Rescue Boat 01 or NDRF water safety team.',
    classified_by: 'ai',
    created_at: new Date(Date.now() - 1200000).toISOString(),
    updated_at: new Date(Date.now() - 1200000).toISOString(),
    assignments: []
  },
  {
    id: 'inc-005',
    title: 'Old City Wall Collapse Hazard',
    description: 'Part of old masonry wall cracked and partially collapsed after morning rains near Bhadra Fort. Pedestrian walkway blocked.',
    type: 'collapse',
    severity: 'medium',
    priority: 55,
    status: 'open',
    lat: 23.0240,
    lng: 72.5810,
    address: 'Bhadra Fort Precinct, Old City, Ahmedabad',
    source: 'citizen',
    report_count: 1,
    reports: [
      {
        id: 'rep-40',
        source: 'citizen',
        reporter: 'Suresh Varma',
        raw_text: 'Old structure wall fell down near Bhadra. Road blocked, no major injury visible.',
        lat: 23.0240,
        lng: 72.5810,
        reported_at: new Date(Date.now() - 2400000).toISOString()
      }
    ],
    ai_confidence: 0.85,
    ai_reasoning: 'Structural hazard without acute mass casualties. Moderate priority for municipal rescue squad and traffic cordon.',
    classified_by: 'ai',
    created_at: new Date(Date.now() - 2400000).toISOString(),
    updated_at: new Date(Date.now() - 2400000).toISOString(),
    assignments: []
  }
];

export const INITIAL_ALERTS: Alert[] = [
  {
    id: 'alt-001',
    type: 'delayed_response',
    level: 'critical',
    title: 'Critical Incident Unassigned > 10m',
    description: 'Multi-Vehicle Highway Pileup on SG Highway (inc-002) has high priority (85) but no unit assigned for 15 minutes!',
    incident_id: 'inc-002',
    created_at: new Date(Date.now() - 300000).toISOString(),
    resolved: false
  },
  {
    id: 'alt-002',
    type: 'resource_shortage',
    level: 'warning',
    title: 'HAZMAT Unit Availability Low',
    description: 'Only 1 active HAZMAT decon unit remaining in Vatva sector. High industrial threat grid load.',
    created_at: new Date(Date.now() - 900000).toISOString(),
    resolved: false
  }
];
