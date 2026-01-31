"""
VI Resorts Concierge - Main system for managing VI ownership.

Provides functionality to:
- Browse and search resorts
- Plan trips and optimize point usage
- Make bookings
- Explain VI rules and policies
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from .accountant import Accountant
from .models import (
    Booking,
    OwnershipRules,
    PointBalance,
    PointType,
    Resort,
    Season,
    Trip,
    UnitType,
)


class PointOptimizer:
    """Optimizes point usage for bookings."""
    
    def __init__(self, point_balances: list[PointBalance]):
        """
        Initialize optimizer with available point balances.
        
        Args:
            point_balances: List of available point balances
        """
        self.point_balances = sorted(
            point_balances,
            key=lambda b: (
                b.expiration_date or date.max,  # Expiring points first
                b.point_type.value  # Then by type
            )
        )
    
    def allocate_points(self, points_needed: int) -> list[tuple[UUID, int]]:
        """
        Allocate points optimally from available balances.
        
        Strategy:
        1. Use points closest to expiration first
        2. Prefer saved points over annual points
        3. Use borrowed points last
        
        Args:
            points_needed: Number of points to allocate
            
        Returns:
            List of (balance_id, points_used) tuples
            
        Raises:
            ValueError: If insufficient points available
        """
        total_available = sum(b.available_points for b in self.point_balances)
        
        if total_available < points_needed:
            raise ValueError(
                f"Insufficient points: {total_available} available, {points_needed} needed"
            )
        
        allocations = []
        remaining = points_needed
        
        for balance in self.point_balances:
            if remaining <= 0:
                break
            
            available = balance.available_points
            to_use = min(available, remaining)
            
            if to_use > 0:
                allocations.append((balance.id, to_use))
                balance.use_points(to_use)
                remaining -= to_use
        
        return allocations


class Concierge:
    """
    The main VI Resorts Concierge system.
    
    Manages resorts, bookings, trips, and provides an interface to the Accountant.
    """
    
    def __init__(self, rules: OwnershipRules):
        """
        Initialize the Concierge with ownership rules.
        
        Args:
            rules: The ownership rules and assumptions
        """
        self.rules = rules
        self.accountant = Accountant(rules)
        self.resorts: dict[UUID, Resort] = {}
        self.point_balances: list[PointBalance] = []
    
    def add_resort(self, resort: Resort) -> None:
        """
        Add a resort to the system.
        
        Args:
            resort: The resort to add
        """
        self.resorts[resort.id] = resort
    
    def list_resorts(
        self,
        country: Optional[str] = None,
        location: Optional[str] = None,
    ) -> list[Resort]:
        """
        List resorts with optional filtering.
        
        Args:
            country: Filter by country
            location: Filter by location (partial match)
            
        Returns:
            List of matching resorts
        """
        resorts = list(self.resorts.values())
        
        if country:
            resorts = [r for r in resorts if r.country.lower() == country.lower()]
        
        if location:
            resorts = [
                r for r in resorts
                if location.lower() in r.location.lower()
            ]
        
        return sorted(resorts, key=lambda r: r.name)
    
    def get_resort(self, resort_id: UUID) -> Optional[Resort]:
        """
        Get a specific resort by ID.
        
        Args:
            resort_id: The resort ID
            
        Returns:
            The resort or None if not found
        """
        return self.resorts.get(resort_id)
    
    def add_point_balance(self, balance: PointBalance) -> None:
        """
        Add a point balance to the system.
        
        Args:
            balance: The point balance to add
        """
        self.point_balances.append(balance)
        self.accountant.record_point_balance(balance)
    
    def get_available_points(self, year: Optional[int] = None) -> int:
        """
        Get total available points.
        
        Args:
            year: Optional year filter
            
        Returns:
            Total available points
        """
        balances = self.point_balances
        if year:
            balances = [b for b in balances if b.year == year]
        
        return sum(b.available_points for b in balances)
    
    def calculate_booking_points(
        self,
        resort: Resort,
        unit_type: UnitType,
        season: Season,
        nights: int,
    ) -> int:
        """
        Calculate points needed for a booking.
        
        Args:
            resort: The resort
            unit_type: Type of unit
            season: Season
            nights: Number of nights
            
        Returns:
            Total points needed
            
        Raises:
            ValueError: If point cost not defined
        """
        unit_key = unit_type.value
        season_key = season.value
        
        if unit_key not in resort.point_costs:
            raise ValueError(f"No point costs defined for {unit_type.value}")
        
        if season_key not in resort.point_costs[unit_key]:
            raise ValueError(f"No point costs defined for {season.value} season")
        
        points_per_night = resort.point_costs[unit_key][season_key]
        return points_per_night * nights
    
    def create_booking(
        self,
        resort_id: UUID,
        check_in: date,
        check_out: date,
        unit_type: UnitType,
        season: Season,
        guest_name: Optional[str] = None,
        optimize: bool = True,
    ) -> Booking:
        """
        Create a new booking.
        
        Args:
            resort_id: The resort ID
            check_in: Check-in date
            check_out: Check-out date
            unit_type: Type of unit
            season: Season
            guest_name: Optional guest name
            optimize: Whether to optimize point allocation
            
        Returns:
            The created booking
            
        Raises:
            ValueError: If resort not found or insufficient points
        """
        resort = self.resorts.get(resort_id)
        if not resort:
            raise ValueError(f"Resort not found: {resort_id}")
        
        # Validate booking window
        days_ahead = (check_in - date.today()).days
        if days_ahead > self.rules.booking_window_days:
            raise ValueError(
                f"Booking is {days_ahead} days ahead, "
                f"maximum is {self.rules.booking_window_days} days"
            )
        
        nights = (check_out - check_in).days
        if nights <= 0:
            raise ValueError("Check-out must be after check-in")
        
        points_needed = self.calculate_booking_points(resort, unit_type, season, nights)
        
        # Allocate points
        if optimize:
            optimizer = PointOptimizer(self.point_balances)
            allocations = optimizer.allocate_points(points_needed)
            point_balance_ids = [balance_id for balance_id, _ in allocations]
        else:
            # Use points in order without optimization
            point_balance_ids = []
            remaining = points_needed
            for balance in self.point_balances:
                if remaining <= 0:
                    break
                to_use = min(balance.available_points, remaining)
                if to_use > 0:
                    balance.use_points(to_use)
                    point_balance_ids.append(balance.id)
                    remaining -= to_use
            
            if remaining > 0:
                raise ValueError(f"Insufficient points: {remaining} points short")
        
        booking = Booking(
            resort_id=resort_id,
            check_in=check_in,
            check_out=check_out,
            unit_type=unit_type,
            season=season,
            points_used=points_needed,
            point_balance_ids=point_balance_ids,
            guest_name=guest_name,
        )
        
        self.accountant.record_booking(booking)
        return booking
    
    def create_trip(
        self,
        name: str,
        start_date: date,
        end_date: date,
        booking_ids: list[UUID],
        travelers: int = 1,
        notes: Optional[str] = None,
    ) -> Trip:
        """
        Create a new trip.
        
        Args:
            name: Trip name
            start_date: Trip start date
            end_date: Trip end date
            booking_ids: List of booking IDs in this trip
            travelers: Number of travelers
            notes: Optional notes
            
        Returns:
            The created trip
        """
        trip = Trip(
            name=name,
            start_date=start_date,
            end_date=end_date,
            bookings=booking_ids,
            travelers=travelers,
            notes=notes,
        )
        
        self.accountant.record_trip(trip)
        return trip
    
    def explain_rules(self) -> dict[str, any]:
        """
        Explain the VI ownership rules.
        
        Returns:
            Dictionary with rule explanations
        """
        return {
            "Annual Points": f"You receive {self.rules.annual_points} points each year",
            "Annual Fee": f"${self.rules.annual_fee} maintenance fee per year",
            "Booking Fee": f"${self.rules.booking_fee} per booking",
            "Guest Certificate Fee": f"${self.rules.guest_certificate_fee} to book for non-members",
            "Point Expiration": f"Points expire after {self.rules.points_expire_months} months",
            "Save Points": "Yes" if self.rules.can_save_points else "No",
            "Borrow Points": "Yes" if self.rules.can_borrow_points else "No",
            "Max Saved Points": self.rules.max_saved_points or "No limit",
            "Booking Window": f"Can book up to {self.rules.booking_window_days} days in advance",
        }
    
    def get_point_value_estimate(self) -> dict[str, any]:
        """
        Estimate the value of points based on costs.
        
        Returns:
            Dictionary with value estimates
        """
        cost_per_point = self.accountant.get_cost_per_point()
        
        return {
            "Cost Per Point": f"${cost_per_point:.2f}",
            "Point Value": f"Each point costs you ${cost_per_point:.2f} when factoring in all fees",
            "Break-Even": f"Use all {self.rules.annual_points} points to maximize value",
        }
