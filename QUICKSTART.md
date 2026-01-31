# VI Resorts Concierge - Quick Reference

## Common Commands

### View Ownership Rules
```bash
vi-concierge rules
```
Shows your VI ownership parameters including annual points, fees, and policies.

### Browse Resorts
```bash
# List all resorts
vi-concierge resorts

# Filter by country
vi-concierge resorts --country USA

# Filter by location
vi-concierge resorts --location "Cabo"
```

### View Resort Details
```bash
vi-concierge resort-details "Cabo Azul"
```
Shows amenities, descriptions, and point costs by season and unit type.

### Check Point Balance
```bash
# Current year
vi-concierge points

# Specific year
vi-concierge points --year 2026
```

### Create a Booking
```bash
vi-concierge book "Cabo Azul" 2026-06-01 2026-06-08 \
    --unit studio \
    --season regular \
    --guest "John Doe"
```

Unit types: `studio`, `1bed`, `2bed`, `3bed`  
Seasons: `peak`, `high`, `regular`, `low`

### Cost Analysis
```bash
# Current year
vi-concierge costs

# Specific year
vi-concierge costs --year 2026
```

### View Audit Ledger
```bash
vi-concierge ledger
```
Shows complete transaction history with timestamps.

## Python API Examples

### Basic Setup
```python
from decimal import Decimal
from vi_resorts import Concierge, OwnershipRules

rules = OwnershipRules(
    annual_points=7000,
    annual_fee=Decimal("1200.00"),
    booking_fee=Decimal("99.00"),
)

concierge = Concierge(rules)
```

### Add a Resort
```python
from vi_resorts import Resort

resort = Resort(
    name="My Resort",
    location="Beach Town",
    country="USA",
    point_costs={
        "studio": {"regular": 1500, "peak": 2500},
    }
)
concierge.add_resort(resort)
```

### Add Points
```python
from datetime import date
from vi_resorts import PointBalance, PointType

balance = PointBalance(
    year=2026,
    point_type=PointType.ANNUAL,
    total_points=7000,
    expiration_date=date(2027, 12, 31),
)
concierge.add_point_balance(balance)
```

### Create a Booking
```python
from datetime import date
from vi_resorts import UnitType, Season

booking = concierge.create_booking(
    resort.id,
    check_in=date(2026, 6, 1),
    check_out=date(2026, 6, 8),
    unit_type=UnitType.STUDIO,
    season=Season.REGULAR,
)
```

### Record Costs
```python
from vi_resorts import Cost, CostCategory

cost = Cost(
    date=date(2026, 6, 1),
    category=CostCategory.TRAVEL,
    amount=Decimal("500.00"),
    description="Airfare",
    trip_id=trip.id,
)
concierge.accountant.record_cost(cost)
```

### Analyze Costs
```python
analysis = concierge.accountant.analyze_costs(2026)

print(f"Total cost: ${analysis.total_cost}")
print(f"Cost per point: ${analysis.cost_per_point}")

for trip_id, cost in analysis.trip_costs.items():
    print(f"Trip {trip_id}: ${cost}")
```

## Key Concepts

### Point Optimizer
Automatically allocates points optimally:
1. Uses expiring points first
2. Prefers saved points over annual points  
3. Uses borrowed points last

### Accountant Ledger
Every transaction is recorded with:
- Unique ID
- Timestamp
- Entry type (cost, booking, trip, point allocation)
- Complete data snapshot
- Human-readable description

### Cost Analysis
Computes true costs including:
- Annual maintenance fees
- Booking fees
- Travel expenses
- Meals and activities
- Incidentals

Provides metrics:
- Cost per trip
- Cost per night
- Cost per year
- True cost per point

### Ownership Rules
Explicit modeling of:
- Annual point allocation
- Fee structure
- Point expiration
- Saving/borrowing policies
- Booking windows

## Tips

1. **Maximize Value**: Use all annual points to minimize cost per point
2. **Book Smart**: Low/regular seasons require fewer points
3. **Use Expiring Points**: System automatically uses points closest to expiration
4. **Track Everything**: Record all costs for accurate analysis
5. **Plan Ahead**: System enforces booking window rules

## Example Workflow

```python
# 1. Set up system
concierge = create_concierge()

# 2. Add resorts and points
concierge.add_resort(resort)
concierge.add_point_balance(balance)

# 3. Create bookings
booking = concierge.create_booking(...)

# 4. Create trip
trip = concierge.create_trip(...)

# 5. Record costs
concierge.accountant.record_cost(airfare)
concierge.accountant.record_cost(meals)

# 6. Analyze
analysis = concierge.accountant.analyze_costs(2026)
```

See `example.py` for a complete working example.
