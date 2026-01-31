"""Tests for the Accountant sub-agent."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from vi_resorts.accountant import Accountant
from vi_resorts.models import (
    Booking,
    Cost,
    CostCategory,
    OwnershipRules,
    PointBalance,
    PointType,
    Season,
    Trip,
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
    )


@pytest.fixture
def accountant(rules):
    """Create test accountant."""
    return Accountant(rules)


def test_accountant_initialization(accountant, rules):
    """Test accountant initialization."""
    assert accountant.rules == rules
    assert len(accountant.ledger) == 0
    assert len(accountant.costs) == 0


def test_record_cost(accountant):
    """Test recording a cost."""
    cost = Cost(
        date=date(2026, 1, 15),
        category=CostCategory.TRAVEL,
        amount=Decimal("500.00"),
        description="Airfare"
    )
    
    accountant.record_cost(cost)
    
    assert len(accountant.costs) == 1
    assert len(accountant.ledger) == 1
    assert accountant.ledger[0].entry_type == "cost"


def test_record_booking(accountant):
    """Test recording a booking."""
    resort_id = uuid4()
    booking = Booking(
        resort_id=resort_id,
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 8),
        unit_type=UnitType.STUDIO,
        season=Season.REGULAR,
        points_used=10500,
    )
    
    accountant.record_booking(booking)
    
    assert booking.id in accountant.bookings
    assert len(accountant.ledger) == 2  # booking + booking fee
    assert len(accountant.costs) == 1  # booking fee


def test_record_trip(accountant):
    """Test recording a trip."""
    trip = Trip(
        name="Summer Vacation",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 15),
    )
    
    accountant.record_trip(trip)
    
    assert trip.id in accountant.trips
    assert len(accountant.ledger) == 1


def test_record_point_balance(accountant):
    """Test recording point balance."""
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=7000,
    )
    
    accountant.record_point_balance(balance)
    
    assert balance.id in accountant.point_balances
    assert len(accountant.ledger) == 1


def test_get_trip_cost(accountant):
    """Test calculating trip cost."""
    trip = Trip(
        name="Test Trip",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 8),
    )
    accountant.record_trip(trip)
    
    # Add costs for the trip
    cost1 = Cost(
        date=date(2026, 6, 1),
        category=CostCategory.TRAVEL,
        amount=Decimal("500.00"),
        description="Airfare",
        trip_id=trip.id,
    )
    cost2 = Cost(
        date=date(2026, 6, 2),
        category=CostCategory.MEALS,
        amount=Decimal("200.00"),
        description="Dining",
        trip_id=trip.id,
    )
    
    accountant.record_cost(cost1)
    accountant.record_cost(cost2)
    
    total = accountant.get_trip_cost(trip.id)
    assert total == Decimal("700.00")


def test_get_booking_cost(accountant):
    """Test calculating booking cost."""
    resort_id = uuid4()
    booking = Booking(
        resort_id=resort_id,
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 8),
        unit_type=UnitType.STUDIO,
        season=Season.REGULAR,
        points_used=10500,
    )
    
    accountant.record_booking(booking)
    
    # Booking fee should be recorded automatically
    cost = accountant.get_booking_cost(booking.id)
    assert cost == accountant.rules.booking_fee


def test_get_cost_per_night(accountant):
    """Test calculating cost per night."""
    resort_id = uuid4()
    booking = Booking(
        resort_id=resort_id,
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 8),  # 7 nights
        unit_type=UnitType.STUDIO,
        season=Season.REGULAR,
        points_used=10500,
    )
    
    accountant.record_booking(booking)
    
    cost_per_night = accountant.get_cost_per_night(booking.id)
    # Booking fee of 99.00 / 7 nights
    expected = accountant.rules.booking_fee / Decimal("7")
    assert cost_per_night == expected


def test_get_annual_cost(accountant):
    """Test calculating annual cost."""
    # Add some costs for 2026
    cost1 = Cost(
        date=date(2026, 6, 1),
        category=CostCategory.TRAVEL,
        amount=Decimal("500.00"),
        description="Travel"
    )
    cost2 = Cost(
        date=date(2026, 7, 1),
        category=CostCategory.MEALS,
        amount=Decimal("300.00"),
        description="Meals"
    )
    
    accountant.record_cost(cost1)
    accountant.record_cost(cost2)
    
    annual_cost = accountant.get_annual_cost(2026)
    
    # Should include annual fee + costs
    expected = accountant.rules.annual_fee + Decimal("800.00")
    assert annual_cost == expected


def test_get_cost_per_point(accountant):
    """Test calculating cost per point."""
    # Record point balance
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=7000,
    )
    accountant.record_point_balance(balance)
    
    # Create a booking using points
    resort_id = uuid4()
    booking = Booking(
        resort_id=resort_id,
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 8),
        unit_type=UnitType.STUDIO,
        season=Season.REGULAR,
        points_used=3500,  # Half the annual points
    )
    accountant.record_booking(booking)
    
    # Calculate cost per point for 2026
    cost_per_point = accountant.get_cost_per_point(2026)
    
    # Total cost = annual fee + booking fee
    total_cost = accountant.rules.annual_fee + accountant.rules.booking_fee
    expected = total_cost / Decimal("3500")
    
    assert cost_per_point == expected


def test_analyze_costs(accountant):
    """Test comprehensive cost analysis."""
    # Setup: Record point balance, booking, and trip
    balance = PointBalance(
        year=2026,
        point_type=PointType.ANNUAL,
        total_points=7000,
    )
    accountant.record_point_balance(balance)
    
    resort_id = uuid4()
    booking = Booking(
        resort_id=resort_id,
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 8),
        unit_type=UnitType.STUDIO,
        season=Season.REGULAR,
        points_used=3500,
    )
    accountant.record_booking(booking)
    
    trip = Trip(
        name="Summer Trip",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 8),
        bookings=[booking.id],
    )
    accountant.record_trip(trip)
    
    # Add trip cost
    cost = Cost(
        date=date(2026, 6, 1),
        category=CostCategory.TRAVEL,
        amount=Decimal("500.00"),
        description="Airfare",
        trip_id=trip.id,
    )
    accountant.record_cost(cost)
    
    # Analyze
    analysis = accountant.analyze_costs(2026)
    
    assert analysis.total_cost > 0
    assert trip.id in analysis.trip_costs
    assert booking.id in analysis.booking_costs
    assert booking.id in analysis.cost_per_night
    assert analysis.cost_per_point > 0


def test_ledger_report(accountant):
    """Test getting ledger report."""
    # Record some entries
    cost = Cost(
        date=date(2026, 1, 15),
        category=CostCategory.TRAVEL,
        amount=Decimal("500.00"),
        description="Airfare"
    )
    accountant.record_cost(cost)
    
    report = accountant.get_ledger_report()
    
    assert len(report) == 1
    assert isinstance(report[0], dict)
    assert report[0]['entry_type'] == 'cost'
