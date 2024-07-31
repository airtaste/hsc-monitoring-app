class Slot:
    def __init__(self, date: str, slot_id: int, ch_time: str):
        self.id = slot_id
        self.ch_date = date
        self.ch_time = ch_time

    def __repr__(self):
        return f"Slot(id={self.id}, date='{self.ch_date}' chtime='{self.ch_time}')"
