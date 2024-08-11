from datetime import datetime, timedelta


class Slot:
    def __init__(self, date: str, slot_id: int, ch_time: str):
        self.id = slot_id
        self.ch_date = date
        self.ch_time = ch_time

    def __repr__(self):
        return f"Slot(id={self.id}, date='{self.ch_date}' chtime='{self.ch_time}')"


class SlotReservation:
    def __init__(self, reserved_at: datetime, reservation_url: str, slot: Slot):
        self.reservation_url = reservation_url
        self.expired_at = reserved_at + timedelta(minutes=1, seconds=15)
        self.slot = slot

    def __repr__(self):
        return f"SlotReservation(location='{self.reservation_url}' expired_at='{self.expired_at}' slot='{self.slot.__repr__()}')"
