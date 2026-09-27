from datetime import date
from enum import Enum
from pydantic import BaseModel, Field

class TripRequest(BaseModel):
    origin: str
    destination: str
    start_date: str
    end_date: str
    travelers: int
    budget: float | None = None
    interests: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

class TripStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    COMPLETE = "COMPLETE"

class TripState(BaseModel):
    trip_id: str
    status: TripStatus = TripStatus.CREATED
    request: TripRequest       
