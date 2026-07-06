"""
Sport settings MCP tools for Intervals.icu.

This module contains tools for reading and updating an athlete's per-sport
settings (FTP, LTHR, max HR, power/HR zones, etc.). The Intervals.icu
SportSettings schema is fairly large and can vary by sport, so writes are
passed through as a raw JSON object rather than mapped to individual named
arguments. Callers should fetch the current settings first (get_sport_setting)
to see the exact field names/shape for that sport, then submit a settings
dict containing only the fields they want to change.
"""

import json
from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.validation import resolve_athlete_id

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


@mcp.tool()
async def get_sport_settings(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get all per-sport settings (FTP, LTHR, max HR, zones, etc.) for an athlete.

    Returns the raw settings for every sport type (Ride, Run, Swim, ...)
    configured for the athlete. Use this to see current values and exact
    field names before calling update_sport_settings.

    Args:
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings", api_key=api_key
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error fetching sport settings: {result.get('message')}"

    if not result:
        return f"No sport settings found for athlete {athlete_id_to_use}."

    return f"Sport settings for athlete {athlete_id_to_use}:\n\n{json.dumps(result, indent=2)}"


@mcp.tool()
async def get_sport_setting(
    type_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get settings for a single sport (e.g. Ride, Run, Swim) for an athlete.

    Args:
        type_id: Sport type (e.g. "Ride", "Run", "Swim") or numeric sport settings id
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg
    if not type_id:
        return "Error: No sport type_id provided."

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings/{type_id}", api_key=api_key
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error fetching sport settings: {result.get('message')}"

    if not result:
        return f"No sport settings found for athlete {athlete_id_to_use}, sport {type_id}."

    return f"Sport settings for athlete {athlete_id_to_use}, sport {type_id}:\n\n{json.dumps(result, indent=2)}"


@mcp.tool()
async def update_sport_settings(
    type_id: str,
    settings: dict[str, Any],
    athlete_id: str | None = None,
    api_key: str | None = None,
    recalc_hr_zones: bool = False,
) -> str:
    """Update settings for a single sport (e.g. FTP, LTHR, max HR, power/HR zones).

    This is a thin, direct wrapper around the Intervals.icu API and does not
    validate the shape of `settings` beyond it being a JSON object: pass only
    the fields you want to change, using the same field names returned by
    get_sport_setting for this sport (e.g. "ftp", "lthr", "max_hr",
    "indoor_ftp"). Changing FTP/zones affects how Intervals.icu scores past
    and future training load, so call get_sport_setting first to confirm the
    current values and field names.

    Args:
        type_id: Sport type (e.g. "Ride", "Run", "Swim") or numeric sport settings id
        settings: Object with the sport settings fields to update
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
        recalc_hr_zones: If True, ask Intervals.icu to recalculate HR zones from the new LTHR/max HR (default False)
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg
    if not type_id:
        return "Error: No sport type_id provided."
    if not settings:
        return "Error: No settings provided to update."

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings/{type_id}",
        api_key=api_key,
        method="PUT",
        params={"recalcHrZones": str(recalc_hr_zones).lower()},
        data=settings,
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error updating sport settings: {result.get('message')}"

    return f"Successfully updated {type_id} sport settings for athlete {athlete_id_to_use}:\n\n{json.dumps(result, indent=2)}"
