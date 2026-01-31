#!/usr/bin/env python
"""
Example usage of the VI Resorts Concierge system.

This script demonstrates the full capabilities of the system including:
- Setting up ownership rules
- Adding resorts
- Managing point balances
- Creating bookings
- Planning trips
- Tracking costs
- Generating financial reports
"""

from datetime import date, timedelta
from decimal import Decimal

from vi_resorts import (
    Concierge,
    Cost,
    CostCategory,
    OwnershipRules,
    PointBalance,
    PointType,
    Resort,
    Season,
    UnitType,
)


def main():
    """Run the example."""
    print("=" * 80)
    print("VI Resorts Concierge - Example Usage")
    print("=" * 80)
    
    # 1. Define ownership rules
    print("\n1. Setting up ownership rules...")
    rules = OwnershipRules(
        annual_points=7000,
        annual_fee=Decimal("1200.00"),
        booking_fee=Decimal("99.00"),
        guest_certificate_fee=Decimal("79.00"),
        points_expire_months=12,
        can_save_points=True,
        can_borrow_points=True,
        booking_window_days=365,
    )
    print(f"   ✓ Annual points: {rules.annual_points}")
    print(f"   ✓ Annual fee: ${rules.annual_fee}")
    print(f"   ✓ Booking fee: ${rules.booking_fee}")
    
    # 2. Create the concierge
    print("\n2. Creating concierge system...")
    concierge = Concierge(rules)
    print("   ✓ Concierge initialized")
    print("   ✓ Accountant sub-agent ready")
    
    # 3. Add resorts
    print("\n3. Adding resorts...")
    cabo = Resort(
        name="Cabo Azul Resort",
        location="San José del Cabo",
        country="Mexico",
        description="Luxury beachfront resort in Los Cabos",
        amenities=["Beach Access", "Pool", "Restaurant", "Spa", "Golf Nearby"],
        point_costs={
            "studio": {"peak": 2500, "high": 2000, "regular": 1500, "low": 1200},
            "one_bedroom": {"peak": 3500, "high": 2800, "regular": 2200, "low": 1800},
            "two_bedroom": {"peak": 5000, "high": 4000, "regular": 3200, "low": 2500},
        }
    )
    concierge.add_resort(cabo)
    print(f"   ✓ Added: {cabo.name} in {cabo.location}, {cabo.country}")
    
    sedona = Resort(
        name="Sedona Summit",
        location="Sedona, Arizona",
        country="USA",
        description="Red rock views in the heart of Sedona",
        amenities=["Pool", "Hot Tub", "Fitness Center", "Hiking Trails"],
        point_costs={
            "studio": {"peak": 1800, "high": 1400, "regular": 1100, "low": 900},
            "one_bedroom": {"peak": 2500, "high": 2000, "regular": 1600, "low": 1300},
            "two_bedroom": {"peak": 3500, "high": 2800, "regular": 2300, "low": 1900},
        }
    )
    concierge.add_resort(sedona)
    print(f"   ✓ Added: {sedona.name} in {sedona.location}, {sedona.country}")
    
    # 4. Add point balances
    print("\n4. Adding point balances...")
    current_year = date.today().year
    
    # Annual points
    annual_points = PointBalance(
        year=current_year,
        point_type=PointType.ANNUAL,
        total_points=7000,
        expiration_date=date(current_year + 1, 12, 31),
    )
    concierge.add_point_balance(annual_points)
    print(f"   ✓ Added {annual_points.total_points} annual points for {current_year}")
    
    # Saved points from last year
    saved_points = PointBalance(
        year=current_year - 1,
        point_type=PointType.SAVED,
        total_points=2000,
        expiration_date=date(current_year, 6, 30),  # Expiring soon!
    )
    concierge.add_point_balance(saved_points)
    print(f"   ✓ Added {saved_points.total_points} saved points (expiring {saved_points.expiration_date})")
    
    print(f"\n   Total available points: {concierge.get_available_points()}")
    
    # 5. Create bookings
    print("\n5. Creating bookings...")
    
    # Booking 1: Cabo in summer (use expiring points) - 5 nights in low season
    cabo_checkin = date(current_year, 6, 15)
    cabo_checkout = cabo_checkin + timedelta(days=5)  # 5 nights instead of 7
    
    cabo_booking = concierge.create_booking(
        cabo.id,
        cabo_checkin,
        cabo_checkout,
        UnitType.STUDIO,
        Season.LOW,  # Low season to conserve points
        guest_name="John and Jane Doe",
    )
    print(f"   ✓ Cabo booking created:")
    print(f"     - Check-in: {cabo_booking.check_in}")
    print(f"     - Check-out: {cabo_booking.check_out}")
    print(f"     - Nights: {cabo_booking.nights}")
    print(f"     - Points used: {cabo_booking.points_used}")
    
    # Booking 2: Sedona in fall - 2 nights in low season
    sedona_checkin = date(current_year, 10, 1)
    sedona_checkout = sedona_checkin + timedelta(days=2)  # 2 nights
    
    sedona_booking = concierge.create_booking(
        sedona.id,
        sedona_checkin,
        sedona_checkout,
        UnitType.STUDIO,  # Studio instead of one-bedroom
        Season.LOW,  # Low season
        guest_name="John and Jane Doe",
    )
    print(f"   ✓ Sedona booking created:")
    print(f"     - Check-in: {sedona_booking.check_in}")
    print(f"     - Check-out: {sedona_booking.check_out}")
    print(f"     - Nights: {sedona_booking.nights}")
    print(f"     - Points used: {sedona_booking.points_used}")
    
    print(f"\n   Remaining points: {concierge.get_available_points()}")
    
    # 6. Create a trip
    print("\n6. Creating a trip...")
    summer_trip = concierge.create_trip(
        name="Summer Vacation 2026",
        start_date=cabo_checkin,
        end_date=cabo_checkout,
        booking_ids=[cabo_booking.id],
        travelers=2,
        notes="Beach vacation in Cabo",
    )
    print(f"   ✓ Trip created: {summer_trip.name}")
    print(f"     - Duration: {summer_trip.duration} days")
    print(f"     - Travelers: {summer_trip.travelers}")
    
    # 7. Add costs
    print("\n7. Recording additional costs...")
    
    # Airfare
    airfare = Cost(
        date=cabo_checkin,
        category=CostCategory.TRAVEL,
        amount=Decimal("800.00"),
        description="Round-trip flights to Cabo",
        trip_id=summer_trip.id,
    )
    concierge.accountant.record_cost(airfare)
    print(f"   ✓ Recorded: {airfare.description} - ${airfare.amount}")
    
    # Car rental
    car = Cost(
        date=cabo_checkin,
        category=CostCategory.TRAVEL,
        amount=Decimal("350.00"),
        description="Car rental for 7 days",
        trip_id=summer_trip.id,
    )
    concierge.accountant.record_cost(car)
    print(f"   ✓ Recorded: {car.description} - ${car.amount}")
    
    # Meals
    meals = Cost(
        date=cabo_checkin + timedelta(days=3),
        category=CostCategory.MEALS,
        amount=Decimal("600.00"),
        description="Dining expenses",
        trip_id=summer_trip.id,
    )
    concierge.accountant.record_cost(meals)
    print(f"   ✓ Recorded: {meals.description} - ${meals.amount}")
    
    # Activities
    activities = Cost(
        date=cabo_checkin + timedelta(days=2),
        category=CostCategory.ACTIVITIES,
        amount=Decimal("450.00"),
        description="Snorkeling tour and spa",
        trip_id=summer_trip.id,
    )
    concierge.accountant.record_cost(activities)
    print(f"   ✓ Recorded: {activities.description} - ${activities.amount}")
    
    # 8. Generate financial analysis
    print("\n8. Generating financial analysis...")
    analysis = concierge.accountant.analyze_costs(current_year)
    
    print(f"\n   📊 Cost Summary for {current_year}:")
    print(f"   {'─' * 60}")
    print(f"   Total Annual Cost:        ${analysis.annual_cost:>10,.2f}")
    print(f"   Cost Per Point:           ${analysis.cost_per_point:>10,.2f}")
    
    if analysis.trip_costs:
        print(f"\n   Trip Costs:")
        for trip_id, cost in analysis.trip_costs.items():
            trip = concierge.accountant.trips[trip_id]
            print(f"     {trip.name:<30} ${cost:>10,.2f}")
    
    if analysis.booking_costs:
        print(f"\n   Booking Breakdown:")
        for booking_id, cost in analysis.booking_costs.items():
            booking = concierge.accountant.bookings[booking_id]
            resort = concierge.get_resort(booking.resort_id)
            cost_per_night = analysis.cost_per_night[booking_id]
            print(f"     {resort.name:<30}")
            print(f"       Total Cost:             ${cost:>10,.2f}")
            print(f"       Cost Per Night:         ${cost_per_night:>10,.2f}")
            print(f"       Points Used:            {booking.points_used:>10,}")
            print(f"       Points Per Night:       {booking.points_per_night:>10,.1f}")
    
    # 9. Show point value insights
    print("\n9. Point value insights...")
    print(f"   {'─' * 60}")
    print(f"   Each point costs you ${analysis.cost_per_point:.2f} when factoring in:")
    print(f"     - Annual maintenance fee")
    print(f"     - Booking fees")
    print(f"     - All other costs")
    print(f"\n   To maximize value:")
    print(f"     ✓ Use all {rules.annual_points:,} points each year")
    print(f"     ✓ Book during low/regular seasons when possible")
    print(f"     ✓ Use expiring points first (optimizer does this automatically)")
    
    # 10. Show ledger summary
    print("\n10. Audit ledger summary...")
    ledger = concierge.accountant.get_ledger_report()
    print(f"   Total ledger entries: {len(ledger)}")
    print(f"   Entry types:")
    
    entry_types = {}
    for entry in ledger:
        entry_type = entry['entry_type']
        entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
    
    for entry_type, count in sorted(entry_types.items()):
        print(f"     - {entry_type}: {count}")
    
    print("\n" + "=" * 80)
    print("Example complete! Use 'vi-concierge' CLI to explore more features.")
    print("=" * 80)


if __name__ == "__main__":
    main()
