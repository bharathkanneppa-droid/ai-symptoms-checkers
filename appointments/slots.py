"""Appointment time-slot generation respecting doctor availability."""
from datetime import datetime, time, timedelta

DEFAULT_START = time(9, 0)
DEFAULT_END = time(17, 0)
SLOT_MINUTES = 60


def _to_time(value):
    """Parse 'HH:MM' (or 'HH:MM:SS') into a time object."""
    parts = value.split(":")
    return time(int(parts[0]), int(parts[1]))


def doctor_window(doctor, weekday):
    """Return (start, end, available) for a doctor on the given weekday."""
    for entry in doctor.availabilities:
        if entry.day_of_week == weekday:
            return _to_time(entry.start_time), _to_time(entry.end_time), entry.is_available
    return DEFAULT_START, DEFAULT_END, True


def generate_slots(doctor, appointment_date, booked_times):
    """Generate available 'HH:MM' slots for one day.

    Args:
        doctor: Doctor ORM instance.
        appointment_date: datetime.date.
        booked_times: iterable of already-booked 'HH:MM' strings.
    Returns:
        list of 'HH:MM' strings.
    """
    start, end, available = doctor_window(doctor, appointment_date.weekday())
    if not available:
        return []

    booked = set(booked_times)
    slots = []
    cursor = datetime.combine(appointment_date, start)
    end_dt = datetime.combine(appointment_date, end)
    now = datetime.now()

    while cursor < end_dt:
        if cursor > now:  # don't offer slots in the past
            label = cursor.strftime("%H:%M")
            if label not in booked:
                slots.append(label)
        cursor += timedelta(minutes=SLOT_MINUTES)
    return slots
