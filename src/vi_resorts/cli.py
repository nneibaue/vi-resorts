"""
CLI interface for VI Resorts Concierge.

Provides a command-line interface for managing VI ownership.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

import click
from rich.console import Console
from rich.table import Table

from .accountant import Accountant
from .concierge import Concierge
from .models import (
    Cost,
    CostCategory,
    OwnershipRules,
    PointBalance,
    PointType,
    Resort,
    Season,
    UnitType,
)

console = Console()


def create_default_concierge() -> Concierge:
    """Create a Concierge with default rules and sample data."""
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
    
    concierge = Concierge(rules)
    
    # Add sample resorts
    sample_resorts = [
        Resort(
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
        ),
        Resort(
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
        ),
        Resort(
            name="Lake Tahoe Resort",
            location="South Lake Tahoe, California",
            country="USA",
            description="Mountain resort near skiing and lake activities",
            amenities=["Ski Access", "Pool", "Hot Tub", "Game Room", "BBQ Area"],
            point_costs={
                "studio": {"peak": 2200, "high": 1700, "regular": 1300, "low": 1000},
                "one_bedroom": {"peak": 3000, "high": 2400, "regular": 1900, "low": 1500},
                "two_bedroom": {"peak": 4200, "high": 3400, "regular": 2700, "low": 2200},
            }
        ),
    ]
    
    for resort in sample_resorts:
        concierge.add_resort(resort)
    
    # Add current year points
    current_year = date.today().year
    annual_points = PointBalance(
        year=current_year,
        point_type=PointType.ANNUAL,
        total_points=rules.annual_points,
        expiration_date=date(current_year + 1, 12, 31),
    )
    concierge.add_point_balance(annual_points)
    
    return concierge


# Global concierge instance
_concierge: Optional[Concierge] = None


def get_concierge() -> Concierge:
    """Get or create the global concierge instance."""
    global _concierge
    if _concierge is None:
        _concierge = create_default_concierge()
    return _concierge


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """VI Resorts Concierge - Manage your Vacation Internationale ownership."""
    pass


@cli.command()
def rules() -> None:
    """Explain VI ownership rules and policies."""
    concierge = get_concierge()
    
    console.print("\n[bold cyan]VI Ownership Rules[/bold cyan]\n")
    
    rules_dict = concierge.explain_rules()
    for key, value in rules_dict.items():
        console.print(f"[yellow]{key}:[/yellow] {value}")
    
    console.print("\n[bold cyan]Point Value Estimate[/bold cyan]\n")
    
    value_dict = concierge.get_point_value_estimate()
    for key, value in value_dict.items():
        console.print(f"[yellow]{key}:[/yellow] {value}")
    
    console.print()


@cli.command()
@click.option('--country', help='Filter by country')
@click.option('--location', help='Filter by location')
def resorts(country: Optional[str], location: Optional[str]) -> None:
    """Browse available resorts."""
    concierge = get_concierge()
    resort_list = concierge.list_resorts(country=country, location=location)
    
    if not resort_list:
        console.print("[yellow]No resorts found matching criteria[/yellow]")
        return
    
    table = Table(title="VI Resorts")
    table.add_column("Resort", style="cyan")
    table.add_column("Location", style="magenta")
    table.add_column("Country", style="green")
    table.add_column("Amenities", style="blue")
    
    for resort in resort_list:
        amenities = ", ".join(resort.amenities[:3])
        if len(resort.amenities) > 3:
            amenities += f" (+{len(resort.amenities) - 3} more)"
        
        table.add_row(
            resort.name,
            resort.location,
            resort.country,
            amenities,
        )
    
    console.print(table)


@cli.command()
@click.argument('resort_name')
def resort_details(resort_name: str) -> None:
    """Show detailed information about a resort."""
    concierge = get_concierge()
    
    # Find resort by name (case-insensitive partial match)
    resort = None
    for r in concierge.resorts.values():
        if resort_name.lower() in r.name.lower():
            resort = r
            break
    
    if not resort:
        console.print(f"[red]Resort not found: {resort_name}[/red]")
        return
    
    console.print(f"\n[bold cyan]{resort.name}[/bold cyan]")
    console.print(f"[yellow]Location:[/yellow] {resort.location}, {resort.country}")
    
    if resort.description:
        console.print(f"\n{resort.description}")
    
    if resort.amenities:
        console.print(f"\n[yellow]Amenities:[/yellow]")
        for amenity in resort.amenities:
            console.print(f"  • {amenity}")
    
    # Show point costs
    console.print(f"\n[bold yellow]Point Costs (per night)[/bold yellow]")
    
    table = Table()
    table.add_column("Unit Type", style="cyan")
    table.add_column("Peak", style="red")
    table.add_column("High", style="yellow")
    table.add_column("Regular", style="green")
    table.add_column("Low", style="blue")
    
    unit_labels = {
        "studio": "Studio",
        "one_bedroom": "1 Bedroom",
        "two_bedroom": "2 Bedroom",
        "three_bedroom": "3 Bedroom",
    }
    
    for unit_type, costs in resort.point_costs.items():
        table.add_row(
            unit_labels.get(unit_type, unit_type),
            str(costs.get("peak", "-")),
            str(costs.get("high", "-")),
            str(costs.get("regular", "-")),
            str(costs.get("low", "-")),
        )
    
    console.print(table)
    console.print()


@cli.command()
@click.option('--year', type=int, help='Filter by year')
def points(year: Optional[int]) -> None:
    """Show available points balance."""
    concierge = get_concierge()
    if year is None:
        year = date.today().year
    
    available = concierge.get_available_points(year=year)
    
    console.print(f"\n[bold cyan]Point Balance for {year}[/bold cyan]\n")
    
    table = Table()
    table.add_column("Type", style="cyan")
    table.add_column("Total", style="green")
    table.add_column("Used", style="yellow")
    table.add_column("Available", style="magenta")
    table.add_column("Expires", style="red")
    
    for balance in concierge.point_balances:
        if balance.year == year:
            expiry = balance.expiration_date.strftime("%Y-%m-%d") if balance.expiration_date else "Never"
            table.add_row(
                balance.point_type.value.title(),
                str(balance.total_points),
                str(balance.used_points),
                str(balance.available_points),
                expiry,
            )
    
    console.print(table)
    console.print(f"\n[bold]Total Available:[/bold] [green]{available}[/green] points\n")


@cli.command()
@click.argument('resort_name')
@click.argument('check_in', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument('check_out', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option('--unit', type=click.Choice(['studio', '1bed', '2bed', '3bed']), default='studio')
@click.option('--season', type=click.Choice(['peak', 'high', 'regular', 'low']), default='regular')
@click.option('--guest', help='Guest name for the booking')
def book(
    resort_name: str,
    check_in: datetime,
    check_out: datetime,
    unit: str,
    season: str,
    guest: Optional[str],
) -> None:
    """Create a new booking."""
    concierge = get_concierge()
    
    # Find resort
    resort = None
    for r in concierge.resorts.values():
        if resort_name.lower() in r.name.lower():
            resort = r
            break
    
    if not resort:
        console.print(f"[red]Resort not found: {resort_name}[/red]")
        return
    
    # Convert unit type
    unit_map = {
        'studio': UnitType.STUDIO,
        '1bed': UnitType.ONE_BEDROOM,
        '2bed': UnitType.TWO_BEDROOM,
        '3bed': UnitType.THREE_BEDROOM,
    }
    unit_type = unit_map[unit]
    
    # Convert season
    season_enum = Season(season)
    
    # Convert dates
    check_in_date = check_in.date()
    check_out_date = check_out.date()
    
    try:
        # Calculate points needed
        nights = (check_out_date - check_in_date).days
        points_needed = concierge.calculate_booking_points(
            resort, unit_type, season_enum, nights
        )
        
        # Show booking summary
        console.print(f"\n[bold cyan]Booking Summary[/bold cyan]")
        console.print(f"Resort: {resort.name}")
        console.print(f"Check-in: {check_in_date}")
        console.print(f"Check-out: {check_out_date}")
        console.print(f"Nights: {nights}")
        console.print(f"Unit: {unit_type.value}")
        console.print(f"Season: {season_enum.value}")
        console.print(f"Points needed: {points_needed}")
        console.print(f"Booking fee: ${concierge.rules.booking_fee}")
        
        if click.confirm("\nProceed with booking?"):
            booking = concierge.create_booking(
                resort.id,
                check_in_date,
                check_out_date,
                unit_type,
                season_enum,
                guest_name=guest,
            )
            console.print(f"\n[green]✓ Booking created successfully![/green]")
            console.print(f"Booking ID: {booking.id}")
            console.print(f"Confirmation: {booking.confirmation_number or 'Pending'}")
        else:
            console.print("\n[yellow]Booking cancelled[/yellow]")
    
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")


@cli.command()
@click.option('--year', type=int, help='Analyze specific year')
def costs(year: Optional[int]) -> None:
    """Show cost analysis and accounting reports."""
    concierge = get_concierge()
    
    if year is None:
        year = date.today().year
    
    analysis = concierge.accountant.analyze_costs(year=year)
    
    console.print(f"\n[bold cyan]Cost Analysis for {year}[/bold cyan]\n")
    
    console.print(f"[yellow]Total Cost:[/yellow] ${analysis.total_cost:.2f}")
    console.print(f"[yellow]Annual Cost:[/yellow] ${analysis.annual_cost:.2f}")
    console.print(f"[yellow]Cost Per Point:[/yellow] ${analysis.cost_per_point:.2f}")
    
    if analysis.trip_costs:
        console.print(f"\n[bold yellow]Trip Costs[/bold yellow]")
        for trip_id, cost in analysis.trip_costs.items():
            trip = concierge.accountant.trips.get(trip_id)
            trip_name = trip.name if trip else str(trip_id)
            console.print(f"  {trip_name}: ${cost:.2f}")
    
    if analysis.booking_costs:
        console.print(f"\n[bold yellow]Booking Costs[/bold yellow]")
        table = Table()
        table.add_column("Booking", style="cyan")
        table.add_column("Total Cost", style="green")
        table.add_column("Cost/Night", style="yellow")
        
        for booking_id, cost in analysis.booking_costs.items():
            booking = concierge.accountant.bookings.get(booking_id)
            cost_per_night = analysis.cost_per_night.get(booking_id, Decimal("0"))
            
            booking_desc = f"{booking_id}" if not booking else f"{booking.unit_type.value} ({booking.nights}n)"
            table.add_row(
                booking_desc,
                f"${cost:.2f}",
                f"${cost_per_night:.2f}",
            )
        
        console.print(table)
    
    console.print()


@cli.command()
def ledger() -> None:
    """Show the complete accounting ledger."""
    concierge = get_concierge()
    
    ledger_entries = concierge.accountant.get_ledger_report()
    
    if not ledger_entries:
        console.print("[yellow]No ledger entries found[/yellow]")
        return
    
    console.print("\n[bold cyan]Accounting Ledger[/bold cyan]\n")
    
    table = Table()
    table.add_column("Timestamp", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Description", style="white")
    
    for entry in ledger_entries:
        timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        table.add_row(
            timestamp,
            entry['entry_type'],
            entry['description'],
        )
    
    console.print(table)
    console.print()


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
