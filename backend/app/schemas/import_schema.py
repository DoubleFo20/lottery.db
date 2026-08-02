from pydantic import BaseModel, Field
from datetime import date

class ImportRow(BaseModel):
    draw_date: date
    government_round: str | None = None
    first_prize: str
    last_two: str | None = None
    front_three: str | None = None
    back_three: str | None = None
