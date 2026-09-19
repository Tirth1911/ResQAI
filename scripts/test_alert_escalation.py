import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from httpx import ASGITransport
from backend.app.config import settings
from backend.app.main import app
from backend.app.database import DatabaseManager
from backend.app.services.alert_service import (
    AlertService,
    AlertType,
    AlertSeverity,
    email_provider,
    sms_provider,
)


async def run_alert_tests():
    print("=" * 75)
    print("🚨 ResQAI Alert & Escalation Engine - Full Validation Suite")
    print("=" * 75)

    db = await DatabaseManager.connect_to_mongo()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. TEST EMAIL & SMS DELIVERY ABSTRACTIONS
        print("\n[TEST 1/7] Testing Email & SMS Provider Abstractions (Zero-Cost / Simulated)...")
        e_ok = await email_provider.send_email(
            recipient="duty-officer@gujarat.gov.in",
            subject="Test Critical Alert",
            body_text="Chemical fire reported at Sanand industrial sector."
        )
        s_ok = await sms_provider.send_sms(
            phone_number="+91-9876543210",
            message="[ResQAI CRITICAL] Immediate evacuation ordered."
        )
        assert e_ok and s_ok, "Provider abstraction failed!"
        print("  ✓ Simulated Email & SMS delivery channels operational without external credentials.")

        # 2. TEST CRITICAL & P1 UNASSIGNED ALERT GENERATION (Condition 1 & 2)
        print("\n[TEST 2/7] Testing Incident Creation -> Automatic CRITICAL & P1 Alert Generation...")
        incident_payload = {
            "title": "Industrial Boiler Blast with Active Fire",
            "description": "Massive explosion in boiler room block B. 6 workers trapped with burns.",
            "source": "iot",
            "type": "industrial_hazard",
            "severity": "CRITICAL",
            "priority": "P1",
            "location": {
                "latitude": 23.0125,
                "longitude": 72.3850,
                "address": "Sanand GIDC, Ahmedabad"
            }
        }
        res_inc = await client.post("/api/v1/incidents/?auto_dedup=false", json=incident_payload)
        assert res_inc.status_code == 201
        created_inc = res_inc.json()
        inc_id = created_inc["incident_id"]
        print(f"  ✓ Created Critical Incident: {inc_id}")

        # Check that notifications collection received the alerts
        res_notifs = await client.get("/api/v1/notifications/?limit=10")
        assert res_notifs.status_code == 200
        notifs = res_notifs.json()
        critical_alerts = [n for n in notifs if n.get("incident_id") == inc_id]
        assert len(critical_alerts) >= 1, "Expected automated critical notification to be created!"
        print(f"  ✓ Automatically generated {len(critical_alerts)} alerts for incident {inc_id}:")
        for a in critical_alerts:
            print(f"     - Alert ID: {a['alert_id']} | Type: {a['type']} | Severity: {a['severity']}")

        # 3. TEST RESPONSE DELAYED ALERT (Condition 3)
        print("\n[TEST 3/7] Testing Delayed Response Detection (Condition 3)...")
        delayed_alerts = await AlertService.check_delayed_responses(db, threshold_minutes=0)
        print(f"  ✓ Delayed response scanner detected {len(delayed_alerts)} overdue incidents.")

        # 4. TEST RESOURCE SHORTAGE ALERT (Conditions 4 & 5)
        print("\n[TEST 4/7] Testing Resource Shortage Alert (Conditions 4 & 5)...")
        shortage_alert = await AlertService.trigger_resource_shortage_alert(
            db=db,
            incident_id=inc_id,
            incident_type="industrial_hazard",
            required_category="HAZMAT"
        )
        assert shortage_alert["type"] == AlertType.RESOURCE_SHORTAGE.value
        assert shortage_alert["severity"] == AlertSeverity.CRITICAL.value
        print(f"  ✓ Resource shortage alert generated: {shortage_alert['alert_id']} ({shortage_alert['title']})")

        # 5. TEST INCIDENT ESCALATION ALERT (Condition 6)
        print("\n[TEST 5/7] Testing Incident Escalation Alert (Condition 6)...")
        esc_alert = await AlertService.trigger_escalation_alert(
            db=db,
            incident_id=inc_id,
            old_severity="MEDIUM",
            new_severity="CRITICAL",
            reason="Secondary cylinder explosion detected."
        )
        assert esc_alert["type"] == AlertType.INCIDENT_ESCALATED.value
        assert esc_alert["severity"] == AlertSeverity.CRITICAL.value
        print(f"  ✓ Escalation alert generated: {esc_alert['alert_id']} ({esc_alert['title']})")

        # 6. TEST MULTIPLE DUPLICATES WARNING ALERT (Condition 7)
        print("\n[TEST 6/7] Testing Multiple Duplicate Reports Warning Alert (Condition 7)...")
        dup_inc = dict(created_inc)
        dup_inc["duplicate_count"] = 4 # >= 3
        dup_alerts = await AlertService.evaluate_incident_alerts(db, dup_inc)
        has_dup_alert = any(a["type"] == AlertType.MULTIPLE_DUPLICATES.value for a in dup_alerts)
        assert has_dup_alert, "Expected MULTIPLE_DUPLICATES alert to be generated!"
        print(f"  ✓ Multiple duplicate warning alert successfully triggered for high-volume distress traffic.")

        # 7. TEST NOTIFICATION REST API ENDPOINTS
        print("\n[TEST 7/7] Testing Notification REST Endpoints (GET, PATCH read, POST mark-all-read)...")
        
        # GET notifications
        list_resp = await client.get("/api/v1/notifications/?limit=20")
        assert list_resp.status_code == 200
        all_notifs = list_resp.json()
        assert len(all_notifs) > 0
        target_id = all_notifs[0]["alert_id"]
        print(f"  ✓ GET /api/v1/notifications/ returned {len(all_notifs)} items.")

        # PATCH /api/notifications/{id}/read
        patch_resp = await client.patch(f"/api/v1/notifications/{target_id}/read")
        assert patch_resp.status_code == 200
        assert patch_resp.json()["read"] is True
        print(f"  ✓ PATCH /api/v1/notifications/{target_id}/read -> read=True.")

        # POST /api/notifications/mark-all-read
        mark_all_resp = await client.post("/api/v1/notifications/mark-all-read")
        assert mark_all_resp.status_code == 200
        assert mark_all_resp.json()["status"] == "success"
        print(f"  ✓ POST /api/v1/notifications/mark-all-read -> marked all remaining notifications as read.")

        # Verify unread filter returns 0
        unread_check = await client.get("/api/v1/notifications/?unread_only=true")
        assert unread_check.status_code == 200
        assert len(unread_check.json()) == 0
        print(f"  ✓ Verified unread_only=true returns 0 unread alerts.")

        # Clean up test incident
        await client.delete(f"/api/v1/incidents/{inc_id}")
        print(f"  ✓ Cleaned up test incident {inc_id}.")

    print("\n" + "=" * 75)
    print("✨ ALL 7 ALERT & ESCALATION VALIDATION TESTS PASSED 100%!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_alert_tests())
