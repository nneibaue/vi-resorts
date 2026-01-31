"""
Accountant sub-agent for VI Resorts Concierge.

Tracks all vacation costs in an audit-friendly ledger and computes:
- True cost per trip
- Cost per night
- Cost per year
- True cost per point
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from .models import (
    Booking,
    Cost,
    CostCategory,
    LedgerEntry,
    OwnershipRules,
    PointBalance,
    Trip,
)


class CostAnalysis:
    """Analysis results from the Accountant."""
    
    def __init__(
        self,
        total_cost: Decimal,
        trip_costs: dict[UUID, Decimal],
        booking_costs: dict[UUID, Decimal],
        cost_per_night: dict[UUID, Decimal],
        cost_per_point: Decimal,
        annual_cost: Decimal,
    ):
        self.total_cost = total_cost
        self.trip_costs = trip_costs
        self.booking_costs = booking_costs
        self.cost_per_night = cost_per_night
        self.cost_per_point = cost_per_point
        self.annual_cost = annual_cost


class Accountant:
    """
    The Accountant sub-agent manages financial tracking for VI ownership.
    
    Maintains an audit-friendly ledger of all costs and provides precise
    cost analysis with explicit assumptions.
    """
    
    def __init__(self, rules: OwnershipRules):
        """
        Initialize the Accountant with ownership rules.
        
        Args:
            rules: The ownership rules that define fees and constraints
        """
        self.rules = rules
        self.ledger: list[LedgerEntry] = []
        self.costs: list[Cost] = []
        self.bookings: dict[UUID, Booking] = {}
        self.trips: dict[UUID, Trip] = {}
        self.point_balances: dict[UUID, PointBalance] = {}
    
    def record_cost(self, cost: Cost) -> None:
        """
        Record a cost in the ledger.
        
        Args:
            cost: The cost to record
        """
        self.costs.append(cost)
        
        entry = LedgerEntry(
            entry_type="cost",
            data=cost.model_dump(mode='json'),
            description=f"{cost.category.value}: {cost.description} - ${cost.amount}"
        )
        self.ledger.append(entry)
    
    def record_booking(self, booking: Booking) -> None:
        """
        Record a booking and its associated costs.
        
        Args:
            booking: The booking to record
        """
        self.bookings[booking.id] = booking
        
        entry = LedgerEntry(
            entry_type="booking",
            data=booking.model_dump(mode='json'),
            description=f"Booking: {booking.unit_type.value} for {booking.nights} nights, {booking.points_used} points"
        )
        self.ledger.append(entry)
        
        # Record booking fee if applicable
        if self.rules.booking_fee > 0:
            booking_fee = Cost(
                date=booking.check_in,
                category=CostCategory.BOOKING_FEE,
                amount=self.rules.booking_fee,
                description=f"Booking fee for {booking.nights} night stay",
                booking_id=booking.id
            )
            self.record_cost(booking_fee)
    
    def record_trip(self, trip: Trip) -> None:
        """
        Record a trip.
        
        Args:
            trip: The trip to record
        """
        self.trips[trip.id] = trip
        
        entry = LedgerEntry(
            entry_type="trip",
            data=trip.model_dump(mode='json'),
            description=f"Trip: {trip.name} ({trip.start_date} to {trip.end_date})"
        )
        self.ledger.append(entry)
    
    def record_point_balance(self, balance: PointBalance) -> None:
        """
        Record a point balance allocation.
        
        Args:
            balance: The point balance to record
        """
        self.point_balances[balance.id] = balance
        
        entry = LedgerEntry(
            entry_type="point_allocation",
            data=balance.model_dump(mode='json'),
            description=f"Point allocation: {balance.total_points} {balance.point_type.value} points for {balance.year}"
        )
        self.ledger.append(entry)
    
    def get_trip_cost(self, trip_id: UUID) -> Decimal:
        """
        Calculate total cost for a specific trip.
        
        Args:
            trip_id: The trip ID
            
        Returns:
            Total cost for the trip
        """
        trip_costs = [
            cost.amount
            for cost in self.costs
            if cost.trip_id == trip_id
        ]
        
        # Also include costs for bookings in this trip
        trip = self.trips.get(trip_id)
        if trip:
            for booking_id in trip.bookings:
                booking_costs = [
                    cost.amount
                    for cost in self.costs
                    if cost.booking_id == booking_id
                ]
                trip_costs.extend(booking_costs)
        
        return sum(trip_costs, Decimal("0"))
    
    def get_booking_cost(self, booking_id: UUID) -> Decimal:
        """
        Calculate total cost for a specific booking.
        
        Args:
            booking_id: The booking ID
            
        Returns:
            Total cost for the booking
        """
        booking_costs = [
            cost.amount
            for cost in self.costs
            if cost.booking_id == booking_id
        ]
        return sum(booking_costs, Decimal("0"))
    
    def get_cost_per_night(self, booking_id: UUID) -> Decimal:
        """
        Calculate cost per night for a booking.
        
        Args:
            booking_id: The booking ID
            
        Returns:
            Cost per night
        """
        booking = self.bookings.get(booking_id)
        if not booking or booking.nights == 0:
            return Decimal("0")
        
        total_cost = self.get_booking_cost(booking_id)
        return total_cost / Decimal(str(booking.nights))
    
    def get_annual_cost(self, year: int) -> Decimal:
        """
        Calculate total cost for a specific year.
        
        Includes:
        - Annual maintenance fee (prorated if ownership started mid-year)
        - All costs recorded in that year
        
        Args:
            year: The year to calculate costs for
            
        Returns:
            Total annual cost
        """
        # Include annual fee
        annual_cost = self.rules.annual_fee
        
        # Add all costs in this year
        yearly_costs = [
            cost.amount
            for cost in self.costs
            if cost.date.year == year and cost.category != CostCategory.ANNUAL_FEE
        ]
        
        return annual_cost + sum(yearly_costs, Decimal("0"))
    
    def get_cost_per_point(self, year: Optional[int] = None) -> Decimal:
        """
        Calculate true cost per point.
        
        This is a key metric that divides total costs by total points used.
        
        Assumptions:
        - Annual fee is amortized across all points for the year
        - If year is None, calculates across all years
        
        Args:
            year: Optional year to calculate for, or None for all-time
            
        Returns:
            Cost per point
        """
        if year:
            # Calculate for specific year
            total_cost = self.get_annual_cost(year)
            
            # Count points used in this year
            points_used = sum(
                booking.points_used
                for booking in self.bookings.values()
                if booking.check_in.year == year or booking.check_out.year == year
            )
            
            # If no points used, divide by allocated points
            if points_used == 0:
                points_used = self.rules.annual_points
        else:
            # Calculate across all time
            total_cost = sum(cost.amount for cost in self.costs)
            
            # Add annual fees for each year we have point balances
            years_active = set(balance.year for balance in self.point_balances.values())
            total_cost += self.rules.annual_fee * len(years_active) if years_active else self.rules.annual_fee
            
            points_used = sum(booking.points_used for booking in self.bookings.values())
            
            # If no points used, use total allocated points
            if points_used == 0:
                points_used = self.rules.annual_points * max(1, len(years_active))
        
        if points_used == 0:
            return Decimal("0")
        
        return total_cost / Decimal(str(points_used))
    
    def analyze_costs(self, year: Optional[int] = None) -> CostAnalysis:
        """
        Generate a comprehensive cost analysis.
        
        Args:
            year: Optional year to analyze, or None for all-time
            
        Returns:
            CostAnalysis with all computed metrics
        """
        # Filter by year if specified
        if year:
            relevant_costs = [c for c in self.costs if c.date.year == year]
            relevant_bookings = {
                bid: b for bid, b in self.bookings.items()
                if b.check_in.year == year or b.check_out.year == year
            }
            relevant_trips = {
                tid: t for tid, t in self.trips.items()
                if t.start_date.year == year or t.end_date.year == year
            }
        else:
            relevant_costs = self.costs
            relevant_bookings = self.bookings
            relevant_trips = self.trips
        
        total_cost = sum(c.amount for c in relevant_costs)
        if year:
            total_cost += self.rules.annual_fee
        
        trip_costs = {
            trip_id: self.get_trip_cost(trip_id)
            for trip_id in relevant_trips.keys()
        }
        
        booking_costs = {
            booking_id: self.get_booking_cost(booking_id)
            for booking_id in relevant_bookings.keys()
        }
        
        cost_per_night = {
            booking_id: self.get_cost_per_night(booking_id)
            for booking_id in relevant_bookings.keys()
        }
        
        cost_per_point = self.get_cost_per_point(year)
        annual_cost = self.get_annual_cost(year) if year else Decimal("0")
        
        return CostAnalysis(
            total_cost=total_cost,
            trip_costs=trip_costs,
            booking_costs=booking_costs,
            cost_per_night=cost_per_night,
            cost_per_point=cost_per_point,
            annual_cost=annual_cost,
        )
    
    def get_ledger_report(self) -> list[dict]:
        """
        Get the complete audit ledger.
        
        Returns:
            List of ledger entries as dictionaries
        """
        return [entry.model_dump(mode='json') for entry in self.ledger]
