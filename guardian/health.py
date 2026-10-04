"""Small, explainable health assessment rules for the MVP."""

from __future__ import annotations

from statistics import mean

from guardian.data import Area, HealthAssessment, Reading
from guardian.weather import WeatherReading


def _values(readings: list[Reading], field: str) -> list[float]:
    return [value for reading in readings if (value := getattr(reading, field)) is not None]


def assess_area(area: Area, weather: WeatherReading | None = None) -> HealthAssessment:
    readings = area.readings
    latest = readings[-1] if readings else None
    score = 100
    reasons: list[str] = []
    trend = "stable"

    if area.latest_mould_index is not None:
        if area.latest_mould_index >= 1:
            score -= 40
            reasons.append("Mould index is elevated")
        elif area.latest_mould_index >= 0.5:
            score -= 20
            reasons.append("Mould index is approaching an elevated level")

    if latest is not None:
        humidity_context = latest.outdoor_relative_humidity_pct
        context_source = "outdoor sensor"
        if humidity_context is None and weather is not None:
            humidity_context = weather.relative_humidity_pct
            context_source = "local weather"
        humidity_is_contextually_high = humidity_context is not None and humidity_context >= 90
        humidity_penalty = 5 if humidity_is_contextually_high else 0
        if latest.indoor_relative_humidity_pct is not None:
            if latest.indoor_relative_humidity_pct >= 98:
                score -= 20 - humidity_penalty
                reasons.append(
                    "Indoor humidity is very high"
                    + (f"; {context_source} is also humid" if humidity_penalty else "")
                )
            elif latest.indoor_relative_humidity_pct >= 90:
                score -= 10 - humidity_penalty
                reasons.append(
                    "Indoor humidity is high"
                    + (f"; {context_source} is also humid" if humidity_penalty else "")
                )

        if (
            latest.indoor_relative_humidity_pct is not None
            and latest.outdoor_relative_humidity_pct is not None
            and latest.indoor_relative_humidity_pct - latest.outdoor_relative_humidity_pct >= 10
        ):
            score -= 10
            reasons.append("Indoor humidity is higher than outdoor humidity")

        if (
            latest.indoor_absolute_humidity_g_m3 is not None
            and latest.outdoor_absolute_humidity_g_m3 is not None
        ):
            absolute_difference = (
                latest.indoor_absolute_humidity_g_m3 - latest.outdoor_absolute_humidity_g_m3
            )
            if absolute_difference >= 4:
                score -= 20
                reasons.append("Indoor absolute humidity is substantially higher than outdoors")
            elif absolute_difference >= 2:
                score -= 10
                reasons.append("Indoor absolute humidity is higher than outdoors")

    recent = readings[-6:]
    persistent = [
        reading
        for reading in recent
        if reading.indoor_relative_humidity_pct is not None
        and reading.indoor_relative_humidity_pct >= 90
    ]
    if len(persistent) >= 5:
        score -= 25
        reasons.append("High indoor humidity has persisted")
    elif len(persistent) >= 3:
        score -= 15
        reasons.append("Indoor humidity has been elevated repeatedly")

    if len(readings) >= 6:
        previous = readings[-6:-3]
        current = readings[-3:]
        previous_rh = _values(previous, "indoor_relative_humidity_pct")
        current_rh = _values(current, "indoor_relative_humidity_pct")
        if previous_rh and current_rh:
            delta = mean(current_rh) - mean(previous_rh)
            if delta >= 5:
                score -= 15
                trend = "worsening"
                reasons.append("Indoor humidity is trending upward")
            elif delta >= 2:
                score -= 8
                trend = "worsening"
                reasons.append("Indoor humidity has started trending upward")
            elif delta <= -2:
                trend = "improving"

    fan_rpm = latest.fan_rpm if latest else area.latest_rpm
    if fan_rpm is not None and fan_rpm <= 0 and persistent:
        score -= 15
        reasons.append("Fan speed is zero while humidity is elevated")
    elif fan_rpm is not None and fan_rpm < 500 and persistent:
        score -= 8
        reasons.append("Fan speed is low while humidity is elevated")

    score = max(0, min(100, score))
    if score < 55:
        status = "action_needed"
    elif score < 80:
        status = "attention"
    else:
        status = "healthy"
    return HealthAssessment(status=status, score=score, reasons=reasons[:5], trend=trend)
