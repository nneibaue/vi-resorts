"""
VI Resorts data models using Pydantic for validation.

This module defines the core data structures for the VI Resorts Concierge system:
- Resorts and their properties
- Bookings and trips
- Points and their usage
- Costs and financial tracking
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PointType(str, Enum):
    """Types of points in the VI system."""
    ANNUAL = "annual"
    BONUS = "bonus"
    SAVED = "saved"
    BORROWED = "borrowed"


class UnitType(str, Enum):
    """Types of accommodation units."""
    STUDIO = "studio"
    ONE_BEDROOM = "one_bedroom"
    TWO_BEDROOM = "two_bedroom"
    THREE_BEDROOM = "three_bedroom"


class Season(str, Enum):
    """Resort seasons affecting point costs."""
    PEAK = "peak"
    HIGH = "high"
    REGULAR = "regular"
    LOW = "low"


class CostCategory(str, Enum):
    """Categories of costs for accounting."""
    ANNUAL_FEE = "annual_fee"
    BOOKING_FEE = "booking_fee"
    GUEST_CERTIFICATE = "guest_certificate"
    UPGRADE_FEE = "upgrade_fee"
    LATE_FEE = "late_fee"
    TRAVEL = "travel"
    MEALS = "meals"
    ACTIVITIES = "activities"
    INCIDENTALS = "incidentals"
    OTHER = "other"


class Resort(BaseModel):
    """A VI Resort property."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    location: str
    country: str = "USA"
    description: Optional[str] = None
    amenities: list[str] = Field(default_factory=list)
    
    # Point costs by unit type and season
    point_costs: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Map of unit_type -> season -> points per night"
    )


class PointBalance(BaseModel):
    """Current point balance and tracking."""
    id: UUID = Field(default_factory=uuid4)
    year: int
    point_type: PointType
    total_points: int
    used_points: int = 0
    expiration_date: Optional[date] = None
    
    @property
    def available_points(self) -> int:
        """Calculate available points."""
        return self.total_points - self.used_points
    
    def use_points(self, points: int) -> None:
        """Use points from this balance."""
        if points > self.available_points:
            raise ValueError(f"Insufficient points: {self.available_points} available, {points} requested")
        self.used_points += points


class Cost(BaseModel):
    """A cost entry in the accounting ledger."""
    id: UUID = Field(default_factory=uuid4)
    date: date
    category: CostCategory
    amount: Decimal = Field(ge=0)
    description: str
    trip_id: Optional[UUID] = None
    booking_id: Optional[UUID] = None
    
    @field_validator('amount', mode='before')
    @classmethod
    def validate_amount(cls, v: any) -> Decimal:
        """Ensure amount is a Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v


class Booking(BaseModel):
    """A resort booking."""
    id: UUID = Field(default_factory=uuid4)
    resort_id: UUID
    check_in: date
    check_out: date
    unit_type: UnitType
    season: Season
    points_used: int
    point_balance_ids: list[UUID] = Field(
        default_factory=list,
        description="Point balances used for this booking"
    )
    guest_name: Optional[str] = None
    confirmation_number: Optional[str] = None
    notes: Optional[str] = None
    
    @property
    def nights(self) -> int:
        """Calculate number of nights."""
        return (self.check_out - self.check_in).days
    
    @property
    def points_per_night(self) -> float:
        """Calculate points per night."""
        if self.nights == 0:
            return 0.0
        return self.points_used / self.nights


class Trip(BaseModel):
    """A vacation trip that may include multiple bookings."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    start_date: date
    end_date: date
    bookings: list[UUID] = Field(default_factory=list)
    travelers: int = 1
    notes: Optional[str] = None
    
    @property
    def duration(self) -> int:
        """Calculate trip duration in days."""
        return (self.end_date - self.start_date).days


class LedgerEntry(BaseModel):
    """A complete ledger entry for audit purposes."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    entry_type: str  # "cost", "booking", "point_allocation"
    data: dict  # Stores the actual entry data
    description: str
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
            UUID: lambda v: str(v),
        }
    }


class OwnershipRules(BaseModel):
    """Rules and assumptions for VI ownership."""
    annual_points: int = Field(gt=0, description="Base annual points allocation")
    annual_fee: Decimal = Field(gt=0, description="Annual maintenance fee")
    booking_fee: Decimal = Field(ge=0, description="Fee per booking")
    guest_certificate_fee: Decimal = Field(ge=0, description="Fee for guest certificates")
    points_expire_months: int = Field(default=12, description="Months until points expire")
    can_save_points: bool = Field(default=True, description="Can save unused points")
    can_borrow_points: bool = Field(default=True, description="Can borrow future points")
    max_saved_points: Optional[int] = Field(default=None, description="Maximum points that can be saved")
    booking_window_days: int = Field(default=365, description="How far in advance you can book")
