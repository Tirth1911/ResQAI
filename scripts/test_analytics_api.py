import asyncio
import os
import sys

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from httpx import ASGITransport
from backend.app.main import app
from backend.app.database import DatabaseManager


async def run_analytics_tests():
    print("=" * 75)
    print("📊 ResQAI Analytics API & MongoDB Aggregation Validation Suite")
    print("=" * 75)

    await DatabaseManager.connect_to_mongo()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. TEST GET /api/v1/analytics/overview
        print("\n[TEST 1/6] GET /api/v1/analytics/overview...")
        res1 = await client.get("/api/v1/analytics/overview")
        assert res1.status_code == 200, f"Overview failed: {res1.text}"
        data1 = res1.json()

        # Check required fields
        required_fields = [
            "total_incidents",
            "active_incidents",
            "critical_incidents",
            "resolved_incidents",
            "average_response_time",
            "resources_available",
            "resources_busy",
            "resource_utilization",
            "duplicate_reports_merged",
        ]
        for field in required_fields:
            assert field in data1, f"Missing required overview field '{field}' in response: {data1}"

        print("  ✓ Overview Aggregation Returned Expected Schema:")
        print(f"     - Total Incidents:           {data1['total_incidents']}")
        print(f"     - Active Incidents:          {data1['active_incidents']}")
        print(f"     - Critical Incidents:        {data1['critical_incidents']}")
        print(f"     - Resolved Incidents:        {data1['resolved_incidents']}")
        print(f"     - Average Response Time:     {data1['average_response_time']} mins")
        print(f"     - Resources Available:       {data1['resources_available']}")
        print(f"     - Resources Busy:            {data1['resources_busy']}")
        print(f"     - Resource Utilization:      {data1['resource_utilization']}")
        print(f"     - Duplicate Reports Merged:  {data1['duplicate_reports_merged']}")

        # 2. TEST GET /api/v1/analytics/incidents-by-type
        print("\n[TEST 2/6] GET /api/v1/analytics/incidents-by-type...")
        res2 = await client.get("/api/v1/analytics/incidents-by-type")
        assert res2.status_code == 200, f"Incidents by type failed: {res2.text}"
        data2 = res2.json()
        assert "data" in data2 and len(data2["data"]) > 0
        print(f"  ✓ Grouped by Incident Type ({len(data2['data'])} categories):")
        for item in data2["data"][:4]:
            print(f"     - {item['name']}: {item['count']} incidents ({item['percentage']}%)")

        # 3. TEST GET /api/v1/analytics/incidents-by-severity
        print("\n[TEST 3/6] GET /api/v1/analytics/incidents-by-severity...")
        res3 = await client.get("/api/v1/analytics/incidents-by-severity")
        assert res3.status_code == 200, f"Incidents by severity failed: {res3.text}"
        data3 = res3.json()
        assert "data" in data3 and len(data3["data"]) > 0
        print(f"  ✓ Grouped by Severity Level:")
        for item in data3["data"]:
            print(f"     - {item['severity']}: {item['count']} incidents ({item['percentage']}%)")

        # 4. TEST GET /api/v1/analytics/incidents-by-region
        print("\n[TEST 4/6] GET /api/v1/analytics/incidents-by-region...")
        res4 = await client.get("/api/v1/analytics/incidents-by-region")
        assert res4.status_code == 200, f"Incidents by region failed: {res4.text}"
        data4 = res4.json()
        assert "data" in data4 and len(data4["data"]) > 0
        print(f"  ✓ Grouped by Geographical Response Region ({len(data4['data'])} regions):")
        for item in data4["data"]:
            print(f"     - {item['region']}: {item['incident_count']} total ({item['critical_count']} critical, {item['active_count']} active)")

        # 5. TEST GET /api/v1/analytics/response-times
        print("\n[TEST 5/6] GET /api/v1/analytics/response-times...")
        res5 = await client.get("/api/v1/analytics/response-times")
        assert res5.status_code == 200, f"Response times failed: {res5.text}"
        data5 = res5.json()
        assert "by_type" in data5 and "by_severity" in data5
        print(f"  ✓ Response Times & SLA Compliance (Overall Avg: {data5['overall_average_response_time_minutes']}m, SLA: {data5['overall_sla_compliance_rate']}):")
        for item in data5["by_severity"]:
            print(f"     - Severity {item['severity']}: Avg {item['avg_response_time_minutes']}m (SLA Target: {item['target_sla_minutes']}m, Compliance: {item['compliance_rate']}%)")

        # 6. TEST GET /api/v1/analytics/resource-utilization
        print("\n[TEST 6/6] GET /api/v1/analytics/resource-utilization...")
        res6 = await client.get("/api/v1/analytics/resource-utilization")
        assert res6.status_code == 200, f"Resource utilization failed: {res6.text}"
        data6 = res6.json()
        assert "by_category" in data6 and len(data6["by_category"]) > 0
        print(f"  ✓ Fleet Resource Utilization (Overall: {data6['overall_utilization_rate']}):")
        for item in data6["by_category"]:
            print(f"     - {item['name']}: {item['busy_units']}/{item['total_units']} active ({item['utilization_rate']}% utilized)")

    print("\n" + "=" * 75)
    print("✨ ALL 6 ANALYTICS API VALIDATION TESTS PASSED 100%!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_analytics_tests())
