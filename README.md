# VI Resorts Concierge

A data-model-first system for managing Vacation Internationale (VI) ownership with an embedded Accountant.

## Overview

The VI Resorts Concierge helps manage your VI timeshare ownership by:

- **Explaining Rules**: Clear explanations of VI ownership rules and policies
- **Browsing Resorts**: Search and explore available VI resorts
- **Planning Trips**: Create and manage vacation trips
- **Optimizing Points**: Smart point allocation to minimize waste and maximize value
- **Tracking Costs**: Comprehensive accounting with audit-friendly ledger

The embedded **Accountant** sub-agent tracks all vacation costs (fees, points, travel, incidentals) and computes:
- True cost per trip
- Cost per night  
- Cost per year
- True cost per point

## Installation

```bash
# Clone the repository
git clone https://github.com/nneibaue/vi-resorts.git
cd vi-resorts

# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

### CLI Usage

```bash
# Show VI ownership rules
vi-concierge rules

# List available resorts
vi-concierge resorts

# Show resort details
vi-concierge resort-details "Cabo Azul"

# Check point balance
vi-concierge points

# Create a booking
vi-concierge book "Cabo Azul" 2026-06-01 2026-06-08 --unit studio --season regular

# View cost analysis
vi-concierge costs

# Show accounting ledger
vi-concierge ledger
```

### Python API

```python
from decimal import Decimal
from datetime import date
from vi_resorts import (
    Concierge,
    OwnershipRules,
    PointBalance,
    PointType,
    Resort,
    Season,
    UnitType,
)

# Define your ownership rules
rules = OwnershipRules(
    annual_points=7000,
    annual_fee=Decimal("1200.00"),
    booking_fee=Decimal("99.00"),
    guest_certificate_fee=Decimal("79.00"),
)

# Create the concierge
concierge = Concierge(rules)

# Add a resort
resort = Resort(
    name="Cabo Azul Resort",
    location="San José del Cabo",
    country="Mexico",
    point_costs={
        "studio": {"regular": 1500, "peak": 2500},
        "one_bedroom": {"regular": 2200, "peak": 3500},
    }
)
concierge.add_resort(resort)

# Add your point balance
balance = PointBalance(
    year=2026,
    point_type=PointType.ANNUAL,
    total_points=7000,
    expiration_date=date(2027, 12, 31),
)
concierge.add_point_balance(balance)

# Create a booking
booking = concierge.create_booking(
    resort.id,
    check_in=date(2026, 6, 1),
    check_out=date(2026, 6, 8),
    unit_type=UnitType.STUDIO,
    season=Season.REGULAR,
)

# Analyze costs
analysis = concierge.accountant.analyze_costs(2026)
print(f"Total cost: ${analysis.total_cost}")
print(f"Cost per point: ${analysis.cost_per_point}")
```

## Architecture

### Data Models

The system uses Pydantic models for validation and type safety:

- **Resort**: Resort properties and point costs
- **PointBalance**: Point allocation and tracking
- **Booking**: Resort bookings with point usage
- **Trip**: Multi-booking vacation trips
- **Cost**: Individual cost entries
- **LedgerEntry**: Audit trail entries
- **OwnershipRules**: VI ownership rules and assumptions

### Concierge

The main system that:
- Manages resorts and point balances
- Creates bookings and trips
- Optimizes point allocation
- Provides rule explanations

### Accountant

The embedded accounting sub-agent that:
- Records all costs in an audit-friendly ledger
- Tracks bookings and point usage
- Computes true costs (per trip, night, year, point)
- Generates financial reports

### Point Optimizer

Smart point allocation that:
- Uses expiring points first
- Optimizes across multiple point balances
- Minimizes point waste

## Design Principles

1. **Data-Model-First**: Pydantic models define structure and validation
2. **Explicit Assumptions**: All rules and costs are explicitly modeled
3. **Precise Math**: Decimal type for financial calculations
4. **Audit Trail**: Complete ledger of all transactions
5. **CLI-First**: Rich terminal interface for primary interaction

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=vi_resorts --cov-report=html

# Type checking
mypy src/vi_resorts

# Linting
ruff check src/vi_resorts
```

## Testing

Comprehensive test coverage for:
- Data model validation
- Point balance operations
- Booking calculations
- Cost tracking and analysis
- Point optimization
- Concierge operations

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_accountant.py

# Run with verbose output
pytest -v
```

## License

MIT License

## Contributing

Contributions welcome! Please ensure:
- All tests pass
- New features include tests
- Code follows existing style
- Type hints are included
