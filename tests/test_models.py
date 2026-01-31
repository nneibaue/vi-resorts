"""Tests for VI Resorts data models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from vi_resorts.models import (
    Booking,
    Cost,
    CostCategory,
    LedgerEntry,
    OwnershipRules,
    PointBalance,
    PointType,
    Resort,
    Season,
    Trip,
    UnitType,
)


def test_resort_creation():
    """Test creating a resort with point costs."""
    resort = Resort(
        name="Test Resort",
        location="Test Location",
        country="USA",
        point_costs={
            "studio": {
                "peak": 2000,
                "regular": 1500,
            }
        }
    )
    
    assert resort.name == "Test Resort"
    assert resort.location == "Test Location"
    assert resort.country == "USA"
    assert "studio" in resort.point_costs
    assert resort.point_costs["studio"]["peak"] == 2000


def test_point_balance_operations():
    """Test point balance tracking."""
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=7000,
    )
    
    assert balance.available_points == 7000
    
    # Use some points
    balance.use_points(1000)
    assert balance.used_points == 1000
    assert balance.available_points == 6000
    
    # Try to use too many points
    with pytest.raises(ValueError):
        balance.use_points(7000)


def test_cost_validation():
    """Test cost creation and validation."""
    cost = Cost(
        date=date(2026, 1, 1),
        category=CostCategory.BOOKING_FEE,
        amount=99.00,
        description="Test booking fee"
    )
    
    assert isinstance(cost.amount, Decimal)
    assert cost.amount == Decimal("99.00")
    assert cost.category == CostCategory.BOOKING_FEE


def test_booking_calculations():
    """Test booking night and point calculations."""
    booking = Booking(
        resort_id=UUID('12345678-1234-5678-1234-567812345678'),
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 8),
        unit_type=UnitType.STUDIO,
        season=Season.REGULAR,
        points_used=10500,
    )
    
    assert booking.nights == 7
    assert booking.points_per_night == 1500.0


def test_trip_duration():
    """Test trip duration calculation."""
    trip = Trip(
        name="Test Trip",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 8),
    )
    
    assert trip.duration == 7


def test_ownership_rules_validation():
    """Test ownership rules validation."""
    rules = OwnershipRules(
        annual_points=7000,
        annual_fee=Decimal("1200.00"),
        booking_fee=Decimal("99.00"),
        guest_certificate_fee=Decimal("79.00"),
    )
    
    assert rules.annual_points == 7000
    assert rules.annual_fee == Decimal("1200.00")
    assert rules.can_save_points is True


def test_ledger_entry():
    """Test ledger entry creation."""
    entry = LedgerEntry(
        entry_type="cost",
        data={"amount": "100.00"},
        description="Test entry"
    )
    
    assert entry.entry_type == "cost"
    assert isinstance(entry.timestamp, datetime)
    assert entry.description == "Test entry"
