from datetime import datetime, timedelta

from guardian.data import Area, Reading
from guardian.health import assess_area


def test_health_assessment_explains_persistent_humidity_and_low_fan() -> None:
    start = datetime(2026, 1, 1)
    readings = [
        Reading(
            timestamp=start + timedelta(hours=index),
            indoor_temperature_c=10,
            indoor_relative_humidity_pct=95 + index,
            indoor_absolute_humidity_g_m3=12,
            outdoor_temperature_c=5,
            outdoor_relative_humidity_pct=80,
            outdoor_absolute_humidity_g_m3=8,
            fan_rpm=0,
        )
        for index in range(6)
    ]
    area = Area(id="roof", name="Roof", kind="roof", readings=readings, latest_mould_index=1.2)

    result = assess_area(area)

    assert result.status == "action_needed"
    assert result.score < 55
    assert "Mould index is elevated" in result.reasons
    assert "High indoor humidity has persisted" in result.reasons
    assert result.trend == "worsening"
