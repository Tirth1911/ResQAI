import pytest
from bson import ObjectId
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db import serialize_doc, to_geojson, from_geojson


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["db"] in ("up", "down")


def test_to_and_from_geojson():
    lat, lng = 23.0225, 72.5714
    geojson = to_geojson(lat, lng)
    assert geojson == {
        "type": "Point",
        "coordinates": [72.5714, 23.0225],
    }

    extracted = from_geojson(geojson)
    assert extracted["lat"] == lat
    assert extracted["lng"] == lng

    # Test extracting from document containing location field
    doc = {"location": geojson}
    extracted_from_doc = from_geojson(doc)
    assert extracted_from_doc["lat"] == lat
    assert extracted_from_doc["lng"] == lng


def test_serialize_doc():
    raw_id = ObjectId()
    nested_id = ObjectId()
    now = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)

    raw_doc = {
        "_id": raw_id,
        "title": "Industrial Fire",
        "nested": {
            "ref_id": nested_id,
        },
        "tags": ["urgent", nested_id],
        "created_at": now,
        "location": {
            "type": "Point",
            "coordinates": [72.5714, 23.0225],
        },
    }

    serialized = serialize_doc(raw_doc)

    assert "_id" not in serialized
    assert serialized["id"] == str(raw_id)
    assert serialized["nested"]["ref_id"] == str(nested_id)
    assert serialized["tags"][1] == str(nested_id)
    assert serialized["created_at"] == "2026-09-19T12:00:00+00:00"
    assert serialized["lat"] == 23.0225
    assert serialized["lng"] == 72.5714
