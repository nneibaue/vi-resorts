"""Tests for the Concierge system."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from vi_resorts.concierge import Concierge, PointOptimizer
from vi_resorts.models import (
    OwnershipRules,
    PointBalance,
    PointType,
    Resort,
    Season,
    UnitType,
)


@pytest.fixture
def rules():
    """Create test ownership rules."""
    return OwnershipRules(
        annual_points=7000,
        annual_fee=Decimal("1200.00"),
        booking_fee=Decimal("99.00"),
        guest_certificate_fee=Decimal("79.00"),
        booking_window_days=365,
    )


@pytest.fixture
def concierge(rules):
    """Create test concierge."""
    return Concierge(rules)


@pytest.fixture
def test_resort():
    """Create a test resort."""
    return Resort(
        name="Test Resort",
        location="Test Location",
        country="USA",
        point_costs={
            "studio": {
                "peak": 2000,
                "high": 1600,
                "regular": 1500,
                "low": 1200,
            },
            "one_bedroom": {
                "peak": 2800,
                "high": 2400,
                "regular": 2200,
                "low": 1800,
            },
        }
    )


def test_concierge_initialization(concierge, rules):
    """Test concierge initialization."""
    assert concierge.rules == rules
    assert isinstance(concierge.accountant, type(concierge.accountant))
    assert len(concierge.resorts) == 0


def test_add_resort(concierge, test_resort):
    """Test adding a resort."""
    concierge.add_resort(test_resort)
    
    assert test_resort.id in concierge.resorts
    assert concierge.get_resort(test_resort.id) == test_resort


def test_list_resorts(concierge, test_resort):
    """Test listing resorts."""
    concierge.add_resort(test_resort)
    
    # List all
    resorts = concierge.list_resorts()
    assert len(resorts) == 1
    assert resorts[0] == test_resort
    
    # Filter by country
    resorts = concierge.list_resorts(country="USA")
    assert len(resorts) == 1
    
    resorts = concierge.list_resorts(country="Mexico")
    assert len(resorts) == 0
    
    # Filter by location
    resorts = concierge.list_resorts(location="Test")
    assert len(resorts) == 1


def test_add_point_balance(concierge):
    """Test adding point balance."""
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=7000,
    )
    
    concierge.add_point_balance(balance)
    
    assert balance in concierge.point_balances
    assert balance.id in concierge.accountant.point_balances


def test_get_available_points(concierge):
    """Test getting available points."""
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=7000,
    )
    concierge.add_point_balance(balance)
    
    available = concierge.get_available_points(2026)
    assert available == 7000
    
    # Use some points
    balance.use_points(1000)
    available = concierge.get_available_points(2026)
    assert available == 6000


def test_calculate_booking_points(concierge, test_resort):
    """Test calculating booking points."""
    concierge.add_resort(test_resort)
    
    points = concierge.calculate_booking_points(
        test_resort,
        UnitType.STUDIO,
        Season.REGULAR,
        7  # nights
    )
    
    assert points == 1500 * 7


def test_create_booking(concierge, test_resort):
    """Test creating a booking."""
    concierge.add_resort(test_resort)
    
    # Add enough points for 7 nights at 1500 points/night = 10500 points
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=12000,  # More than enough for the booking
    )
    concierge.add_point_balance(balance)
    
    # Create booking
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=7)
    
    booking = concierge.create_booking(
        test_resort.id,
        check_in,
        check_out,
        UnitType.STUDIO,
        Season.REGULAR,
    )
    
    assert booking.resort_id == test_resort.id
    assert booking.nights == 7
    assert booking.points_used == 1500 * 7
    assert booking.id in concierge.accountant.bookings


def test_create_booking_insufficient_points(concierge, test_resort):
    """Test creating booking with insufficient points."""
    concierge.add_resort(test_resort)
    
    # Add only 1000 points (not enough)
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=1000,
    )
    concierge.add_point_balance(balance)
    
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=7)
    
    with pytest.raises(ValueError, match="Insufficient points"):
        concierge.create_booking(
            test_resort.id,
            check_in,
            check_out,
            UnitType.STUDIO,
            Season.REGULAR,
        )


def test_create_booking_beyond_window(concierge, test_resort):
    """Test creating booking beyond booking window."""
    concierge.add_resort(test_resort)
    
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=7000,
    )
    concierge.add_point_balance(balance)
    
    # Try to book 400 days ahead (beyond 365 day window)
    check_in = date.today() + timedelta(days=400)
    check_out = check_in + timedelta(days=7)
    
    with pytest.raises(ValueError, match="maximum is"):
        concierge.create_booking(
            test_resort.id,
            check_in,
            check_out,
            UnitType.STUDIO,
            Season.REGULAR,
        )


def test_create_trip(concierge):
    """Test creating a trip."""
    booking_id = uuid4()
    
    trip = concierge.create_trip(
        name="Summer Vacation",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 15),
        booking_ids=[booking_id],
        travelers=2,
    )
    
    assert trip.name == "Summer Vacation"
    assert trip.duration == 14
    assert booking_id in trip.bookings
    assert trip.id in concierge.accountant.trips


def test_explain_rules(concierge):
    """Test explaining ownership rules."""
    rules_dict = concierge.explain_rules()
    
    assert "Annual Points" in rules_dict
    assert "Annual Fee" in rules_dict
    assert "Booking Fee" in rules_dict
    assert "7000" in rules_dict["Annual Points"]


def test_get_point_value_estimate(concierge):
    """Test getting point value estimate."""
    estimate = concierge.get_point_value_estimate()
    
    assert "Cost Per Point" in estimate
    assert "Point Value" in estimate


def test_point_optimizer():
    """Test point optimizer allocation."""
    # Create multiple point balances
    expiring_soon = PointBalance(
        year=2026,
        point_type=PointType.SAVED,
        total_points=2000,
        expiration_date=date(2026, 6, 30),
    )
    
    annual = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=7000,
        expiration_date=date(2027, 12, 31),
    )
    
    optimizer = PointOptimizer([expiring_soon, annual])
    
    # Allocate 5000 points
    allocations = optimizer.allocate_points(5000)
    
    # Should use expiring points first
    assert len(allocations) == 2
    assert allocations[0][0] == expiring_soon.id
    assert allocations[0][1] == 2000
    assert allocations[1][0] == annual.id
    assert allocations[1][1] == 3000


def test_point_optimizer_insufficient():
    """Test point optimizer with insufficient points."""
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=1000,
    )
    
    optimizer = PointOptimizer([balance])
    
    with pytest.raises(ValueError, match="Insufficient points"):
        optimizer.allocate_points(5000)
