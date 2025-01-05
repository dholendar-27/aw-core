import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pytz
from sd_core.models import Event
from tzlocal import get_localzone

logger = logging.getLogger(__name__)


def heartbeat_reduce(events: List[Event], pulsetime: float) -> List[Event]:
    """
     Heartbeats are merged with the last event. This is a wrapper around heartbeat_merge that does not check for duplicates

     @param events - List of events to reduce
     @param pulsetime - Time in seconds to use for merge

     @return A list of events that were merged with the last event in the list and have the same pulset
    """
    reduced = []
    # Add the last event to the reduced list.
    if events:
        reduced.append(events.pop(0))
    # Merge heartbeat events with the same heartbeat.
    for heartbeat in events:
        merged = heartbeat_merge(reduced[-1], heartbeat, pulsetime)
        # Add a heartbeat to the reduced list of heartbeat.
        if merged is not None:
            # Heartbeat was merged
            reduced[-1] = merged
        else:
            # Heartbeat was not merged
            reduced.append(heartbeat)
    return reduced


def get_server_timezone():
    return get_localzone()  # Automatically fetch the local time zone

# Helper function to convert UTC time to the user's local time
def convert_to_user_timezone(utc_timestamp: datetime, user_timezone: pytz.timezone) -> datetime:
    return utc_timestamp.astimezone(user_timezone)

# Heartbeat merge function
def heartbeat_merge(
    last_event: Event, heartbeat: Event, pulsetime: float
) -> Optional[Event]:
    """
    Merge two heartbeats into a single event using the server's or user's time zone.
    The time zone is automatically detected.

    @param last_event - The event that was the last heartbeat
    @param heartbeat - The event that we want to merge
    @param pulsetime - The pulse time in seconds for the heartbeat
    @return The merged event or None if there was no merge to be done.
    """
    # Get the time zone (this could be dynamically set based on the user or system)
    user_timezone = get_server_timezone()  # Automatically detect the server's time zone

    # Convert timestamps from UTC to the local time zone
    last_event_utc = last_event.timestamp.astimezone(pytz.utc)
    heartbeat_utc = heartbeat.timestamp.astimezone(pytz.utc)

    # Now, we continue with the merge logic in the user's local time zone
    if last_event.data == heartbeat.data:
        pulseperiod_end = (
            last_event_utc + last_event.duration + timedelta(seconds=pulsetime)
        )

        within_pulsetime_window = (
            last_event_utc <= heartbeat_utc <= pulseperiod_end
        )

        if within_pulsetime_window:
            new_duration = (
                heartbeat_utc - last_event_utc
            ) + heartbeat.duration

            if new_duration < timedelta(0):
                logger.warning("Merging heartbeats would result in a negative duration, refusing to merge.")
                return last_event

            # Take the maximum of the last event's duration and the new duration
            last_event.duration = max(last_event.duration, new_duration)
            return last_event

    return None
